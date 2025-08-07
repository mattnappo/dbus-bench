import asyncio
import time
import json
import signal
from collections import deque
from datetime import datetime, timezone
import zoneinfo
import sys
if len(sys.argv) != 2:
    print("Usage: asyncbench.py <gvisor|runc>")
    sys.exit(1)

RUNTIME = sys.argv[1]
DURATION = 1000

d = "{:%Y%m%d_%H%M%S}".format(datetime.now())
OUTPUT_FILE = f"results_{d}.json"
BUS_OUTPUT_FILE = f"bus_{d}.json"


async def get_num_containers(runtime):
    if runtime.lower() == "gvisor":
        cmd = "ps aux | grep -v grep | grep runsc-sandbox | wc -l"
    elif runtime.lower() == "runc":
        cmd = "runc list | grep running | wc -l"
    else:
        assert False

    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    stdout, _ = await proc.communicate()
    return int(stdout.decode().strip())


async def get_busctl_latency():
    t0 = time.monotonic()
    proc = await asyncio.create_subprocess_shell(
        "busctl get-property org.freedesktop.systemd1 /org/freedesktop/systemd1 org.freedesktop.systemd1.Manager Version",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.communicate()
    return time.monotonic() - t0


async def container_updater(shared, runtime, interval=1.0):
    while not shared["stop"]:
        try:
            shared["num_containers"] = await get_num_containers(runtime)
        except Exception:
            shared["num_containers"] = 0
        await asyncio.sleep(interval)


async def latency_updater(shared, interval=1.0):
    while not shared["stop"]:
        try:
            shared["busctl_latency"] = await get_busctl_latency()
        except Exception:
            shared["busctl_latency"] = -1
        await asyncio.sleep(interval)


def handle_line(line):
    ts = line["timestamp-realtime"]
    ts_sec = ts / 1_000_000
    dt_utc = datetime.fromtimestamp(ts_sec, tz=timezone.utc)
    edt = zoneinfo.ZoneInfo("America/New_York")
    dt_edt = dt_utc.astimezone(edt)
    t = dt_edt.timestamp()
    obj = {
        "timestamp": t,
        "type": line.get("type"),
        "sender": line.get("sender"),
        "destination": line.get("destination"),
        "path": line.get("path"),
        "interface": line.get("interface"),
        "member": line.get("member"),
        "_payload": line.get("payload"),
    }
    return obj


async def monitor_dbus(duration=DURATION):
    proc = await asyncio.create_subprocess_exec(
        "busctl",
        "monitor",
        "--system",
        "--json=short",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )

    window = deque(maxlen=10)
    data_log = []
    bus_log = []
    shared = {"num_containers": 0, "busctl_latency": -1, "stop": False}
    container_task = asyncio.create_task(container_updater(shared, RUNTIME))
    latency_task = asyncio.create_task(latency_updater(shared))

    current_count = 0
    last_sample_time = time.time()
    start_time = last_sample_time

    try:
        while True:
            now = time.time()
            if now - start_time >= duration:
                break
            if proc.stdout.at_eof():
                break

            try:
                line = await asyncio.wait_for(proc.stdout.readline(), timeout=0.1)
                line = json.loads(line.decode().strip())
                line = handle_line(line)
                bus_log.append(line)
                current_count += 1
            except asyncio.TimeoutError:
                pass

            if now - last_sample_time >= 0.1:
                window.append(current_count)
                avg = sum(window) / len(window)
                obj = {
                    "timestamp": now,
                    "avg_msgs_per_sec": avg * 10,
                    "num_containers": shared["num_containers"],
                    "busctl_latency": shared["busctl_latency"],
                }
                data_log.append(obj)
                current_count = 0
                last_sample_time = now

    except asyncio.CancelledError:
        print(">>> monitor_dbus: CancelledError caught. Exiting early.")
        # Don't re-raise, we want to return the collected data

    finally:
        shared["stop"] = True
        container_task.cancel()
        latency_task.cancel()
        try:
            await container_task
        except asyncio.CancelledError:
            pass
        try:
            await latency_task
        except asyncio.CancelledError:
            pass
        proc.terminate()

    return (data_log, bus_log)


async def main():
    data = []
    bus = []
    shutdown_event = asyncio.Event()

    def signal_handler():
        print("\n>>> Ctrl+C received. Shutting down gracefully...")
        shutdown_event.set()

    # Set up signal handler for graceful shutdown
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, signal_handler)
    loop.add_signal_handler(signal.SIGTERM, signal_handler)

    try:
        # Create the monitoring task
        monitor_task = asyncio.create_task(monitor_dbus())

        # Wait for either the task to complete or shutdown signal
        _done, pending = await asyncio.wait(
            [monitor_task, asyncio.create_task(shutdown_event.wait())],
            return_when=asyncio.FIRST_COMPLETED,
        )

        if shutdown_event.is_set():
            # Shutdown was requested, cancel the monitor task
            monitor_task.cancel()
            try:
                data, bus = await monitor_task
            except asyncio.CancelledError:
                # This shouldn't happen since monitor_dbus doesn't re-raise CancelledError
                data = None
                bus = None
        else:
            # Normal completion
            data, bus = monitor_task.result()

        # Cancel any remaining pending tasks
        for task in pending:
            task.cancel()

    except Exception as e:
        print(f">>> Unexpected error: {e}")
    finally:
        print(f"Saving {len(data)} records to {OUTPUT_FILE}")
        with open(OUTPUT_FILE, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Saving {len(bus)} records to {BUS_OUTPUT_FILE}")
        with open(BUS_OUTPUT_FILE, "w") as f:
            json.dump(bus, f, indent=2)
        print("Done.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # This should not happen now since we handle SIGINT in the event loop
        print("\n>>> Fallback Ctrl+C handler. Data may not be saved.")

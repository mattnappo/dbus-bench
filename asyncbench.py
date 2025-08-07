import asyncio
import time
from collections import deque

RUNTIME = "gvisor"


async def get_num_containers(runtime):
    """Async call to count how many runc containers are running."""
    if runtime.lower == "gvisor":
        cmd = "ps aux | grep -v grep | grep runsc-sandbox | wc -l"
    elif runtime.lower() == "runc":
        cmd = "runsc list | grep running | wc -l"
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
    proc = await asyncio.create_subprocess_shell(
        "busctl get-property org.freedesktop.systemd1 /org/freedesktop/systemd1 org.freedesktop.systemd1.Manager Version",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    stdout, _ = await proc.communicate()
    return int(stdout.decode().strip())


async def container_updater(shared, runtime, interval=1.0):
    """Async task that updates container count every `interval` seconds."""
    while not shared["stop"]:
        try:
            shared["num_containers"] = await get_num_containers(runtime)
        except Exception:
            shared["num_containers"] = -1
        await asyncio.sleep(interval)


async def latency_updater(shared, interval=1.0):
    """Async task that updates container count every `interval` seconds."""
    while not shared["stop"]:
        try:
            shared["busctl_latency"] = await get_busctl_latency()
        except Exception:
            shared["busctl_latency"] = -1
        await asyncio.sleep(interval)


async def monitor_dbus(duration=1000):  # ~16 min
    proc = await asyncio.create_subprocess_exec(
        "busctl",
        "monitor",
        "--system",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )

    window = deque(maxlen=10)
    data_log = []

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
                line = line.decode().strip()
                if "Type=" in line:
                    current_count += 1
            except asyncio.TimeoutError:
                pass

            if now - last_sample_time >= 0.1:
                window.append(current_count)
                avg = sum(window) / len(window)
                data_log.append(
                    {
                        "timestamp": now,
                        "avg_msgs_per_sec": avg * 10,
                        "num_containers": shared["num_containers"],
                        "busctl_latency": shared["busctl_latency"],
                    }
                )
                current_count = 0
                last_sample_time = now

    except KeyboardInterrupt:
        print("\nInterrupted by user. Finalizing...")

    finally:
        shared["stop"] = True
        await container_task
        await latency_task
        proc.terminate()
        return data_log


if __name__ == "__main__":
    asyncio.run(monitor_dbus())

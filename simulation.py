import subprocess
import time
import concurrent.futures
from datetime import datetime
import json
from threading import Lock

lock = Lock()


def create_load(duration_list):
    start = time.time()
    cmd = "busctl get-property org.freedesktop.systemd1 /org/freedesktop/systemd1 org.freedesktop.systemd1.Manager Version"
    subprocess.run(cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    end = time.time()

    duration_ms = (end - start) * 1000.0
    with lock:
        duration_list.append(duration_ms)


def run_load_for_rate(rate_per_sec, duration_sec):
    print(f"Starting load: {rate_per_sec} msgs/sec for {duration_sec} seconds")
    interval = 1.0 / rate_per_sec
    end_time = time.time() + duration_sec
    phase_start = datetime.now()

    # Stats
    durations = []
    counts_per_second = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=rate_per_sec) as executor:
        second_start = time.time()
        count_this_second = 0

        while time.time() < end_time:
            now = time.time()
            if now - second_start >= 1.0:
                counts_per_second.append(count_this_second)
                count_this_second = 0
                second_start = now

            executor.submit(create_load, durations)
            count_this_second += 1

            elapsed = time.time() - now
            sleep_time = max(0, interval - elapsed)
            time.sleep(sleep_time)

        # Capture last second's count
        counts_per_second.append(count_this_second)

    phase_end = datetime.now()
    print(f"Finished load: {rate_per_sec} msgs/sec")

    return {
        "rate_per_sec": rate_per_sec,
        "duration_sec": duration_sec,
        "start_time": phase_start.isoformat(),
        "end_time": phase_end.isoformat(),
        "calls_per_second": counts_per_second,
        "call_durations_ms": durations,
    }


def main():
    schedule = [100, 200, 400, 800, 1600, 2000]
    duration_per_level = 8

    simulation_start = datetime.now()
    print(f"Simulation started at: {simulation_start.strftime('%Y-%m-%d %H:%M:%S')}")

    result_data = {
        "simulation_start": simulation_start.isoformat(),
        "phases": [],
    }

    for rate in schedule:
        phase_data = run_load_for_rate(rate, duration_per_level)
        result_data["phases"].append(phase_data)

    simulation_end = datetime.now()
    result_data["simulation_end"] = simulation_end.isoformat()
    result_data["total_duration_seconds"] = (
        simulation_end - simulation_start
    ).total_seconds()

    print(f"Simulation ended at: {simulation_end.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total duration: {simulation_end - simulation_start}")

    # Save results to JSON
    timestamp_str = simulation_end.strftime("%Y%m%d_%H%M%S")
    filename = f"dbus_load_{timestamp_str}.json"
    with open(filename, "w") as f:
        json.dump(result_data, f, indent=2)

    print(f"Results written to {filename}")


if __name__ == "__main__":
    main()

import subprocess
import time
from collections import deque
import datetime
import json
import matplotlib.pyplot as plt


def num_containers():
    """Count how many runsc-sandbox processes are running."""
    # cmd = "ps aux | grep runsc-sandbox | grep -v grep | wc -l"
    cmd = "ps aux | grep 'runc ' | grep -v grep | wc -l"
    result = subprocess.check_output(cmd, shell=True).decode().strip()
    return int(result)


def monitor_dbus(duration=1000):  # 16 min
    # Start busctl monitor --system
    proc = subprocess.Popen(
        ["busctl", "monitor", "--system"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )

    window = deque(maxlen=10)
    data_log = []

    current_count = 0
    last_sample_time = time.time()
    start_time = last_sample_time

    try:
        while True:
            now = time.time()

            if now - start_time >= duration:
                break

            if proc.stdout is not None:
                ready = proc.stdout.readline()
                if not ready:
                    continue

                line = ready.strip()
                if "Type=" in line:
                    current_count += 1

            if now - last_sample_time >= 0.1:
                window.append(current_count)
                avg = sum(window) / len(window)
                data_log.append(
                    {
                        "timestamp": now,
                        "avg_msgs_per_sec": avg * 10,  # scale to 1s
                        "num_containers": num_containers(),
                    }
                )
                current_count = 0
                last_sample_time = now

    except KeyboardInterrupt:
        print("\nInterrupted by user. Finalizing...")

    finally:
        proc.terminate()
        return data_log


def save_results_and_plot(results):
    # Extract data
    times = [datetime.datetime.fromtimestamp(entry["timestamp"]) for entry in results]
    avgs = [entry["avg_msgs_per_sec"] for entry in results]
    containers = [entry["num_containers"] for entry in results]

    # Create dual-axis plot
    fig, ax1 = plt.subplots()
    fig.set_size_inches(19.20, 10.80)

    ax1.set_xlabel("Time")
    ax1.set_ylabel("Messages/sec", color="tab:blue")
    ax1.plot(times, avgs, label="D-Bus Msg/sec", color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    ax2 = ax1.twinx()
    ax2.set_ylabel("runsc-sandbox Processes", color="tab:red")
    ax2.plot(times, containers, label="runsc-sandbox count", color="tab:red")
    ax2.tick_params(axis="y", labelcolor="tab:red")

    plt.title("D-Bus Message Rate vs. runsc-sandbox Process Count")
    fig.autofmt_xdate()
    plt.grid(True)
    fig.tight_layout()

    # Timestamp for filenames
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save plot
    plot_filename = f"dbus_dual_plot_{timestamp_str}.png"
    plt.savefig(plot_filename, dpi=100)
    print(f"Plot saved to {plot_filename}")

    # Save data as JSON
    json_filename = f"dbus_data_{timestamp_str}.json"
    with open(json_filename, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Data saved to {json_filename}")


def from_file(filename):
    with open(filename) as f:
        results = json.loads(f.read())
        save_results_and_plot(results)


if __name__ == "__main__":
    # results = monitor_dbus()
    # save_results_and_plot(results)

    import sys

    from_file(sys.argv[1])

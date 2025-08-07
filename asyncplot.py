import matplotlib.pyplot as plt
from datetime import datetime
import json
import sys

d = "{:%Y%m%d_%H%M%S}".format(datetime.now())
OUTFILE = f"plot_latency_{d}.png"


def plot(data):
    # Parse data
    times = [datetime.fromtimestamp(d["timestamp"]) for d in data]
    msgs = [d["avg_msgs_per_sec"] for d in data]
    containers = [d["num_containers"] for d in data]
    latency = [d["busctl_latency"] for d in data]

    # Base figure and first axis
    fig, ax1 = plt.subplots(figsize=(19.20, 10.80))

    ax1.set_xlabel("Time")
    ax1.set_ylabel("Messages/sec", color="blue")
    ax1.plot(times, msgs, label="Messages/sec", color="blue")
    ax1.tick_params(axis="y", labelcolor="blue")

    # Second axis (containers)
    ax2 = ax1.twinx()
    ax2.set_ylabel("Num Containers", color="green")
    ax2.plot(times, containers, label="Containers", color="green")
    ax2.tick_params(axis="y", labelcolor="green")

    # Third axis (latency) - offset to avoid overlap
    ax3 = ax1.twinx()
    ax3.spines["right"].set_position(("outward", 60))  # Offset third y-axis
    ax3.set_ylabel("Busctl Latency", color="red")
    ax3.plot(times, latency, label="Busctl Latency", color="red")
    ax3.tick_params(axis="y", labelcolor="red")

    fig.tight_layout()
    fig.autofmt_xdate()
    plt.title("D-Bus Load, Container Count, and Busctl Latency")
    # plt.show()
    plt.savefig(OUTFILE, dpi=150, bbox_inches="tight")


if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        plot(json.loads(f.read()))

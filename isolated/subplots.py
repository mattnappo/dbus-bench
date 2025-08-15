import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re
import math
from dataset import groups

n_groups = len(groups)
n_cols = 2
n_rows = math.ceil(n_groups / n_cols)

fig, axs = plt.subplots(n_rows, n_cols, figsize=(16, 8), dpi=300, sharey=True)
axs = axs.flatten()

#for ax, (label, file_list) in zip(axs, groups.items()):
for ax, (label, file_list) in zip(axs, groups):
    print(ax)
    dfs = []
    for filename in file_list:
        df = pd.read_json(filename)
        df["last_ms"] = df["latency"] * 1000
        dfs.append(df)
    combined = pd.concat(dfs, ignore_index=True)
    
    sorted_vals = np.sort(combined["last_ms"])
    y_vals = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
    
    ax.plot(sorted_vals, y_vals, linestyle="-", color="C0")
    
    # Percentile annotations
    for perc in [0, 50, 90, 95]:
        t = np.percentile(sorted_vals, perc)
        # Find the closest y-value in the ECDF for this x
        y_pos = y_vals[np.searchsorted(sorted_vals, t)]
        ax.axvline(t, alpha=0.15, color="C0", linestyle="--")
        # Place text slightly above the curve
        ax.text(t, y_pos + 0.02, f"p{perc}: {t:.2f} ms",
                rotation=0, va="bottom", ha="center", fontsize=6, color="C0") 

    ax.set_title(label)
    ax.set_xlabel("lag (ms)")
    ax.set_ylabel("Cumulative probability")
    ax.grid(True, linestyle="--", alpha=0.6)

# Hide unused subplots
for ax in axs[n_groups:]:
    ax.set_visible(False)

fig.suptitle("DBus Lag ECDF Comparison by Group", fontsize=16)
fig.tight_layout(rect=[0, 0, 1, 0.96])

safe_filename = re.sub(r"[^\w\-]", "_", "dbus_lag_ecdf_subplots") + ".png"
fig.savefig(safe_filename)
print(f"Saved plot as {safe_filename}")

plt.show()


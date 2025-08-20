import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re

from dataset import groups

plt.figure(figsize=(19.2, 10.8), dpi=200)

for label, file_list in groups:
    dfs = []
    for filename in file_list:
        df = pd.read_json(filename)
        df["latency"] = df["latency"] * 1000
        dfs.append(df)
    combined = pd.concat(dfs, ignore_index=True)
    
    # Sort values for ECDF
    sorted_vals = np.sort(combined["latency"])
    y_vals = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
    
    # Plot ECDF line
    plt.plot(sorted_vals, y_vals, linestyle="-", label=label)

    '''
    # Percentile annotations
    for perc in [0, 50, 90, 95]:
        t = np.percentile(sorted_vals, perc)
        # Find the closest y-value in the ECDF for this x
        y_pos = y_vals[np.searchsorted(sorted_vals, t)]
        plt.axvline(t, alpha=0.15, color="C0", linestyle="--")
        # Place text slightly above the curve
        plt.text(t, y_pos + 0.02, f"p{perc}: {t:.2f} ms",
                rotation=0, va="bottom", ha="center", fontsize=6, color="C0") 
    '''

plt.xlabel("lag (ms)")
plt.ylabel("Cumulative probability")
plt.title("DBus Lag ECDF Comparison (Averaged Groups)")
plt.grid(True, linestyle="--", alpha=0.6)
plt.legend()

# Save with nice filename
safe_filename = re.sub(r"[^\w\-]", "_", "dbus_lag_ecdf_comparison_grouped") + ".png"
plt.savefig(safe_filename)
print(f"Saved plot as {safe_filename}")

plt.show()


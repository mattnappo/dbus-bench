import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re

from dataset import groups

plt.figure(figsize=(19.2, 10.8), dpi=100)

for label, file_list in groups.items():
    dfs = []
    for filename in file_list:
        df = pd.read_csv(filename, delim_whitespace=True)
        df["last_ms"] = df["last"] * 1000
        dfs.append(df)
    
    # Combine all runs for the group
    combined = pd.concat(dfs, ignore_index=True)
    
    # Sort values for ECDF
    sorted_vals = np.sort(combined["last_ms"])
    y_vals = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
    
    # Plot ECDF line
    plt.plot(sorted_vals, y_vals, linestyle="-", label=label)

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


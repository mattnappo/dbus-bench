import json
import pandas as pd
import numpy as np
from collections import Counter
import sys

from bokeh.io import curdoc
from bokeh.plotting import figure, ColumnDataSource
from bokeh.layouts import column
from bokeh.models import RangeTool

# Bokeh server version - no output_notebook() needed 

# Handle arguments for both command line and Bokeh server
if len(sys.argv) >= 3:
    DATA_FILE = sys.argv[1]
    BUS_FILE = sys.argv[2]
else:
    print("Usage: smartplot.py <RESULTS FILE> <BUS FILE>")
    print("Or run with: bokeh serve smartplot.py --args results_file.json bus_file.json")
    sys.exit(1)

# --- Load your data ---
# First dataset: time series
with open(DATA_FILE) as f:
    ts_data = json.load(f)

df_ts = pd.DataFrame(ts_data)
df_ts["datetime"] = pd.to_datetime(df_ts["timestamp"], unit="s")

# Second dataset: events
with open(BUS_FILE) as f:  # replace with your actual filename
    msg_data = json.load(f)

df_msg = pd.DataFrame(msg_data)
df_msg["datetime"] = pd.to_datetime(df_msg["timestamp"], unit="s")

# --- Prepare ColumnDataSource ---
source_ts = ColumnDataSource(df_ts)

# --- Time series plots ---
# Main plot: Messages per Second
p1 = figure(width=800, height=250, x_axis_type="datetime",
            title="Messages per Second (avg_msgs_per_sec)")
p1.line("datetime", "avg_msgs_per_sec", source=source_ts, line_color="blue")
p1.yaxis.axis_label = "avg_msgs_per_sec"

# Second plot: Number of Containers
p2 = figure(width=800, height=250, x_axis_type="datetime",
            title="Number of Containers", x_range=p1.x_range)
p2.line("datetime", "num_containers", source=source_ts, line_color="green")
p2.yaxis.axis_label = "num_containers"

# Third plot: Busctl Latency
p3 = figure(width=800, height=250, x_axis_type="datetime",
            title="Busctl Latency (seconds)", x_range=p1.x_range)
p3.line("datetime", "busctl_latency", source=source_ts, line_color="red")
p3.yaxis.axis_label = "busctl_latency (sec)"

# --- Range selector ---
select = figure(width=800, height=130, x_axis_type="datetime",
                y_range=p1.y_range, y_axis_type=None, tools="", toolbar_location=None)
select.line("datetime", "avg_msgs_per_sec", source=source_ts)
range_tool = RangeTool(x_range=p1.x_range)
range_tool.overlay.fill_color = "navy"
range_tool.overlay.fill_alpha = 0.2
select.add_tools(range_tool)

# --- Histogram plot ---
hist_src = ColumnDataSource(data=dict(members=[], counts=[]))
hist_fig = figure(width=800, height=300, x_range=[], title="Histogram of 'member' Field")
hist_fig.vbar(x='members', top='counts', width=0.9, source=hist_src)

# --- Update histogram when x_range changes ---
def update_histogram(attr, old, new):
    start = pd.to_datetime(p1.x_range.start, unit="ms")
    end = pd.to_datetime(p1.x_range.end, unit="ms")

    mask = (df_msg["datetime"] >= start) & (df_msg["datetime"] <= end)
    members = df_msg.loc[mask, "member"].dropna()

    counts = Counter(members)
    members_list = list(counts.keys())
    counts_list = list(counts.values())

    hist_src.data = dict(members=members_list, counts=counts_list)
    hist_fig.x_range.factors = members_list  # Update categorical x-axis

update_histogram(None, None, None)

p1.x_range.on_change('start', update_histogram)
p1.x_range.on_change('end', update_histogram)

# --- Display ---
curdoc().add_root(column(p1, p2, p3, select, hist_fig))
curdoc().title = "Smart Plot Dashboard"
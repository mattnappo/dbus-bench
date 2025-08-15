import json
import pandas as pd
import numpy as np
from collections import Counter
import sys

from bokeh.io import curdoc
from bokeh.plotting import figure, ColumnDataSource
from bokeh.layouts import column, row
from bokeh.models import RangeTool, PreText
import time

TRUNCATE=100_000
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
hist_fig.xaxis.major_label_orientation = "vertical"

# --- Text boxes for bus JSON data ---
text_box_1st = PreText(text="", width=800, height=400)
text_box_1st.text = "Most Common Member JSON (for current time range)\n\nSelect a time range to see bus messages JSON data..."

text_box_2nd = PreText(text="", width=800, height=400)
text_box_2nd.text = "Second Most Common Member JSON (for current time range)\n\nSelect a time range to see bus messages JSON data..."

# --- Throttling variables ---
last_update_time = 0
update_pending = False

# --- Update histogram and text box when x_range changes ---
def update_histogram_throttled():
    """Actual update function that does the work"""
    start = pd.to_datetime(p1.x_range.start, unit="ms")
    end = pd.to_datetime(p1.x_range.end, unit="ms")

    mask = (df_msg["datetime"] >= start) & (df_msg["datetime"] <= end)
    members = df_msg.loc[mask, "member"].dropna()

    counts = Counter(members)
    members_list = list(counts.keys())
    counts_list = list(counts.values())

    hist_src.data = dict(members=members_list, counts=counts_list)
    hist_fig.x_range.factors = members_list  # Update categorical x-axis
    
    # Update text boxes with filtered bus messages JSON for most and second most common members
    if len(counts) > 0:
        # Sort members by count to get most and second most common
        sorted_members = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        
        # Handle most common member (1st)
        most_common_member, most_count = sorted_members[0]
        member_mask_1st = (df_msg["datetime"] >= start) & (df_msg["datetime"] <= end) & (df_msg["member"] == most_common_member)
        filtered_messages_1st = df_msg.loc[member_mask_1st].to_dict('records')
        
        if len(filtered_messages_1st) > 0:
            # Sort messages by string size (largest first)
            filtered_messages_1st_sorted = sorted(filtered_messages_1st, 
                                                  key=lambda msg: len(json.dumps(msg, default=str)), 
                                                  reverse=True)
            json_text_1st = json.dumps(filtered_messages_1st_sorted, indent=2, default=str)
            if len(json_text_1st) > TRUNCATE:  # Smaller limit since we have two columns
                json_text_1st = json_text_1st[:TRUNCATE] + "\n... [truncated - too many messages to display]"
            text_box_1st.text = f"Most Common Member JSON (for current time range)\n\nMember: '{most_common_member}' ({most_count} occurrences)\nShowing {len(filtered_messages_1st)} messages (sorted by size, largest first):\n\n{json_text_1st}"
        else:
            text_box_1st.text = f"Most Common Member JSON (for current time range)\n\nMember: '{most_common_member}' but no messages found."
        
        # Handle second most common member (2nd)
        if len(sorted_members) > 1:
            second_common_member, second_count = sorted_members[1]
            member_mask_2nd = (df_msg["datetime"] >= start) & (df_msg["datetime"] <= end) & (df_msg["member"] == second_common_member)
            filtered_messages_2nd = df_msg.loc[member_mask_2nd].to_dict('records')
            
            if len(filtered_messages_2nd) > 0:
                # Sort messages by string size (largest first)
                filtered_messages_2nd_sorted = sorted(filtered_messages_2nd, 
                                                      key=lambda msg: len(json.dumps(msg, default=str)), 
                                                      reverse=True)
                json_text_2nd = json.dumps(filtered_messages_2nd_sorted, indent=2, default=str)
                if len(json_text_2nd) > TRUNCATE:  # Smaller limit since we have two columns
                    json_text_2nd = json_text_2nd[:TRUNCATE] + "\n... [truncated - too many messages to display]"
                text_box_2nd.text = f"Second Most Common Member JSON (for current time range)\n\nMember: '{second_common_member}' ({second_count} occurrences)\nShowing {len(filtered_messages_2nd)} messages (sorted by size, largest first):\n\n{json_text_2nd}"
            else:
                text_box_2nd.text = f"Second Most Common Member JSON (for current time range)\n\nMember: '{second_common_member}' but no messages found."
        else:
            text_box_2nd.text = "Second Most Common Member JSON (for current time range)\n\nOnly one unique member found in the selected time range."
    else:
        text_box_1st.text = "Most Common Member JSON (for current time range)\n\nNo bus messages found in the selected time range."
        text_box_2nd.text = "Second Most Common Member JSON (for current time range)\n\nNo bus messages found in the selected time range."


def update_histogram(attr, old, new):
    """Throttled update handler"""
    global last_update_time, update_pending
    current_time = time.time()
    
    # If enough time has passed since last update, update immediately
    if current_time - last_update_time >= 5.0:
        update_histogram_throttled()
        last_update_time = current_time
        update_pending = False
    else:
        # Mark that an update is pending
        update_pending = True


def periodic_update():
    """Called periodically to handle pending updates"""
    global last_update_time, update_pending
    current_time = time.time()
    
    if update_pending and (current_time - last_update_time >= 5.0):
        update_histogram_throttled()
        last_update_time = current_time
        update_pending = False


# Initial update
update_histogram_throttled()

# Set up range change listeners
p1.x_range.on_change('start', update_histogram)
p1.x_range.on_change('end', update_histogram)

# Set up periodic callback to handle pending updates (check every second)
curdoc().add_periodic_callback(periodic_update, 1000)

# --- Display ---
left_column = column(p1, p2, p3, select, hist_fig)
middle_column = column(text_box_1st)
right_column = column(text_box_2nd)
layout = row(left_column, middle_column, right_column)
curdoc().add_root(layout)
curdoc().title = DATA_FILE

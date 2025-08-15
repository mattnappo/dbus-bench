#!/bin/bash

set -u

results="$1"
bus="$2"
port="$3"

bokeh serve ~/benchmarking/smartplot.py --port $port --args $results $bus $port --show

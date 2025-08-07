#!/bin/bash

results="$1"
bus="$2"

bokeh serve ~/benchmarking/smartplot.py --args $results $bus --show

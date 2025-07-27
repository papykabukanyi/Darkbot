#!/bin/sh
# Simple health check for the Darkbot container

# Check if the Python process is running
if ps aux | grep -q "[p]ython main.py"; then
    # Process is running
    echo "Darkbot is running"
    exit 0
else
    # Process is not running
    echo "Darkbot is not running"
    exit 1
fi

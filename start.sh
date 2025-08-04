#!/bin/bash
# This script is used to start the application
source /opt/venv/bin/activate
python sneakerbot.py --interval 30 --check-profit --notify

#!/bin/bash
# This script is used during the build phase
python -m venv --copies /opt/venv
source /opt/venv/bin/activate
pip install -r requirements.txt

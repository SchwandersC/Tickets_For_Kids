#!/bin/bash
/opt/bin/entry_point.sh &  # Start Selenium in background
sleep 5
python3 main.py "$1"


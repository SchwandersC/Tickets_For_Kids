#!/bin/bash
# Start the Selenium server in the background.
# Use the original entrypoint command of the Selenium image.
/opt/bin/entry_point.sh &

# Wait for Selenium to start up.
sleep 5

# Now run your Python script.
python run_new_season.py

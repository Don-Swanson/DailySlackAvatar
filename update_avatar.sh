#!/bin/sh

# Exit on any error
set -e

# Print execution time for logging
date

# Run the script with upload
python daily_slack_avatar.py --upload

# Print success message
echo "Avatar updated successfully"

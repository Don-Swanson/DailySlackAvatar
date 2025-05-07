#!/bin/bash

# Default cron schedule is daily at 9 AM
DEFAULT_CRON_SCHEDULE="0 9 * * *"
CRON_SCHEDULE=${CRON_SCHEDULE:-$DEFAULT_CRON_SCHEDULE}

echo "Setting up cron schedule: $CRON_SCHEDULE"

# Replace the placeholder in the template with the actual schedule
cat /app/crontab.template | sed "s|\${CRON_SCHEDULE}|$CRON_SCHEDULE|g" > /etc/cron.d/slack-avatar-cron

# Give execution rights to the cron job
chmod 0644 /etc/cron.d/slack-avatar-cron

# Apply cron job
crontab /etc/cron.d/slack-avatar-cron

# Create or clear the log file
echo "Starting cron daemon..." > /var/log/cron.log
chmod 0644 /var/log/cron.log

# Start cron in foreground
exec cron -f 
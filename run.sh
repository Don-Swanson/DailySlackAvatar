#!/bin/bash

# Make the script executable
chmod +x update_avatar.sh

# Check if configuration exists
if [ ! -f .slack_config.json ]; then
  echo "No .slack_config.json found. You will need to set up your Slack token."
  echo "After container starts, you can run:"
  echo "docker-compose exec dailyslackavatar python daily_slack_avatar.py --setup-slack"
fi

# Pull the latest image from Docker Hub
echo "Pulling the latest image from Docker Hub..."
docker pull donswanson/dailyslackavatar:latest

# Start the container
docker-compose up -d

echo ""
echo "Daily Slack Avatar scheduler is now running!"
echo "The avatar will update daily at 9 AM"
echo ""
echo "You can check logs with:"
echo "docker-compose logs -f"
echo ""
echo "To run an update manually:"
echo "docker-compose exec dailyslackavatar ./update_avatar.sh"
echo "" 
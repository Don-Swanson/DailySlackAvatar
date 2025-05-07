FROM python:3.12-slim

# Install cron
RUN apt-get update && apt-get -y install cron && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

# Create directories if they don't exist
RUN mkdir -p foreground background output

# Set permissions for scripts
RUN chmod +x update_avatar.sh
RUN chmod +x docker-entrypoint.sh

# Create log file
RUN touch /var/log/cron.log

# Set environment variable defaults
ENV CRON_SCHEDULE="0 9 * * *"

# Run the entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"] 
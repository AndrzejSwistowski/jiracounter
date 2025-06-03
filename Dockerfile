# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Install cron and other necessary packages
RUN apt-get update && apt-get install -y \
    cron \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Set timezone (can be overridden with environment variable)
ENV TZ=Europe/Warsaw
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Create application directory
WORKDIR /app

# Copy the application code first
COPY . /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements/requirements.txt

# Create logs directory
RUN mkdir -p /app/logs

# Copy cron configuration
COPY docker/crontab /etc/cron.d/jira-etl
RUN chmod 0644 /etc/cron.d/jira-etl

# Apply cron job
RUN crontab /etc/cron.d/jira-etl

# Setup entrypoint script
RUN chmod +x /app/docker/entrypoint.sh

# Set only system environment variables
ENV PYTHONPATH=/app
ENV TZ=Europe/Warsaw

# Expose volume for logs
VOLUME ["/app/logs"]

# Use entrypoint script
ENTRYPOINT ["/app/docker/entrypoint.sh"]

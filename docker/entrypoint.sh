#!/bin/bash

# Entrypoint script for Jira ETL Docker container
set -e

echo "Starting Jira ETL Container..."
echo "Current time: $(date)"
echo "Timezone: $TZ"

# Create log files if they don't exist
touch /app/logs/cron.log
touch /app/logs/jira_etl_es.log

# Set permissions for log files
chmod 666 /app/logs/*.log

# Print environment info
echo "Python version: $(python --version)"
echo "Working directory: $(pwd)"
echo "PYTHONPATH: $PYTHONPATH"

# Validate required environment variables
if [ -z "$JIRA_API_TOKEN" ]; then
  echo "WARNING: JIRA_API_TOKEN is not set"
fi

if [ -z "$ELASTIC_URL" ] && [ -z "$ELASTIC_APIKEY" ]; then
  echo "WARNING: Elasticsearch connection variables not set"
fi

# Test the populate_es.py script
echo "Testing populate_es.py script..."
if python -c "import populate_es; print('Import successful')"; then
  echo "populate_es.py can be imported successfully"
else
  echo "ERROR: Cannot import populate_es.py"
  exit 1
fi

# Start cron in the background
echo "Starting cron daemon..."
cron

# Run an initial population to test everything works
echo "Running initial ETL test..."
cd /app
python populate_es.py --max-issues 10 || echo "Initial test run failed, but continuing with cron..."

echo "Cron started. ETL will run every hour."
echo "Logs will be written to /app/logs/cron.log and /app/logs/jira_etl_es.log"

# Keep the container running and tail the logs
echo "Tailing cron log..."
tail -f /app/logs/cron.log

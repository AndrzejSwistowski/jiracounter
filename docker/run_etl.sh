#!/bin/bash

# ETL runner script for cron jobs
# This script ensures environment variables are properly loaded before running the ETL

set -e

echo "========================================="
echo "JIRA ETL Cron Job - $(date)"
echo "========================================="

# Load environment variables from the Docker init process
# This ensures all Docker environment variables are available to the cron job
if [ -f /proc/1/environ ]; then
  echo "Loading environment variables from Docker init process..."
  export $(cat /proc/1/environ | tr '\0' '\n' | grep -E '^(JIRA_|ELASTIC_|KIBANA_|DOCKER_|TZ|PYTHONPATH)' | xargs)
fi

# Verify critical environment variables are set
echo "Environment check:"
echo "  DOCKER_ENV: ${DOCKER_ENV:-Not set}"
echo "  ELASTIC_URL: ${ELASTIC_URL:-Not set}"
echo "  ELASTIC_APIKEY: ${ELASTIC_APIKEY:+***SET***}"
echo "  JIRA_BASE_URL: ${JIRA_BASE_URL:-Not set}"
echo "  JIRA_API_TOKEN: ${JIRA_API_TOKEN:+***SET***}"
echo "  PYTHONPATH: ${PYTHONPATH:-Not set}"
echo "  TZ: ${TZ:-Not set}"

# Change to the app directory
cd /app

# Run the ETL script with proper environment
echo "Starting ETL process..."
exec /usr/local/bin/python populate_es.py "$@"

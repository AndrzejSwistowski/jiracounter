#!/bin/bash

# Simple ETL runner script for cron jobs
# This script ensures environment variables are properly loaded before running the ETL

set -e

echo "========================================="
echo "JIRA ETL Cron Job - $(date)"
echo "========================================="

# Debug: Show initial environment
echo "Initial environment:"
env | grep -E "(ELASTIC_|JIRA_|DOCKER_|PYTHONPATH|TZ)" | sort || echo "No matching env vars found"
echo ""

# Source environment variables from a file that's created at container startup
if [ -f /app/.env ]; then
  echo "Loading environment variables from /app/.env..."
  set -a # automatically export all variables
  source /app/.env
  set +a # turn off automatic export
  echo "Successfully sourced /app/.env"
else
  echo "ERROR: /app/.env file not found!"
fi

# Debug: Show environment after loading
echo ""
echo "Environment after loading:"
env | grep -E "(ELASTIC_|JIRA_|DOCKER_|PYTHONPATH|TZ)" | sort || echo "No matching env vars found"
echo ""

# Fallback: try to load from proc if .env doesn't exist
if [ -z "$ELASTIC_URL" ] && [ -f /proc/1/environ ]; then
  echo "ELASTIC_URL still empty, loading environment variables from Docker init process..."
  while IFS= read -r -d '' env_var; do
    if [[ "$env_var" =~ ^(JIRA_|ELASTIC_|KIBANA_|DOCKER_|TZ|PYTHONPATH) ]]; then
      export "$env_var"
      echo "Exported from proc: $env_var"
    fi
  done </proc/1/environ
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

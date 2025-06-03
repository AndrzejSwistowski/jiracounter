#!/bin/bash

# Linux/Mac bash script to stop the Jira ETL Docker container

echo "Stopping Jira ETL Docker Container..."

docker-compose -f docker-compose-etl.yml down

if [ $? -ne 0 ]; then
  echo "ERROR: Failed to stop container!"
  read -p "Press Enter to exit..."
  exit 1
fi

echo "Container stopped successfully!"

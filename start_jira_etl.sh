#!/bin/bash

# Linux/Mac bash script to start the Jira ETL Docker container

echo "Starting Jira ETL Docker Container..."

# Check if .env file exists
if [ ! -f .env ]; then
  echo "ERROR: .env file not found!"
  echo "Please copy .env.template to .env and configure your settings."
  echo "Example: cp .env.template .env"
  read -p "Press Enter to exit..."
  exit 1
fi

# Build and start the container
echo "Building Docker image..."
docker-compose -f docker-compose-etl.yml build

if [ $? -ne 0 ]; then
  echo "ERROR: Docker build failed!"
  read -p "Press Enter to exit..."
  exit 1
fi

echo "Starting container..."
docker-compose -f docker-compose-etl.yml up -d

if [ $? -ne 0 ]; then
  echo "ERROR: Failed to start container!"
  read -p "Press Enter to exit..."
  exit 1
fi

echo "Container started successfully!"
echo ""
echo "To view logs: docker-compose -f docker-compose-etl.yml logs -f"
echo "To stop: docker-compose -f docker-compose-etl.yml down"
echo ""

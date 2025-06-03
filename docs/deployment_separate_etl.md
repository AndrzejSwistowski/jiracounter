# JIRA ETL Deployment Guide - Separate ETL Service

This guide explains how to deploy the JIRA ETL application as a separate service that communicates with the existing Elasticsearch stack.

## Architecture Overview

The deployment consists of two separate Docker Compose configurations:

1. **Main Elasticsearch Stack** (`docker-compose.yml`):
   - Elasticsearch service
   - Kibana service  
   - Elasticsearch Head service
   - Shared network: `elastic`

2. **ETL Service** (`docker-compose-etl.yml`):
   - JIRA ETL application with cron scheduling
   - Connects to the same `elastic` network
   - Communicates with Elasticsearch via internal Docker networking

## Prerequisites

1. **Environment Variables**: Create a `.env` file in the project root with your configuration:
   ```env
   # JIRA Configuration
   JIRA_BASE_URL=https://your-company.atlassian.net
   JIRA_USERNAME=your-email@company.com
   JIRA_API_TOKEN=your_jira_api_token
   
   # Optional: Elasticsearch Configuration (defaults to internal Docker services)
   # ELASTIC_URL=http://elasticsearch:9200
   # ELASTIC_USERNAME=elastic
   # ELASTIC_PASSWORD=your_password
   
   # Timezone
   TZ=Europe/Warsaw
   
   # Logging
   JIRA_LOG_LEVEL=INFO
   ```

2. **JIRA API Token**: Generate an API token from your Jira account settings
3. **Docker and Docker Compose** installed on your system

## Deployment Steps

### Step 1: Start the Elasticsearch Stack

First, start the main Elasticsearch infrastructure:

```bash
# Start Elasticsearch, Kibana, and ES Head
docker-compose up -d

# Verify services are running
docker-compose ps

# Check Elasticsearch health
curl http://localhost:9200/_cluster/health

# Access Kibana at http://localhost:5601
# Access ES Head at http://localhost:9100
```

### Step 2: Wait for Elasticsearch to be Ready

Ensure Elasticsearch is fully initialized before starting the ETL service:

```bash
# Wait for healthy status
docker-compose logs -f elasticsearch

# Or check health endpoint
curl http://localhost:9200/_cluster/health?wait_for_status=green&timeout=60s
```

### Step 3: Start the ETL Service

Once Elasticsearch is running, start the ETL service:

```bash
# Start the ETL service
docker-compose -f docker-compose-etl.yml up -d

# Check ETL service status
docker-compose -f docker-compose-etl.yml ps

# View ETL logs
docker-compose -f docker-compose-etl.yml logs -f jira-etl
```

## Network Communication

The ETL service connects to the Elasticsearch stack through Docker's internal networking:

- **Network**: Both services use the `elastic` network
- **Elasticsearch URL**: `http://elasticsearch:9200` (internal Docker hostname)
- **Service Discovery**: Docker's built-in DNS resolves service names to container IPs

## Monitoring and Troubleshooting

### Check Service Status
```bash
# Check main stack
docker-compose ps

# Check ETL service
docker-compose -f docker-compose-etl.yml ps

# Check network connectivity
docker network ls
docker network inspect jiracouter_elastic
```

### View Logs
```bash
# Elasticsearch logs
docker-compose logs elasticsearch

# Kibana logs
docker-compose logs kibana

# ETL logs
docker-compose -f docker-compose-etl.yml logs jira-etl

# Follow ETL logs in real-time
docker-compose -f docker-compose-etl.yml logs -f jira-etl
```

### Manual ETL Execution
```bash
# Run ETL manually (one-time execution)
docker-compose -f docker-compose-etl.yml exec jira-etl python -m src.jira_etl.etl_main
```

### Debug Network Connectivity
```bash
# Enter ETL container
docker-compose -f docker-compose-etl.yml exec jira-etl bash

# Test Elasticsearch connectivity from within ETL container
curl http://elasticsearch:9200/_cluster/health

# Test from host machine
curl http://localhost:9200/_cluster/health
```

## ETL Schedule

The ETL service runs on a cron schedule defined in `/docker/crontab`:

```cron
# Run ETL every hour at minute 0
0 * * * * cd /app && python -m src.jira_etl.etl_main >> /app/logs/cron.log 2>&1

# Run full sync daily at 2 AM
0 2 * * * cd /app && python -m src.jira_etl.etl_main --full-sync >> /app/logs/cron.log 2>&1
```

## Data Flow

1. **Extract**: ETL service connects to JIRA API to fetch issues
2. **Transform**: Issues are processed and formatted for Elasticsearch
3. **Load**: Transformed data is indexed into Elasticsearch via `http://elasticsearch:9200`
4. **Visualize**: Data is accessible through Kibana at `http://localhost:5601`

## Scaling and Production Considerations

### Resource Allocation
```yaml
# Add resource limits to docker-compose-etl.yml
services:
  jira-etl:
    # ... existing configuration ...
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
```

### Persistent Storage
```yaml
# Add persistent volumes for logs
volumes:
  - ./logs:/app/logs
  - etl_data:/app/data

volumes:
  etl_data:
    driver: local
```

### Health Checks
```yaml
# Add health check to ETL service
healthcheck:
  test: ["CMD", "python", "-c", "import requests; requests.get('http://elasticsearch:9200/_cluster/health')"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

## Cleanup

### Stop Services
```bash
# Stop ETL service
docker-compose -f docker-compose-etl.yml down

# Stop main stack
docker-compose down
```

### Remove Everything
```bash
# Stop and remove all containers, networks, and volumes
docker-compose -f docker-compose-etl.yml down -v
docker-compose down -v

# Remove images (optional)
docker image prune -f
```

## Troubleshooting Common Issues

### 1. ETL Can't Connect to Elasticsearch
- Ensure Elasticsearch is running: `docker-compose ps`
- Check network connectivity: `docker network inspect jiracouter_elastic`
- Verify ETL service is on the correct network

### 2. JIRA Authentication Issues
- Verify API token is correct
- Check JIRA URL format
- Ensure username matches token owner

### 3. Cron Job Not Running
- Check cron logs: `docker-compose -f docker-compose-etl.yml logs jira-etl`
- Verify timezone settings
- Check crontab syntax in `/docker/crontab`

### 4. Elasticsearch Index Issues
- Check index creation: `curl http://localhost:9200/_cat/indices`
- Verify mapping: `curl http://localhost:9200/jira_issues/_mapping`
- Review ETL logs for indexing errors

## Next Steps

1. Configure index templates in Elasticsearch for better data management
2. Set up monitoring and alerting for ETL failures
3. Implement data retention policies
4. Add backup strategies for Elasticsearch data

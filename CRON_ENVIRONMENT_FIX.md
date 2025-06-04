# Fix for Cron Environment Variables Issue

## Problem
The Docker container's cron jobs were failing because environment variables (like `ELASTIC_URL`, `ELASTIC_APIKEY`, etc.) were not being passed to the cron execution environment. This caused the application to fall back to default values, trying to connect to `localhost:9200` instead of the configured Elasticsearch URL.

## Root Cause
- Cron jobs run in a minimal environment without inheriting Docker environment variables
- The application's configuration correctly uses `DOCKER_ENV` to determine whether to use `elasticsearch` (Docker container name) or `localhost` as the default host
- However, when cron runs, `DOCKER_ENV` and other environment variables are not available

## Solution
Created two wrapper scripts that ensure environment variables are properly loaded before running the ETL:

### 1. `/app/docker/run_etl_simple.sh` (Recommended)
- Uses a `.env` file created at container startup by the entrypoint script
- Falls back to reading from `/proc/1/environ` if the `.env` file doesn't exist
- More reliable and simpler approach

### 2. `/app/docker/run_etl.sh` (Alternative)
- Directly reads environment variables from `/proc/1/environ`
- Uses the Docker init process environment

## Changes Made

### Modified Files:
1. **`docker/crontab`** - Updated to use the wrapper script instead of calling Python directly
2. **`docker/run_etl_simple.sh`** - New wrapper script (recommended approach)
3. **`docker/run_etl.sh`** - Alternative wrapper script
4. **`docker/entrypoint.sh`** - Creates `.env` file with environment variables for cron
5. **`Dockerfile`** - Makes wrapper scripts executable

### Key Changes:

#### Before (crontab):
```
0 * * * * cd /app && /usr/local/bin/python populate_es.py --max-issues 1000 >> /app/logs/cron.log 2>&1
```

#### After (crontab):
```
0 * * * * cd /app && /app/docker/run_etl_simple.sh --max-issues 1000 >> /app/logs/cron.log 2>&1
```

#### New Environment File Creation (entrypoint.sh):
```bash
# Create environment variables file for cron to use
echo "Creating environment file for cron jobs..."
env | grep -E '^(JIRA_|ELASTIC_|KIBANA_|DOCKER_|TZ|PYTHONPATH)' > /app/.env
chmod 600 /app/.env
echo "Environment file created with $(wc -l < /app/.env) variables"
```

## Testing

### 1. Rebuild and Deploy
```powershell
# Stop current container
docker-compose -f docker-compose-etl-custom-dns.yml down

# Rebuild with changes
docker-compose -f docker-compose-etl-custom-dns.yml build

# Start with logs
docker-compose -f docker-compose-etl-custom-dns.yml up -d
docker-compose -f docker-compose-etl-custom-dns.yml logs -f
```

### 2. Manual Testing
```powershell
# Test the wrapper script manually
docker-compose -f docker-compose-etl-custom-dns.yml exec jira-etl /app/docker/run_etl_simple.sh --max-issues 10

# Check environment variables are loaded
docker-compose -f docker-compose-etl-custom-dns.yml exec jira-etl cat /app/.env

# Check cron logs
docker-compose -f docker-compose-etl-custom-dns.yml exec jira-etl cat /app/logs/cron.log
```

### 3. Verify Cron Execution
```powershell
# Check crontab is installed
docker-compose -f docker-compose-etl-custom-dns.yml exec jira-etl crontab -l

# Check cron process is running
docker-compose -f docker-compose-etl-custom-dns.yml exec jira-etl ps aux | grep cron

# Wait for next hourly run and check logs
docker-compose -f docker-compose-etl-custom-dns.yml logs -f jira-etl
```

## Expected Results

### Environment Check Output:
The wrapper script will now show proper environment variables:
```
Environment check:
  DOCKER_ENV: true
  ELASTIC_URL: http://elastic.voyager.pl:9200
  ELASTIC_APIKEY: ***SET***
  JIRA_BASE_URL: https://voyager-team.atlassian.net
  JIRA_API_TOKEN: ***SET***
  PYTHONPATH: /app
  TZ: Europe/Warsaw
```

### Successful ETL Connection:
Instead of the previous `localhost:9200` connection error, you should see:
```
Successfully connected to Elasticsearch cluster: your-cluster-name / Status: green
```

## Troubleshooting

### If the simple approach doesn't work:
1. Switch to the alternative wrapper by updating the crontab:
   ```bash
   0 * * * * cd /app && /app/docker/run_etl.sh --max-issues 1000 >> /app/logs/cron.log 2>&1
   ```

2. Or add explicit environment variable exports to the crontab:
   ```bash
   0 * * * * cd /app && ELASTIC_URL=http://elastic.voyager.pl:9200 DOCKER_ENV=true /usr/local/bin/python populate_es.py --max-issues 1000 >> /app/logs/cron.log 2>&1
   ```

### Debug Commands:
```powershell
# Check if .env file is created properly
docker-compose -f docker-compose-etl-custom-dns.yml exec jira-etl ls -la /app/.env

# Check environment variables in running container
docker-compose -f docker-compose-etl-custom-dns.yml exec jira-etl env | grep -E "ELASTIC|JIRA|DOCKER"

# Test connection manually
docker-compose -f docker-compose-etl-custom-dns.yml exec jira-etl python -c "import config; print('ELASTIC_URL:', config.ELASTIC_URL); print('ES_HOST:', config.ES_HOST)"
```

This fix ensures that the cron jobs have access to all necessary environment variables, resolving the connection issue to Elasticsearch.

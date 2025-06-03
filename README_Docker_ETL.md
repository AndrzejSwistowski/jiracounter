# Jira ETL Docker Container

This Docker container runs the Jira ETL process (`populate_es.py`) automatically via cron every hour to sync data from Jira to Elasticsearch.

## Features

- **Automated Scheduling**: Runs ETL process every hour via cron
- **Persistent Logs**: Logs are stored in a mounted volume
- **Environment Configuration**: Easy configuration via environment variables
- **Health Monitoring**: Initial test run and continuous log monitoring
- **Error Handling**: Graceful error handling and logging

## Quick Start

### 1. Configure Environment

Copy the environment template and configure your settings:

```bash
# Windows
copy .env.template .env

# Linux/Mac
cp .env.template .env
```

Edit `.env` file with your actual credentials:

```env
JIRA_API_TOKEN=your_actual_jira_api_token
ELASTIC_URL=http://your-elasticsearch-host:9200
ELASTIC_APIKEY=your_actual_elastic_api_key
```

### 2. Start the Container

**Windows:**
```cmd
# Using batch script
start_jira_etl.cmd

# Or using PowerShell
.\start_jira_etl.ps1

# Or manually
docker-compose -f docker-compose-etl.yml up -d
```

**Linux/Mac:**
```bash
docker-compose -f docker-compose-etl.yml up -d
```

### 3. Monitor Logs

```bash
# Follow all container logs
docker-compose -f docker-compose-etl.yml logs -f

# Follow only cron logs
docker-compose -f docker-compose-etl.yml exec jira-etl tail -f /app/logs/cron.log

# Follow ETL application logs
docker-compose -f docker-compose-etl.yml exec jira-etl tail -f /app/logs/jira_etl_es.log
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `JIRA_BASE_URL` | Jira instance URL | https://voyager-team.atlassian.net | Yes |
| `JIRA_USERNAME` | Jira username | andrzej.swistowski@voyager.pl | Yes |
| `JIRA_API_TOKEN` | Jira API token | - | Yes |
| `ELASTIC_URL` | Elasticsearch URL | - | Yes |
| `ELASTIC_APIKEY` | Elasticsearch API key | - | Yes* |
| `ELASTIC_USERNAME` | Elasticsearch username | - | Yes* |
| `ELASTIC_PASSWORD` | Elasticsearch password | - | Yes* |
| `TZ` | Timezone | Europe/Warsaw | No |
| `JIRA_LOG_LEVEL` | Log level | INFO | No |

*Either API key or username/password is required for Elasticsearch authentication.

### Cron Schedule

The default schedule is every hour (`0 * * * *`). To modify:

1. Edit `docker/crontab` file
2. Rebuild the container: `docker-compose -f docker-compose-etl.yml build`
3. Restart: `docker-compose -f docker-compose-etl.yml up -d`

### ETL Parameters

The ETL process runs with these default parameters:
- `--max-issues 1000`: Process maximum 1000 issues per run
- Incremental sync (uses last sync date)
- Bulk size: 100 records per batch

To modify, edit the cron command in `docker/crontab`.

## Commands

### Container Management

```bash
# Start container
docker-compose -f docker-compose-etl.yml up -d

# Stop container
docker-compose -f docker-compose-etl.yml down

# Restart container
docker-compose -f docker-compose-etl.yml restart

# View container status
docker-compose -f docker-compose-etl.yml ps

# Rebuild container
docker-compose -f docker-compose-etl.yml build --no-cache
```

### Manual ETL Execution

```bash
# Run ETL manually (one-time)
docker-compose -f docker-compose-etl.yml exec jira-etl python populate_es.py

# Run with specific parameters
docker-compose -f docker-compose-etl.yml exec jira-etl python populate_es.py --max-issues 500 --verbose

# Run full sync
docker-compose -f docker-compose-etl.yml exec jira-etl python populate_es.py --full-sync
```

### Logs and Debugging

```bash
# View cron logs
docker-compose -f docker-compose-etl.yml exec jira-etl cat /app/logs/cron.log

# View application logs
docker-compose -f docker-compose-etl.yml exec jira-etl cat /app/logs/jira_etl_es.log

# Check cron status
docker-compose -f docker-compose-etl.yml exec jira-etl crontab -l

# Access container shell
docker-compose -f docker-compose-etl.yml exec jira-etl bash
```

## Troubleshooting

### Common Issues

1. **Container fails to start**
   - Check environment variables in `.env` file
   - Verify Elasticsearch connection: `docker-compose -f docker-compose-etl.yml logs`

2. **ETL fails**
   - Check Jira API token permissions
   - Verify Elasticsearch authentication
   - Review logs: `/app/logs/cron.log` and `/app/logs/jira_etl_es.log`

3. **No data syncing**
   - Check cron is running: `docker-compose -f docker-compose-etl.yml exec jira-etl ps aux | grep cron`
   - Verify cron schedule: `docker-compose -f docker-compose-etl.yml exec jira-etl crontab -l`

### Log Locations

- Container logs: `docker-compose -f docker-compose-etl.yml logs`
- Cron execution logs: `./logs/cron.log`
- ETL application logs: `./logs/jira_etl_es.log`

### Testing Connection

```bash
# Test Jira connection
docker-compose -f docker-compose-etl.yml exec jira-etl python -c "from jiraservice import JiraService; js = JiraService(); print('Jira connection OK')"

# Test Elasticsearch connection
docker-compose -f docker-compose-etl.yml exec jira-etl python -c "from es_populate import JiraElasticsearchPopulator; pop = JiraElasticsearchPopulator(); pop.connect(); print('ES connection OK')"
```

## File Structure

```
.
├── Dockerfile                     # Docker container definition
├── docker-compose-etl.yml         # Docker Compose configuration
├── .env.template                  # Environment variables template
├── .env                          # Your environment configuration
├── start_jira_etl.cmd            # Windows startup script
├── start_jira_etl.ps1            # PowerShell startup script
├── docker/
│   ├── crontab                   # Cron schedule configuration
│   └── entrypoint.sh             # Container startup script
├── logs/                         # Log files (mounted volume)
│   ├── cron.log                  # Cron execution logs
│   └── jira_etl_es.log          # ETL application logs
└── [application files...]
```

## Security Notes

- Store sensitive credentials in `.env` file (not in version control)
- Use API tokens instead of passwords
- Limit Elasticsearch user permissions to required indices only
- Regularly rotate API tokens and credentials

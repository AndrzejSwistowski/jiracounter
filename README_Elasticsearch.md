# Elasticsearch and Kibana Docker Setup with Polish Language Support

This setup provides Elasticsearch 8.11.3 and Kibana with Polish full-text search capabilities for the Jira Counter application.

## Prerequisites

- Docker Desktop installed and running
- Python 3.x with `requests` library

## Quick Start

### Option 1: Using Windows Batch Script
```cmd
start_elasticsearch.cmd
```

### Option 2: Using PowerShell Script
```powershell
.\start_elasticsearch.ps1
```

### Option 3: Manual Docker Commands
```cmd
# Build the custom Elasticsearch image with Polish plugins
docker-compose build elasticsearch

# Start all services
docker-compose up -d

# Initialize Elasticsearch with Polish mappings
python init_elasticsearch.py
```

## What Gets Started

- **Elasticsearch** (port 9200): Search engine with Polish language analyzers
- **Kibana** (port 5601): Web interface for Elasticsearch
- **Elasticsearch Head** (port 9100): Cluster management interface

## Services Access

- Elasticsearch: http://localhost:9200
- Kibana: Configured via `KIBANA_URL` environment variable (default: http://localhost:5601)
- Elasticsearch Head: http://localhost:9100

> **Note**: Kibana URL can be customized by setting the `KIBANA_URL` environment variable or by configuring `KIBANA_HOST`, `KIBANA_PORT`, and `KIBANA_USE_SSL` in the configuration.

## Polish Language Features

The setup includes:

1. **Custom Analyzers**:
   - `polish_standard`: Basic Polish text analysis
   - `polish_stempel`: Advanced Polish stemming

2. **Installed Plugins**:
   - `analysis-icu`: International Components for Unicode
   - `analysis-stempel`: Polish language stemmer

3. **Index Fields with Polish Support**:
   - `summary`: Issue summaries with Polish analysis
   - `description`: Issue descriptions with Polish analysis
   - `comment`: Comments with Polish analysis

## Data Storage

- **Elasticsearch data**: Stored in Docker volume `elasticsearch_data`
- **Kibana data**: Stored in Docker volume `kibana_data`
- **Mount data**: Available at `./mountdata` (mapped to `/usr/share/elasticsearch/mountdata`)

## Management Commands

### Check Status
```cmd
python check_elasticsearch.py
```

### Stop Services
```cmd
stop_elasticsearch.cmd
```

### Stop and Remove All Data
```cmd
docker-compose down -v
```

### View Logs
```cmd
# All services
docker-compose logs -f

# Elasticsearch only
docker-compose logs -f elasticsearch

# Kibana only
docker-compose logs -f kibana
```

## Testing Polish Search

After initialization, you can test Polish text analysis:

```bash
# Test Polish analyzer
curl -X POST "localhost:9200/jira-changelog/_analyze" -H 'Content-Type: application/json' -d'
{
  "analyzer": "polish_stempel",
  "text": "Aplikacja działa poprawnie"
}'
```

## Troubleshooting

### Elasticsearch Won't Start
1. Ensure Docker Desktop is running
2. Check if ports 9200, 5601, 9100 are available
3. Increase Docker memory to at least 4GB
4. Check logs: `docker-compose logs elasticsearch`

### Plugins Not Installed
1. Rebuild the image: `docker-compose build --no-cache elasticsearch`
2. Check plugin status: `python check_elasticsearch.py`

### Memory Issues
If you get memory errors:
1. Increase Docker Desktop memory allocation
2. Reduce Elasticsearch heap size in docker-compose.yml:
   ```yaml
   - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
   ```

## File Structure

```
├── docker-compose.yml          # Main Docker Compose configuration
├── Dockerfile.elasticsearch    # Custom Elasticsearch image with plugins
├── es_mapping_polish.py        # Elasticsearch mappings with Polish support
├── init_elasticsearch.py       # Index initialization script
├── check_elasticsearch.py      # Status checking script
├── start_elasticsearch.cmd     # Windows batch startup script
├── start_elasticsearch.ps1     # PowerShell startup script
├── stop_elasticsearch.cmd      # Windows batch stop script
└── mountdata/                  # Directory for mounted data
```

## Development Notes

- Security is disabled for development convenience
- Data persists between container restarts
- Use `docker-compose down -v` to completely reset data
- The setup uses single-node Elasticsearch (not suitable for production)

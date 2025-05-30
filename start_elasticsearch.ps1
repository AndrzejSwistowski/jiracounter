# Start Elasticsearch and Kibana with Docker Compose
Write-Host "Starting Elasticsearch and Kibana with Docker Compose..." -ForegroundColor Green

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Error: Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Create mountdata directory if it doesn't exist
if (!(Test-Path "mountdata")) {
    Write-Host "Creating mountdata directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "mountdata" | Out-Null
}

# Start Docker Compose services
Write-Host "Building custom Elasticsearch image with Polish plugins..." -ForegroundColor Yellow
docker-compose build elasticsearch

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Error: Failed to build Elasticsearch image" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Starting services..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Error: Failed to start Docker services" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✓ Services started successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Wait for Elasticsearch to be ready and initialize
Write-Host "Initializing Elasticsearch with Polish support..." -ForegroundColor Yellow
python init_elasticsearch.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠ Warning: Elasticsearch initialization failed or incomplete" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Services are now running:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Elasticsearch: http://localhost:9200" -ForegroundColor White
Write-Host "Kibana:        http://localhost:5601" -ForegroundColor White
Write-Host "ES Head:       http://localhost:9100" -ForegroundColor White
Write-Host ""
Write-Host "To stop services: docker-compose down" -ForegroundColor Gray
Write-Host "To view logs:    docker-compose logs -f" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter to exit"

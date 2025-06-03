# PowerShell script to start the Jira ETL Docker container

Write-Host "Starting Jira ETL Docker Container..." -ForegroundColor Green

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    Write-Host "Please copy .env.template to .env and configure your settings." -ForegroundColor Yellow
    Write-Host "Example: Copy-Item .env.template .env" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Build and start the container
Write-Host "Building Docker image..." -ForegroundColor Yellow
docker-compose -f docker-compose-etl.yml build

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker build failed!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Starting container..." -ForegroundColor Yellow
docker-compose -f docker-compose-etl.yml up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to start container!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Container started successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "To view logs: docker-compose -f docker-compose-etl.yml logs -f" -ForegroundColor Cyan
Write-Host "To stop: docker-compose -f docker-compose-etl.yml down" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to continue"

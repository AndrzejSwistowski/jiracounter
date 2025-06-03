# PowerShell script to stop the Jira ETL Docker container

Write-Host "Stopping Jira ETL Docker Container..." -ForegroundColor Yellow

docker-compose -f docker-compose-etl.yml down

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to stop container!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Container stopped successfully!" -ForegroundColor Green
Read-Host "Press Enter to continue"

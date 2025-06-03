@echo off
REM Windows batch script to stop the Jira ETL Docker container

echo Stopping Jira ETL Docker Container...

docker-compose -f docker-compose-etl.yml down

if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to stop container!
    pause
    exit /b 1
)

echo Container stopped successfully!
pause

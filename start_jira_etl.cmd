@echo off
REM Windows batch script to start the Jira ETL Docker container

echo Starting Jira ETL Docker Container...

REM Check if .env file exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please copy .env.template to .env and configure your settings.
    echo Example: copy .env.template .env
    pause
    exit /b 1
)

REM Build and start the container
echo Building Docker image...
docker-compose -f docker-compose-etl.yml build

if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker build failed!
    pause
    exit /b 1
)

echo Starting container...
docker-compose -f docker-compose-etl.yml up -d

if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to start container!
    pause
    exit /b 1
)

echo Container started successfully!
echo.
echo To view logs: docker-compose -f docker-compose-etl.yml logs -f
echo To stop: docker-compose -f docker-compose-etl.yml down
echo.
pause

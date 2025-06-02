@echo off
echo Stopping Elasticsearch and Kibana services...

docker-compose down

if errorlevel 1 (
    echo Error: Failed to stop services
    pause
    exit /b 1
)

echo.
echo Services stopped successfully!
echo.
echo To remove volumes (delete all data): docker-compose down -v
echo To start services again: start_elasticsearch.cmd
echo.
pause

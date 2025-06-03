@echo off
REM Windows batch script to view Jira ETL logs

echo Jira ETL Docker Container Logs
echo ================================
echo.
echo 1. View all container logs (live)
echo 2. View cron execution logs
echo 3. View ETL application logs
echo 4. View last 50 lines of cron logs
echo 5. View last 50 lines of ETL logs
echo 6. Exit
echo.

set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" (
    echo Following all container logs... Press Ctrl+C to exit.
    docker-compose -f docker-compose-etl.yml logs -f
) else if "%choice%"=="2" (
    echo Following cron logs... Press Ctrl+C to exit.
    docker-compose -f docker-compose-etl.yml exec jira-etl tail -f /app/logs/cron.log
) else if "%choice%"=="3" (
    echo Following ETL application logs... Press Ctrl+C to exit.
    docker-compose -f docker-compose-etl.yml exec jira-etl tail -f /app/logs/jira_etl_es.log
) else if "%choice%"=="4" (
    echo Last 50 lines of cron logs:
    echo =============================
    docker-compose -f docker-compose-etl.yml exec jira-etl tail -n 50 /app/logs/cron.log
    pause
) else if "%choice%"=="5" (
    echo Last 50 lines of ETL logs:
    echo ===========================
    docker-compose -f docker-compose-etl.yml exec jira-etl tail -n 50 /app/logs/jira_etl_es.log
    pause
) else if "%choice%"=="6" (
    exit /b 0
) else (
    echo Invalid choice. Please try again.
    pause
    goto :eof
)

@echo off
REM Complete setup and management script for Jira ETL Docker container

:main
cls
echo ===============================================
echo    Jira ETL Docker Container Management
echo ===============================================
echo.
echo Current Status:
docker-compose -f docker-compose-etl.yml ps 2>nul
echo.
echo Options:
echo 1. First-time setup (create .env from template)
echo 2. Start ETL container
echo 3. Stop ETL container
echo 4. Restart ETL container
echo 5. View logs
echo 6. Manual ETL operations
echo 7. Check container health
echo 8. Clean up (remove containers and images)
echo 9. Exit
echo.

set /p choice="Enter your choice (1-9): "

if "%choice%"=="1" goto setup
if "%choice%"=="2" goto start
if "%choice%"=="3" goto stop
if "%choice%"=="4" goto restart
if "%choice%"=="5" goto logs
if "%choice%"=="6" goto manual
if "%choice%"=="7" goto health
if "%choice%"=="8" goto cleanup
if "%choice%"=="9" goto exit
echo Invalid choice. Please try again.
pause
goto main

:setup
echo Setting up Jira ETL for first time...
if exist .env (
    echo .env file already exists. 
    set /p overwrite="Overwrite existing .env? (y/n): "
    if /i not "%overwrite%"=="y" goto main
)
copy .env.template .env
echo.
echo .env file created. Please edit it with your actual credentials:
echo - JIRA_API_TOKEN: Your Jira API token
echo - ELASTIC_URL: Your Elasticsearch URL
echo - ELASTIC_APIKEY: Your Elasticsearch API key
echo.
echo After editing .env, you can start the container with option 2.
pause
goto main

:start
echo Starting Jira ETL container...
if not exist .env (
    echo ERROR: .env file not found! Please run setup first (option 1).
    pause
    goto main
)
docker-compose -f docker-compose-etl.yml up -d --build
echo Container started. Check logs with option 5.
pause
goto main

:stop
echo Stopping Jira ETL container...
docker-compose -f docker-compose-etl.yml down
echo Container stopped.
pause
goto main

:restart
echo Restarting Jira ETL container...
docker-compose -f docker-compose-etl.yml restart
echo Container restarted.
pause
goto main

:logs
call view_logs.cmd
goto main

:manual
call manual_etl.cmd
goto main

:health
echo Checking container health...
echo.
echo Container status:
docker-compose -f docker-compose-etl.yml ps
echo.
echo Recent logs:
docker-compose -f docker-compose-etl.yml logs --tail=10
echo.
echo Cron status:
docker-compose -f docker-compose-etl.yml exec jira-etl ps aux | findstr cron
pause
goto main

:cleanup
echo WARNING: This will remove all containers and images!
set /p confirm="Are you sure? Type 'yes' to continue: "
if /i not "%confirm%"=="yes" goto main
echo Stopping and removing containers...
docker-compose -f docker-compose-etl.yml down
echo Removing images...
docker image rm jiracouter_jira-etl 2>nul
echo Cleanup completed.
pause
goto main

:exit
echo Goodbye!
exit /b 0

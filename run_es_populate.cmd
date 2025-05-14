@echo off
REM Get current timestamp for the log file
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "TIMESTAMP=%dt:~0,8%_%dt:~8,6%"
set "LOG_FILE=logs\es_populate_task_%TIMESTAMP%.log"

echo ===== Jira to Elasticsearch ETL Script ===== >> "%LOG_FILE%"
echo Started at: %date% %time% >> "%LOG_FILE%"
echo ===== Jira to Elasticsearch ETL Script =====
echo.

REM Create logs directory if it doesn't exist
if not exist logs mkdir logs
echo Logs directory ready.
echo Logs directory ready. >> "%LOG_FILE%"

REM Check if environment variables are already set in the system
set SYSTEM_ELASTIC_URL=%ELASTIC_URL%
set SYSTEM_ELASTIC_APIKEY=%ELASTIC_APIKEY%

REM Only set variables if they're not already set in the environment
if "%SYSTEM_ELASTIC_URL%"=="" (
    set ELASTIC_URL=http://elastic.voyager.pl:9200
    echo Using script-defined ELASTIC_URL
    echo Using script-defined ELASTIC_URL >> "%LOG_FILE%"
) else (
    echo Using system-defined ELASTIC_URL
    echo Using system-defined ELASTIC_URL >> "%LOG_FILE%"
)

if "%SYSTEM_ELASTIC_APIKEY%"=="" (
    echo WARNING: No ELASTIC_APIKEY found in environment variables >> "%LOG_FILE%"
    echo WARNING: No ELASTIC_APIKEY found in environment variables
    echo Please set ELASTIC_APIKEY as a system environment variable for security >> "%LOG_FILE%"
    echo Please set ELASTIC_APIKEY as a system environment variable for security
    echo or uncomment and set the API key in the script >> "%LOG_FILE%"
    echo or uncomment and set the API key in the script
    REM set ELASTIC_APIKEY=your_api_key_here
) else (
    echo Using system-defined ELASTIC_APIKEY
    echo Using system-defined ELASTIC_APIKEY >> "%LOG_FILE%"
)

REM Default values for script parameters
set DAYS=1
set AGENT_NAME=JiraETLAgent
set BULK_SIZE=100

REM Process command-line arguments
if "%1"=="--days" set DAYS=%2
if "%1"=="--full-sync" set FULL_SYNC=--full-sync
if "%1"=="--recreate-index" set RECREATE_INDEX=--recreate-index
if "%1"=="--confirm" set CONFIRM=--confirm
if "%1"=="--verbose" set VERBOSE=--verbose
if "%1"=="--agent" set AGENT_NAME=%2
if "%1"=="--bulk-size" set BULK_SIZE=%2

if "%3"=="--days" set DAYS=%4
if "%3"=="--full-sync" set FULL_SYNC=--full-sync
if "%3"=="--recreate-index" set RECREATE_INDEX=--recreate-index
if "%3"=="--confirm" set CONFIRM=--confirm
if "%3"=="--verbose" set VERBOSE=--verbose
if "%3"=="--agent" set AGENT_NAME=%4
if "%3"=="--bulk-size" set BULK_SIZE=%4

if "%5"=="--days" set DAYS=%6
if "%5"=="--full-sync" set FULL_SYNC=--full-sync
if "%5"=="--recreate-index" set RECREATE_INDEX=--recreate-index
if "%5"=="--confirm" set CONFIRM=--confirm
if "%5"=="--verbose" set VERBOSE=--verbose
if "%5"=="--agent" set AGENT_NAME=%6
if "%5"=="--bulk-size" set BULK_SIZE=%6

echo Environment variables:
echo ELASTIC_URL=%ELASTIC_URL% >> "%LOG_FILE%"
echo ELASTIC_URL=%ELASTIC_URL%
echo ELASTIC_APIKEY=***masked*** >> "%LOG_FILE%"
echo ELASTIC_APIKEY=***masked***

echo. >> "%LOG_FILE%"
echo.
echo ETL Configuration: >> "%LOG_FILE%"
echo ETL Configuration:
echo Days to process: %DAYS% >> "%LOG_FILE%"
echo Days to process: %DAYS%
echo Agent name: %AGENT_NAME% >> "%LOG_FILE%"
echo Agent name: %AGENT_NAME%
echo Bulk size: %BULK_SIZE% >> "%LOG_FILE%"
echo Bulk size: %BULK_SIZE%
if defined FULL_SYNC echo Full sync: Enabled >> "%LOG_FILE%" && echo Full sync: Enabled
if defined RECREATE_INDEX echo Recreate index: Enabled >> "%LOG_FILE%" && echo Recreate index: Enabled
if defined CONFIRM echo Skip confirmation: Enabled >> "%LOG_FILE%" && echo Skip confirmation: Enabled
if defined VERBOSE echo Verbose logging: Enabled >> "%LOG_FILE%" && echo Verbose logging: Enabled

echo.
echo Running Elasticsearch populator...
echo.
echo Running Elasticsearch populator... >> "%LOG_FILE%"
echo Start time: %time% >> "%LOG_FILE%"

REM Run the Python script with parameters and capture output to log file
python populate_es.py --days %DAYS% --agent "%AGENT_NAME%" --bulk-size %BULK_SIZE% %FULL_SYNC% %RECREATE_INDEX% %CONFIRM% %VERBOSE% >> "%LOG_FILE%" 2>&1

echo End time: %time% >> "%LOG_FILE%"
echo ETL process finished with exit code: %ERRORLEVEL% >> "%LOG_FILE%"

echo.
echo Execution complete. Check the logs folder for details.
echo Execution complete at %date% %time%. Check log file: %LOG_FILE% >> "%LOG_FILE%"

REM When running as a scheduled task, we don't want to pause
if "%1"=="--scheduled" (
  echo Running in scheduled mode, no pause.
  echo Running in scheduled mode, no pause. >> "%LOG_FILE%"
) else (
  pause
)
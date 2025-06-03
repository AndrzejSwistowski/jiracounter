@echo off
REM Windows batch script for manual Jira ETL operations

echo Jira ETL Manual Operations
echo ===========================
echo.
echo 1. Run ETL now (quick test - 10 issues)
echo 2. Run ETL now (normal - 1000 issues)
echo 3. Run full sync (ignore last sync date)
echo 4. Run with verbose logging
echo 5. Check ETL status and last sync
echo 6. Recreate Elasticsearch index
echo 7. Exit
echo.

set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" (
    echo Running quick ETL test...
    docker-compose -f docker-compose-etl.yml exec jira-etl python populate_es.py --max-issues 10 --verbose
) else if "%choice%"=="2" (
    echo Running normal ETL...
    docker-compose -f docker-compose-etl.yml exec jira-etl python populate_es.py --max-issues 1000
) else if "%choice%"=="3" (
    echo Running full sync...
    docker-compose -f docker-compose-etl.yml exec jira-etl python populate_es.py --full-sync --max-issues 5000
) else if "%choice%"=="4" (
    echo Running ETL with verbose logging...
    docker-compose -f docker-compose-etl.yml exec jira-etl python populate_es.py --verbose --max-issues 500
) else if "%choice%"=="5" (
    echo Checking ETL status...
    docker-compose -f docker-compose-etl.yml exec jira-etl python -c "from es_populate import JiraElasticsearchPopulator; p = JiraElasticsearchPopulator(); p.connect(); print('Last sync:', p.get_last_sync_date()); print('Summary:', p.get_database_summary())"
) else if "%choice%"=="6" (
    echo WARNING: This will delete and recreate the Elasticsearch index!
    set /p confirm="Are you sure? Type 'yes' to continue: "
    if /i "%confirm%"=="yes" (
        docker-compose -f docker-compose-etl.yml exec jira-etl python populate_es.py --recreate-index --confirm --full-sync
    ) else (
        echo Operation cancelled.
    )
) else if "%choice%"=="7" (
    exit /b 0
) else (
    echo Invalid choice. Please try again.
)

echo.
pause

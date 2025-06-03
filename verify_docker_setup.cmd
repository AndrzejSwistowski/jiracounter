@echo off
REM Docker setup verification script

echo Verifying Docker ETL Setup
echo ============================
echo.

REM Check if Docker is installed and running
echo 1. Checking Docker installation...
docker --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker is not installed or not running
    echo Please install Docker Desktop and make sure it's running
    pause
    exit /b 1
) else (
    docker --version
    echo ✓ Docker is installed
)

echo.
echo 2. Checking Docker Compose...
docker-compose --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker Compose is not available
    pause
    exit /b 1
) else (
    docker-compose --version
    echo ✓ Docker Compose is available
)

echo.
echo 3. Checking required files...
if not exist "Dockerfile" (
    echo ERROR: Dockerfile not found
    exit /b 1
) else (
    echo ✓ Dockerfile found
)

if not exist "docker-compose-etl.yml" (
    echo ERROR: docker-compose-etl.yml not found
    exit /b 1
) else (
    echo ✓ docker-compose-etl.yml found
)

if not exist "docker\crontab" (
    echo ERROR: docker\crontab not found
    exit /b 1
) else (
    echo ✓ Crontab configuration found
)

if not exist "docker\entrypoint.sh" (
    echo ERROR: docker\entrypoint.sh not found
    exit /b 1
) else (
    echo ✓ Entrypoint script found
)

if not exist ".env.template" (
    echo ERROR: .env.template not found
    exit /b 1
) else (
    echo ✓ Environment template found
)

if not exist "populate_es.py" (
    echo ERROR: populate_es.py not found
    exit /b 1
) else (
    echo ✓ ETL script found
)

echo.
echo 4. Checking Python requirements...
if not exist "requirements\requirements.txt" (
    echo WARNING: requirements.txt not found
) else (
    echo ✓ Requirements file found
)

echo.
echo 5. Environment configuration...
if not exist ".env" (
    echo WARNING: .env file not found
    echo You need to create .env from .env.template and configure it
) else (
    echo ✓ .env file exists
    echo Checking environment variables...
    
    findstr "JIRA_API_TOKEN=" .env | findstr "your_jira_api_token_here" >nul
    if %ERRORLEVEL% equ 0 (
        echo WARNING: JIRA_API_TOKEN still has default value
    ) else (
        echo ✓ JIRA_API_TOKEN appears to be configured
    )
    
    findstr "ELASTIC_URL=" .env >nul
    if %ERRORLEVEL% neq 0 (
        echo WARNING: ELASTIC_URL not found in .env
    ) else (
        echo ✓ ELASTIC_URL is configured
    )
)

echo.
echo 6. Testing Docker build (dry run)...
docker-compose -f docker-compose-etl.yml config >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker Compose configuration is invalid
    pause
    exit /b 1
) else (
    echo ✓ Docker Compose configuration is valid
)

echo.
echo Verification Results:
echo =====================
if exist ".env" (
    findstr "JIRA_API_TOKEN=" .env | findstr "your_jira_api_token_here" >nul
    if %ERRORLEVEL% equ 0 (
        echo STATUS: Ready for configuration
        echo NEXT STEP: Edit .env file with your actual credentials
    ) else (
        echo STATUS: Ready to run
        echo NEXT STEP: Run 'start_jira_etl.cmd' to start the container
    )
) else (
    echo STATUS: Needs setup
    echo NEXT STEP: Run 'manage_jira_etl.cmd' and choose option 1 for setup
)

echo.
pause

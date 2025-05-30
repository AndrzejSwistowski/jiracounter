@echo off
echo Starting Elasticsearch and Kibana with Docker Compose...

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

REM Create mountdata directory if it doesn't exist
if not exist "mountdata" (
    echo Creating mountdata directory...
    mkdir mountdata
)

REM Start Docker Compose services
echo Building custom Elasticsearch image with Polish plugins...
docker-compose build elasticsearch

if errorlevel 1 (
    echo Error: Failed to build Elasticsearch image
    pause
    exit /b 1
)

echo Starting services...
docker-compose up -d

if errorlevel 1 (
    echo Error: Failed to start Docker services
    pause
    exit /b 1
)

echo.
echo Services started successfully!
echo.
echo Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Wait for Elasticsearch to be ready and initialize
echo Initializing Elasticsearch with Polish support...
python init_elasticsearch.py

if errorlevel 1 (
    echo Warning: Elasticsearch initialization failed or incomplete
)

echo.
echo ========================================
echo Services are now running:
echo ========================================
echo Elasticsearch: http://localhost:9200
echo Kibana:        http://localhost:5601
echo ES Head:       http://localhost:9100
echo.
echo To stop services: docker-compose down
echo To view logs:    docker-compose logs -f
echo ========================================
echo.
pause

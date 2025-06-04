# PowerShell script to test and deploy the cron environment fix
# File: test_cron_fix.ps1

param(
  [switch]$Deploy,
  [switch]$Test,
  [switch]$Debug,
  [string]$ComposeFile = "docker-compose-etl-custom-dns.yml"
)

Write-Host "Cron Environment Fix - Test and Deploy Script" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

function Test-DockerCompose {
  try {
    docker-compose --version | Out-Null
    return $true
  }
  catch {
    Write-Host "❌ Docker Compose not available" -ForegroundColor Red
    return $false
  }
}

function Stop-Container {
  Write-Host "🛑 Stopping existing container..." -ForegroundColor Yellow
  docker-compose -f $ComposeFile down
  if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Container stopped successfully" -ForegroundColor Green
  }
}

function Build-Container {
  Write-Host "🔧 Building container with fixes..." -ForegroundColor Yellow
  docker-compose -f $ComposeFile build
  if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Container built successfully" -ForegroundColor Green
    return $true
  }
  else {
    Write-Host "❌ Container build failed" -ForegroundColor Red
    return $false
  }
}

function Start-Container {
  Write-Host "🚀 Starting container..." -ForegroundColor Yellow
  docker-compose -f $ComposeFile up -d
  if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Container started successfully" -ForegroundColor Green
    return $true
  }
  else {
    Write-Host "❌ Container start failed" -ForegroundColor Red
    return $false
  }
}

function Test-EnvironmentFix {
  Write-Host "🧪 Testing environment variable fix..." -ForegroundColor Yellow
    
  # Wait a moment for container to be ready
  Start-Sleep -Seconds 5
    
  # Check if container is actually running
  $containerStatus = docker-compose -f $ComposeFile ps jira-etl --format json 2>$null
  if ($LASTEXITCODE -ne 0 -or -not $containerStatus) {
    Write-Host "❌ Container is not running or not accessible" -ForegroundColor Red
    Write-Host "💡 Try: docker-compose -f $ComposeFile up -d" -ForegroundColor Yellow
    return $false
  }
    
  # Test 1: Check if .env file was created
  Write-Host "📋 Checking .env file creation..." -ForegroundColor Cyan
  try {
    $envCheck = docker-compose -f $ComposeFile exec -T jira-etl test -f /app/.env 2>$null
    if ($LASTEXITCODE -eq 0) {
      Write-Host "✅ .env file exists" -ForegroundColor Green
            
      # Show .env file contents
      Write-Host "📄 .env file contents:" -ForegroundColor Cyan
      docker-compose -f $ComposeFile exec -T jira-etl cat /app/.env 2>$null
    }
    else {
      Write-Host "❌ .env file not found" -ForegroundColor Red
    }
  }
  catch {
    Write-Host "❌ Error checking .env file: $_" -ForegroundColor Red
  }
    
  # Test 2: Run the test script
  Write-Host "`n🧪 Running environment validation test..." -ForegroundColor Cyan
  try {
    docker-compose -f $ComposeFile exec -T jira-etl python /app/test_cron_env_fix.py
    if ($LASTEXITCODE -eq 0) {
      Write-Host "✅ Environment validation test completed successfully" -ForegroundColor Green
    }
    else {
      Write-Host "❌ Environment validation test failed" -ForegroundColor Red
    }
  }
  catch {
    Write-Host "❌ Error running environment test: $_" -ForegroundColor Red
  }
    
  # Test 3: Test wrapper script manually
  Write-Host "`n🧪 Testing wrapper script manually..." -ForegroundColor Cyan
  try {
    docker-compose -f $ComposeFile exec -T jira-etl /app/docker/run_etl_simple.sh --max-issues 5
    if ($LASTEXITCODE -eq 0) {
      Write-Host "✅ Wrapper script test completed successfully" -ForegroundColor Green
    }
    else {
      Write-Host "❌ Wrapper script test failed" -ForegroundColor Red
    }
  }
  catch {
    Write-Host "❌ Error running wrapper script test: $_" -ForegroundColor Red
  }
}

function Show-Logs {
  Write-Host "📋 Showing container logs..." -ForegroundColor Yellow
  docker-compose -f $ComposeFile logs --tail=50 jira-etl
}

function Debug-Environment {
  Write-Host "🔍 Debug Information" -ForegroundColor Yellow
  Write-Host "===================" -ForegroundColor Yellow
    
  # Check crontab
  Write-Host "`n📅 Crontab configuration:" -ForegroundColor Cyan
  docker-compose -f $ComposeFile exec jira-etl crontab -l
    
  # Check cron process
  Write-Host "`n⚙️  Cron process status:" -ForegroundColor Cyan
  docker-compose -f $ComposeFile exec jira-etl ps aux | grep cron
    
  # Check environment variables
  Write-Host "`n🌍 Environment variables:" -ForegroundColor Cyan
  docker-compose -f $ComposeFile exec jira-etl env | grep -E "ELASTIC|JIRA|DOCKER"
    
  # Check script permissions
  Write-Host "`n🔐 Script permissions:" -ForegroundColor Cyan
  docker-compose -f $ComposeFile exec jira-etl ls -la /app/docker/run_etl*.sh
    
  # Check recent cron logs
  Write-Host "`n📋 Recent cron logs:" -ForegroundColor Cyan
  docker-compose -f $ComposeFile exec jira-etl tail -n 20 /app/logs/cron.log 2>/dev/null || Write-Host "No cron logs yet"
}

# Main execution
if (-not (Test-DockerCompose)) {
  exit 1
}

if ($Deploy) {
  Write-Host "`n🚀 DEPLOY MODE" -ForegroundColor Green
  Write-Host "===============" -ForegroundColor Green
    
  Stop-Container
  if (Build-Container) {
    if (Start-Container) {
      Start-Sleep -Seconds 10
      Test-EnvironmentFix
    }
  }
}
elseif ($Test) {
  Write-Host "`n🧪 TEST MODE" -ForegroundColor Green  
  Write-Host "============" -ForegroundColor Green
    
  Test-EnvironmentFix
}
elseif ($Debug) {
  Write-Host "`n🔍 DEBUG MODE" -ForegroundColor Green
  Write-Host "==============" -ForegroundColor Green
    
  Debug-Environment
  Show-Logs
}
else {
  Write-Host "`nUsage:" -ForegroundColor Yellow
  Write-Host "  .\test_cron_fix.ps1 -Deploy    # Stop, rebuild, start, and test"
  Write-Host "  .\test_cron_fix.ps1 -Test      # Test current running container"
  Write-Host "  .\test_cron_fix.ps1 -Debug     # Show debug information"
  Write-Host "`nOptions:" -ForegroundColor Yellow
  Write-Host "  -ComposeFile <file>             # Specify docker-compose file (default: docker-compose-etl-custom-dns.yml)"
  Write-Host "`nExamples:" -ForegroundColor Yellow
  Write-Host "  .\test_cron_fix.ps1 -Deploy -ComposeFile docker-compose-etl.yml"
  Write-Host "  .\test_cron_fix.ps1 -Test"
  Write-Host "  .\test_cron_fix.ps1 -Debug"
}

Write-Host "`n📋 Next Steps:" -ForegroundColor Cyan
Write-Host "- Monitor logs: docker-compose -f $ComposeFile logs -f jira-etl" -ForegroundColor Gray
Write-Host "- Check cron execution: Wait for the next hour or check /app/logs/cron.log" -ForegroundColor Gray
Write-Host "- Manual test: docker-compose -f $ComposeFile exec jira-etl /app/docker/run_etl_simple.sh --max-issues 10" -ForegroundColor Gray

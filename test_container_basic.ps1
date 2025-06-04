# Simple local test script to verify container connectivity and environment
# File: test_container_basic.ps1

param(
    [string]$ComposeFile = "docker-compose-etl-custom-dns.yml"
)

Write-Host "🔍 Basic Container Connectivity Test" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

function Test-ContainerRunning {
    Write-Host "`n📋 Checking if container is running..." -ForegroundColor Yellow
    
    $containerStatus = docker-compose -f $ComposeFile ps jira-etl --format json | ConvertFrom-Json
    
    if ($containerStatus -and $containerStatus.State -eq "running") {
        Write-Host "✅ Container is running" -ForegroundColor Green
        return $true
    } else {
        Write-Host "❌ Container is not running" -ForegroundColor Red
        Write-Host "   Status: $($containerStatus.State)" -ForegroundColor Gray
        return $false
    }
}

function Test-ContainerHealth {
    Write-Host "`n🏥 Testing container health..." -ForegroundColor Yellow
    
    try {
        # Test basic connectivity
        $result = docker-compose -f $ComposeFile exec -T jira-etl echo "Container is accessible"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Container is accessible" -ForegroundColor Green
        } else {
            Write-Host "❌ Cannot access container" -ForegroundColor Red
            return $false
        }
        
        # Test Python availability
        $pythonTest = docker-compose -f $ComposeFile exec -T jira-etl python --version
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Python is available: $pythonTest" -ForegroundColor Green
        } else {
            Write-Host "❌ Python is not available" -ForegroundColor Red
            return $false
        }
        
        return $true
    }
    catch {
        Write-Host "❌ Error testing container health: $_" -ForegroundColor Red
        return $false
    }
}

function Test-EnvironmentVariables {
    Write-Host "`n🌍 Testing environment variables..." -ForegroundColor Yellow
    
    try {
        # Check critical environment variables
        $envVars = @("DOCKER_ENV", "ELASTIC_URL", "ELASTIC_APIKEY", "JIRA_BASE_URL", "JIRA_API_TOKEN")
        
        foreach ($envVar in $envVars) {
            $value = docker-compose -f $ComposeFile exec -T jira-etl sh -c "echo `$`${envVar}"
            if ($value -and $value.Trim() -ne "") {
                if ($envVar -like "*TOKEN*" -or $envVar -like "*KEY*") {
                    Write-Host "✅ $envVar`: ***SET***" -ForegroundColor Green
                } else {
                    Write-Host "✅ $envVar`: $($value.Trim())" -ForegroundColor Green
                }
            } else {
                Write-Host "❌ $envVar`: NOT SET" -ForegroundColor Red
            }
        }
        
        return $true
    }
    catch {
        Write-Host "❌ Error checking environment variables: $_" -ForegroundColor Red
        return $false
    }
}

function Test-FileAccess {
    Write-Host "`n📁 Testing file access..." -ForegroundColor Yellow
    
    try {
        # Check if .env file exists
        $envFileCheck = docker-compose -f $ComposeFile exec -T jira-etl test -f /app/.env
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ .env file exists" -ForegroundColor Green
        } else {
            Write-Host "⚠️  .env file does not exist" -ForegroundColor Yellow
        }
        
        # Check if wrapper scripts exist and are executable
        $scripts = @("/app/docker/run_etl_simple.sh", "/app/docker/run_etl.sh")
        foreach ($script in $scripts) {
            $scriptCheck = docker-compose -f $ComposeFile exec -T jira-etl test -x $script
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ $script is executable" -ForegroundColor Green
            } else {
                Write-Host "❌ $script is missing or not executable" -ForegroundColor Red
            }
        }
        
        # Check if test script exists
        $testScriptCheck = docker-compose -f $ComposeFile exec -T jira-etl test -f /app/test_cron_env_fix.py
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ test_cron_env_fix.py exists" -ForegroundColor Green
        } else {
            Write-Host "❌ test_cron_env_fix.py is missing" -ForegroundColor Red
        }
        
        return $true
    }
    catch {
        Write-Host "❌ Error checking file access: $_" -ForegroundColor Red
        return $false
    }
}

function Run-EnvironmentTest {
    Write-Host "`n🧪 Running environment test inside container..." -ForegroundColor Yellow
    
    try {
        Write-Host "Executing: docker-compose -f $ComposeFile exec jira-etl python /app/test_cron_env_fix.py" -ForegroundColor Gray
        docker-compose -f $ComposeFile exec jira-etl python /app/test_cron_env_fix.py
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n✅ Environment test completed successfully" -ForegroundColor Green
            return $true
        } else {
            Write-Host "`n❌ Environment test failed with exit code: $LASTEXITCODE" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "`n❌ Error running environment test: $_" -ForegroundColor Red
        return $false
    }
}

function Test-WrapperScript {
    Write-Host "`n🔧 Testing wrapper script..." -ForegroundColor Yellow
    
    try {
        Write-Host "Executing: docker-compose -f $ComposeFile exec jira-etl /app/docker/run_etl_simple.sh --max-issues 2" -ForegroundColor Gray
        docker-compose -f $ComposeFile exec jira-etl /app/docker/run_etl_simple.sh --max-issues 2
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n✅ Wrapper script test completed successfully" -ForegroundColor Green
            return $true
        } else {
            Write-Host "`n❌ Wrapper script test failed with exit code: $LASTEXITCODE" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "`n❌ Error running wrapper script test: $_" -ForegroundColor Red
        return $false
    }
}

# Main execution
Write-Host "Using compose file: $ComposeFile" -ForegroundColor Gray

$allTests = @()

# Run all tests
$allTests += ("Container Running", (Test-ContainerRunning))
$allTests += ("Container Health", (Test-ContainerHealth))
$allTests += ("Environment Variables", (Test-EnvironmentVariables))
$allTests += ("File Access", (Test-FileAccess))
$allTests += ("Environment Test", (Run-EnvironmentTest))
$allTests += ("Wrapper Script", (Test-WrapperScript))

# Summary
Write-Host "`n📊 Test Summary" -ForegroundColor Cyan
Write-Host "===============" -ForegroundColor Cyan

$passCount = 0
$totalCount = $allTests.Count / 2

for ($i = 0; $i -lt $allTests.Count; $i += 2) {
    $testName = $allTests[$i]
    $testResult = $allTests[$i + 1]
    
    if ($testResult) {
        Write-Host "✅ $testName" -ForegroundColor Green
        $passCount++
    } else {
        Write-Host "❌ $testName" -ForegroundColor Red
    }
}

Write-Host "`nResults: $passCount/$totalCount tests passed" -ForegroundColor $(if ($passCount -eq $totalCount) { "Green" } else { "Yellow" })

if ($passCount -eq $totalCount) {
    Write-Host "`n🎉 All tests passed! The cron environment fix is working correctly." -ForegroundColor Green
} else {
    Write-Host "`n⚠️  Some tests failed. Check the output above for details." -ForegroundColor Yellow
    Write-Host "`n🔧 Troubleshooting steps:" -ForegroundColor Cyan
    Write-Host "1. Make sure the container is running: docker-compose -f $ComposeFile up -d" -ForegroundColor Gray
    Write-Host "2. Check container logs: docker-compose -f $ComposeFile logs jira-etl" -ForegroundColor Gray
    Write-Host "3. Rebuild if needed: docker-compose -f $ComposeFile build" -ForegroundColor Gray
}

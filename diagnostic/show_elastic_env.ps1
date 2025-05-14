# PowerShell script to show Elasticsearch environment variables
# File: show_elastic_env.ps1

Write-Host "Checking Elasticsearch environment variables..." -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Cyan

# Check ELASTIC_URL environment variable
$elasticUrl = [Environment]::GetEnvironmentVariable("ELASTIC_URL", "User")
$elasticUrlMachine = [Environment]::GetEnvironmentVariable("ELASTIC_URL", "Machine")

if ($elasticUrl) {
    Write-Host "ELASTIC_URL (User level): $elasticUrl" -ForegroundColor Green
} else {
    Write-Host "ELASTIC_URL (User level): Not set" -ForegroundColor Yellow
}

if ($elasticUrlMachine) {
    Write-Host "ELASTIC_URL (Machine level): $elasticUrlMachine" -ForegroundColor Green
} else {
    Write-Host "ELASTIC_URL (Machine level): Not set" -ForegroundColor Yellow
}

# Check ELASTIC_APIKEY environment variable
$elasticApiKey = [Environment]::GetEnvironmentVariable("ELASTIC_APIKEY", "User")
$elasticApiKeyMachine = [Environment]::GetEnvironmentVariable("ELASTIC_APIKEY", "Machine")

if ($elasticApiKey) {
    # Mask the API key for security
    $maskedKey = $elasticApiKey.Substring(0, 4) + "..." + $elasticApiKey.Substring($elasticApiKey.Length - 4)
    Write-Host "ELASTIC_APIKEY (User level): $maskedKey" -ForegroundColor Green
} else {
    Write-Host "ELASTIC_APIKEY (User level): Not set" -ForegroundColor Yellow
}

if ($elasticApiKeyMachine) {
    # Mask the machine-level API key for security
    $maskedKeyMachine = $elasticApiKeyMachine.Substring(0, 4) + "..." + $elasticApiKeyMachine.Substring($elasticApiKeyMachine.Length - 4)
    Write-Host "ELASTIC_APIKEY (Machine level): $maskedKeyMachine" -ForegroundColor Green
} else {
    Write-Host "ELASTIC_APIKEY (Machine level): Not set" -ForegroundColor Yellow
}

Write-Host "----------------------------------------" -ForegroundColor Cyan
Write-Host "Note: API keys are partially masked for security reasons" -ForegroundColor Cyan
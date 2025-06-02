# PowerShell script to show Elasticsearch and Kibana environment variables
# File: show_elastic_env.ps1

Write-Host "Checking Elasticsearch and Kibana environment variables..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "ELASTICSEARCH CONFIGURATION:" -ForegroundColor Yellow
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

Write-Host ""
Write-Host "KIBANA CONFIGURATION:" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Cyan

# Check KIBANA_URL environment variable
$kibanaUrl = [Environment]::GetEnvironmentVariable("KIBANA_URL", "User")
$kibanaUrlMachine = [Environment]::GetEnvironmentVariable("KIBANA_URL", "Machine")

if ($kibanaUrl) {
    Write-Host "KIBANA_URL (User level): $kibanaUrl" -ForegroundColor Green
} else {
    Write-Host "KIBANA_URL (User level): Not set" -ForegroundColor Yellow
}

if ($kibanaUrlMachine) {
    Write-Host "KIBANA_URL (Machine level): $kibanaUrlMachine" -ForegroundColor Green
} else {
    Write-Host "KIBANA_URL (Machine level): Not set" -ForegroundColor Yellow
}

# Check KIBANA_USERNAME environment variable
$kibanaUsername = [Environment]::GetEnvironmentVariable("KIBANA_USERNAME", "User")
$kibanaUsernameMachine = [Environment]::GetEnvironmentVariable("KIBANA_USERNAME", "Machine")

if ($kibanaUsername) {
    Write-Host "KIBANA_USERNAME (User level): $kibanaUsername" -ForegroundColor Green
} else {
    Write-Host "KIBANA_USERNAME (User level): Not set" -ForegroundColor Yellow
}

if ($kibanaUsernameMachine) {
    Write-Host "KIBANA_USERNAME (Machine level): $kibanaUsernameMachine" -ForegroundColor Green
} else {
    Write-Host "KIBANA_USERNAME (Machine level): Not set" -ForegroundColor Yellow
}

# Check KIBANA_PASSWORD environment variable (masked for security)
$kibanaPassword = [Environment]::GetEnvironmentVariable("KIBANA_PASSWORD", "User")
$kibanaPasswordMachine = [Environment]::GetEnvironmentVariable("KIBANA_PASSWORD", "Machine")

if ($kibanaPassword) {
    Write-Host "KIBANA_PASSWORD (User level): ****" -ForegroundColor Green
} else {
    Write-Host "KIBANA_PASSWORD (User level): Not set" -ForegroundColor Yellow
}

if ($kibanaPasswordMachine) {
    Write-Host "KIBANA_PASSWORD (Machine level): ****" -ForegroundColor Green
} else {
    Write-Host "KIBANA_PASSWORD (Machine level): Not set" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Note: API keys and passwords are masked for security reasons" -ForegroundColor Cyan

# Show current configuration from config.py
Write-Host ""
Write-Host "CURRENT CONFIGURATION FROM CONFIG.PY:" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Cyan
try {
    python -c "import config; print('Elasticsearch:'); es_config = config.get_elasticsearch_config(); print(f'  Host: {es_config[\"host\"]}:{es_config[\"port\"]}'); print(f'  SSL: {es_config[\"use_ssl\"]}'); print(f'  URL: {es_config[\"url\"] or \"Not set\"}'); print('Kibana:'); kb_config = config.get_kibana_config(); print(f'  Host: {kb_config[\"host\"]}:{kb_config[\"port\"]}'); print(f'  SSL: {kb_config[\"use_ssl\"]}'); print(f'  URL: {kb_config[\"url\"] or \"Not set\"}')"
} catch {
    Write-Host "Error reading configuration from config.py" -ForegroundColor Red
}
# Simple PowerShell script to find JSON parsing errors in Elasticsearch
# File: query_json_errors.ps1

# Get connection details from environment - using compatible syntax for older PowerShell versions
$elasticUrl = [Environment]::GetEnvironmentVariable("ELASTIC_URL", "User")
if (-not $elasticUrl) {
    $elasticUrl = [Environment]::GetEnvironmentVariable("ELASTIC_URL", "Machine")
}

$elasticApiKey = [Environment]::GetEnvironmentVariable("ELASTIC_APIKEY", "User")
if (-not $elasticApiKey) {
    $elasticApiKey = [Environment]::GetEnvironmentVariable("ELASTIC_APIKEY", "Machine")
}

# Basic validation
if (-not $elasticUrl) { 
    Write-Host "Error: ELASTIC_URL not set in environment variables" -ForegroundColor Red
    exit 1
}
if (-not $elasticApiKey) { 
    Write-Host "Error: ELASTIC_APIKEY not set in environment variables" -ForegroundColor Red
    exit 1
}

# Clean URL and prepare search
$elasticUrl = $elasticUrl.TrimEnd('/')
$indexPattern = ".ds-filebeat*"  # Search all filebeat indices

# Build a simple query to find JSON errors
$query = @{
    size = 10  # Get the 10 most recent matching errors
    sort = @(@{"@timestamp" = @{order = "desc"}})  # Newest first
    query = @{
        bool = @{
            must = @(
                @{match = @{"error.type" = "json"}}
            )
        }
    }
}

# Execute the search request
Write-Host "Searching for JSON decoding errors..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$elasticUrl/$indexPattern/_search" `
                                 -Method Post `
                                 -Headers @{
                                     "Content-Type" = "application/json"
                                     "Authorization" = "ApiKey $elasticApiKey"
                                 } `
                                 -Body ($query | ConvertTo-Json -Depth 10)

    # Display results
    $count = $response.hits.total.value
    Write-Host "Found $count JSON parsing errors" -ForegroundColor Green
    
    if ($count -gt 0) {
        Write-Host "`nLatest JSON parsing errors:" -ForegroundColor Yellow
        foreach ($hit in $response.hits.hits) {
            $timestamp = $hit._source."@timestamp"
            $errorMsg = $hit._source.error.message
            $logPath = $hit._source.log.file.path
            $message = $hit._source.message
            
            Write-Host "`n-------------------------------------------------" -ForegroundColor Gray
            Write-Host "Time: $timestamp" -ForegroundColor Cyan
            Write-Host "Log: $logPath" -ForegroundColor Cyan
            Write-Host "Error: $errorMsg" -ForegroundColor Red
            Write-Host "Message: $message" -ForegroundColor Yellow
        }
        Write-Host "-------------------------------------------------" -ForegroundColor Gray
    }
} 
catch {
    Write-Host "Error querying Elasticsearch: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $details = $reader.ReadToEnd()
        $reader.Close()
        Write-Host "Response: $details" -ForegroundColor Red
    }
}
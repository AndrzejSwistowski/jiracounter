# PowerShell script to monitor an active Elasticsearch import task
# Usage: .\monitor_es_task.ps1 [LogFilePath]
# If LogFilePath is not provided, will look for the most recent log file

param(
	[string]$LogFilePath = ""
)

# Function to find the most recent log file if not specified
function Get-LatestLogFile {
	$logFolder = Join-Path (Split-Path -Parent $PSScriptRoot) "logs"
	$pattern = "es_populate_task_*.log"
    
	$latestLog = Get-ChildItem -Path $logFolder -Filter $pattern | 
	Sort-Object LastWriteTime -Descending | 
	Select-Object -First 1
    
	if ($latestLog) {
		return $latestLog.FullName
	}
 else {
		throw "No log files found matching pattern $pattern in $logFolder"
	}
}

# Determine which log file to monitor
if ([string]::IsNullOrEmpty($LogFilePath)) {
	try {
		$LogFilePath = Get-LatestLogFile
		Write-Host "Monitoring most recent log file: $LogFilePath" -ForegroundColor Cyan
	}
 catch {
		Write-Host "Error: $_" -ForegroundColor Red
		exit 1
	}
}
else {
	if (-not (Test-Path $LogFilePath)) {
		Write-Host "Error: Log file not found at $LogFilePath" -ForegroundColor Red
		exit 1
	}
}

# Show initial log content
Write-Host "`nInitial log file content:" -ForegroundColor Yellow
Get-Content $LogFilePath | ForEach-Object {
	Write-Host $_ -ForegroundColor Gray
}

# Monitor the file for changes and progress
Write-Host "`nNow monitoring for progress updates..." -ForegroundColor Green
$lastPosition = (Get-Item $LogFilePath).Length

while ($true) {
	Start-Sleep -Seconds 5
    
	# Check if the file still exists
	if (-not (Test-Path $LogFilePath)) {
		Write-Host "Error: Log file no longer exists." -ForegroundColor Red
		break
	}
    
	# Get new content
	$currentSize = (Get-Item $LogFilePath).Length
    
	if ($currentSize -gt $lastPosition) {
		$stream = [System.IO.File]::Open($LogFilePath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
		$reader = New-Object System.IO.StreamReader($stream)
		$null = $reader.BaseStream.Seek($lastPosition, [System.IO.SeekOrigin]::Begin)
        
		$newContent = $reader.ReadToEnd()
		$reader.Close()
		$stream.Close()
        
		# Display new content with highlighting for important info
		$newContent -split "`r`n" | ForEach-Object {
			$line = $_
            
			# Highlight different types of information
			if ($line -match "ERROR|Exception|Failed|Could not connect") {
				Write-Host $line -ForegroundColor Red
			}
			elseif ($line -match "SUCCESS|Successfully|Bulk insert") {
				Write-Host $line -ForegroundColor Green
			}
			elseif ($line -match "WARNING") {
				Write-Host $line -ForegroundColor Yellow
			}
			elseif ($line -match "Start time|End time|ETL process|Execution complete") {
				Write-Host $line -ForegroundColor Cyan
			}
			else {
				Write-Host $line -ForegroundColor Gray
			}
		}
        
		$lastPosition = $currentSize
        
		# Check if process has completed
		if ($newContent -match "Execution complete") {
			Write-Host "`nProcess completed!" -ForegroundColor Green
			break
		}
	}
}

Write-Host "`nMonitoring ended. Full log available at: $LogFilePath" -ForegroundColor Cyan

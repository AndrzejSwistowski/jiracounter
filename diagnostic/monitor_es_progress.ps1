# PowerShell script to monitor Elasticsearch populate task progress
# File: monitor_es_progress.ps1
# Usage: monitor_es_progress.ps1 [TaskId]

param(
	[string]$TaskId = ""
)

$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RootPath = Split-Path -Parent $ScriptPath
$LogPath = Join-Path -Path $RootPath -ChildPath "logs"

# Find the most relevant log file
function Get-LatestLogFile {
	# If TaskId provided, look for that specific log
	if ($TaskId) {
		$pattern = "*$TaskId*.log"
		$logFile = Get-ChildItem -Path $LogPath -Filter $pattern | 
		Sort-Object LastWriteTime -Descending | 
		Select-Object -First 1
        
		if ($logFile) {
			return $logFile.FullName
		}
	}
    
	# Otherwise get the most recent log file
	$logFile = Get-ChildItem -Path $LogPath -Filter "*.log" | 
	Sort-Object LastWriteTime -Descending | 
	Select-Object -First 1
               
	if ($logFile) {
		return $logFile.FullName
	}
    
	return $null
}

# Initialize
$logFile = Get-LatestLogFile
if (-not $logFile) {
	Write-Host "No log files found in $LogPath" -ForegroundColor Red
	exit 1
}

Write-Host "Monitoring log file: $logFile" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Yellow
Write-Host "-------------------------------------" -ForegroundColor Cyan

# Statistics
$totalRecords = 0
$successRecords = 0
$failedRecords = 0
$startTime = Get-Date

# Regular expressions for parsing log lines
$bulkInsertRegex = "Bulk insert: (\d+) succeeded(?:, (\d+) failed)?"
$completedRegex = "ETL process completed. Inserted (\d+) records"

# Monitor the log file
try {
	$lastPosition = 0
    
	while ($true) {
		# Check if file still exists
		if (-not (Test-Path $logFile)) {
			Write-Host "Log file no longer exists. Monitoring stopped." -ForegroundColor Red
			break
		}
        
		# Get file size
		$fileInfo = Get-Item $logFile
		$fileSize = $fileInfo.Length
        
		# If file has new content
		if ($fileSize -gt $lastPosition) {
			$fileStream = New-Object System.IO.FileStream($logFile, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
			$fileReader = New-Object System.IO.StreamReader($fileStream)
            
			# Skip to last position
			$null = $fileReader.BaseStream.Seek($lastPosition, [System.IO.SeekOrigin]::Begin)
            
			# Read new content
			while (-not $fileReader.EndOfStream) {
				$line = $fileReader.ReadLine()
                
				# Parse different types of log lines
				if ($line -match $bulkInsertRegex) {
					$success = [int]$matches[1]
					$failed = if ($matches[2]) { [int]$matches[2] } else { 0 }
                    
					$totalRecords += ($success + $failed)
					$successRecords += $success
					$failedRecords += $failed
                    
					$elapsed = (Get-Date) - $startTime
					$rate = if ($elapsed.TotalSeconds -gt 0) { $totalRecords / $elapsed.TotalSeconds } else { 0 }
                    
					# Display progress
					Write-Host "Records processed: $totalRecords | Success: $successRecords | Failed: $failedRecords | Rate: $([math]::Round($rate, 2))/sec | Elapsed: $($elapsed.ToString('hh\:mm\:ss'))" -ForegroundColor Green
				}
				elseif ($line -match $completedRegex) {
					$finalCount = [int]$matches[1]
					Write-Host "Process completed! Total records inserted: $finalCount" -ForegroundColor Cyan
                    
					# Calculate final statistics
					$elapsed = (Get-Date) - $startTime
					$rate = if ($elapsed.TotalSeconds -gt 0) { $totalRecords / $elapsed.TotalSeconds } else { 0 }
                    
					Write-Host "-------------------------------------" -ForegroundColor Cyan
					Write-Host "Final Statistics:" -ForegroundColor Cyan
					Write-Host "Total records processed: $totalRecords" -ForegroundColor White
					Write-Host "Records successfully inserted: $successRecords" -ForegroundColor Green
					Write-Host "Records failed: $failedRecords" -ForegroundColor Red
					Write-Host "Processing rate: $([math]::Round($rate, 2)) records/second" -ForegroundColor White
					Write-Host "Total time elapsed: $($elapsed.ToString('hh\:mm\:ss'))" -ForegroundColor White
					Write-Host "-------------------------------------" -ForegroundColor Cyan
                    
					# Exit the monitoring loop
					exit 0
				}
				elseif ($line -match "ERROR|Exception|error|fail") {
					# Highlight errors in red
					Write-Host $line -ForegroundColor Red
				}
				elseif ($line -match "WARNING|warning") {
					# Highlight warnings in yellow
					Write-Host $line -ForegroundColor Yellow
				}
				elseif ($line -match "Starting|Populating|Connected|Created|Index|Elasticsearch Summary") {
					# Highlight important status messages in cyan
					Write-Host $line -ForegroundColor Cyan
				}
			}
            
			# Update last position
			$lastPosition = $fileStream.Position
            
			# Close readers
			$fileReader.Close()
			$fileStream.Close()
		}
        
		# Wait before checking again
		Start-Sleep -Seconds 2
	}
}
catch {
	Write-Host "Error monitoring log file: $_" -ForegroundColor Red
}
finally {
	if ($fileReader) { $fileReader.Close() }
	if ($fileStream) { $fileStream.Close() }
}

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$logDirectory = Join-Path $projectRoot "logs"
New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$logFile = Join-Path $logDirectory "refresh_$timestamp.log"

& ".\.venv\Scripts\python.exe" `
    -m app.scripts.refresh_prediction_data `
    2>&1 |
    Tee-Object -FilePath $logFile

if ($LASTEXITCODE -ne 0) {
    throw "Prediction data refresh failed. See $logFile"
}

Write-Output ""
Write-Output "Refresh completed successfully."
Write-Output "Log: $logFile"

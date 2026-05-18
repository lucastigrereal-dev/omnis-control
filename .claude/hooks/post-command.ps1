# OMNIS Post-Command Hook
# Executado após cada comando para logging e verificação

param(
    [string]$Command,
    [int]$ExitCode,
    [string]$WorkingDirectory
)

$logFile = Join-Path $PSScriptRoot "..\state\command-log.jsonl"

$entry = @{
    timestamp = (Get-Date -Format "o")
    command = $Command
    exit_code = $ExitCode
    directory = $WorkingDirectory
} | ConvertTo-Json -Compress

try {
    Add-Content -Path $logFile -Value $entry -ErrorAction SilentlyContinue
} catch {
    # Silent fail — logging never blocks
}

if ($ExitCode -ne 0) {
    Write-Host "Command exited with code $ExitCode" -ForegroundColor Yellow
}

exit 0

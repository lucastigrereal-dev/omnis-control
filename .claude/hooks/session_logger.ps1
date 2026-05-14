# CCOS session_logger.ps1
# Logs session start/stop in markdown

param($event_type, $session_id)

$log_dir = "docs/reports/sessions"
if (-not (Test-Path $log_dir)) {
    New-Item -ItemType Directory -Force -Path $log_dir | Out-Null
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$log_file = Join-Path $log_dir "$(Get-Date -Format 'yyyy-MM-dd')-aba3.md"

$entry = @"

## $event_type — $timestamp
- Session: $session_id
- Branch: $(git branch --show-current 2>$null)
- Commit: $(git log --oneline -1 2>$null)

"@

Add-Content -Path $log_file -Value $entry

# OMNIS CCOS â€” Session Stop Report
$ErrorActionPreference = "Continue"
$logDir = "reports/ccos"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$gitStatus = git status --short 2>$null
$branch = git branch --show-current 2>$null
$report = @"
# CCOS Session Stop Report

- Time: $timestamp
- Branch: $branch

## Git status
```
$gitStatus
```

## Reminder
- Sem push sem autorizaÃ§Ã£o explÃ­cita do Lucas.
- Sem merge sem QA report e suite completa verde.
- dry_run=True como default universal.
"@
$path = "$logDir/session-stop-$((Get-Date).ToString('yyyyMMdd_HHmmss')).md"
Set-Content -Path $path -Value $report -Encoding UTF8
exit 0

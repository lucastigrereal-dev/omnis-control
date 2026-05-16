# OMNIS CCOS â€” PostTool Logger
$ErrorActionPreference = "Continue"
$raw = [Console]::In.ReadToEnd()
$logDir = "reports/ccos"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path "$logDir/post-tool-events.log" -Value "[$timestamp] RAW=$raw"
exit 0

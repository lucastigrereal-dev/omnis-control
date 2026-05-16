# OMNIS CCOS â€” PreTool Guard
# LÃª JSON do Claude Code via STDIN quando disponÃ­vel e bloqueia padrÃµes perigosos.
$ErrorActionPreference = "Stop"

$raw = [Console]::In.ReadToEnd()
$logDir = "reports/ccos"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path "$logDir/pre-tool-events.log" -Value "[$timestamp] RAW=$raw"

$blockedPatterns = @(
  "rm -rf",
  "Remove-Item -Recurse",
  "git reset --hard",
  "git clean -fd",
  "git push --force",
  "docker compose down",
  ".env",
  ".env.",
  "secrets/",
  ".pem",
  ".key",
  "exports/",
  "data/runtime/"
)

foreach ($pattern in $blockedPatterns) {
  if ($raw -match [regex]::Escape($pattern)) {
    Write-Error "OMNIS CCOS BLOCKED: padrÃ£o proibido detectado: $pattern"
    exit 2
  }
}

exit 0

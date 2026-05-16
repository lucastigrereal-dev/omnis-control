param(
  [string[]]$WorktreePaths = @("../omnis-runtime-bridge","../omnis-approval-core","../omnis-capability-forge","../omnis-memory-core","../omnis-akasha-sink")
)

$ErrorActionPreference = "Stop"

foreach ($path in $WorktreePaths) {
  if (Test-Path $path) {
    Write-Host "Sync .claude -> $path"
    New-Item -ItemType Directory -Force -Path "$path/.claude" | Out-Null
    Copy-Item -Path ".claude/*" -Destination "$path/.claude" -Recurse -Force
    if (Test-Path "CLAUDE.md") {
      Copy-Item -Path "CLAUDE.md" -Destination "$path/CLAUDE.md" -Force
    }
  } else {
    Write-Host "Pulado, worktree nÃ£o existe: $path"
  }
}

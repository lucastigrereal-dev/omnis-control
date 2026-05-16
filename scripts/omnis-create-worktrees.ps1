param(
  [switch]$Apply
)

$ErrorActionPreference = "Stop"

$worktrees = @(
  @{ Path="../omnis-runtime-bridge"; Branch="feat/p37-runtime-bridge" },
  @{ Path="../omnis-approval-core"; Branch="feat/p38-approval-core" },
  @{ Path="../omnis-capability-forge"; Branch="feat/p39-capability-forge" },
  @{ Path="../omnis-memory-core"; Branch="feat/p40-memory-core" },
  @{ Path="../omnis-akasha-sink"; Branch="feat/p41-akasha-sink" }
)

Write-Host "OMNIS worktree planner"
if (-not $Apply) {
  Write-Host "PREVIEW: use -Apply para criar."
}

foreach ($wt in $worktrees) {
  Write-Host "git worktree add $($wt.Path) -b $($wt.Branch)"
  if ($Apply) {
    git worktree add $wt.Path -b $wt.Branch
  }
}

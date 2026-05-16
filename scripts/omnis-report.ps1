$ErrorActionPreference = "Continue"
$dir = "reports/ccos"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$branch = git branch --show-current
$status = git status --short
$worktrees = git worktree list
$tests = "NÃ£o executado neste relatÃ³rio. Rode scripts/omnis-safe-test.ps1."

$content = @"
# OMNIS CCOS Report â€” $stamp

## Branch
$branch

## Git status
```
$status
```

## Worktrees
```
$worktrees
```

## Tests
$tests

## Regras lembradas
- Sem push sem autorizaÃ§Ã£o explÃ­cita de Lucas.
- Sem merge sem suite completa verde.
- dry_run=True como default.
- NÃ£o ler secrets.
"@

Set-Content -Path "$dir/CCOS_REPORT_$stamp.md" -Value $content -Encoding UTF8
Write-Host "RelatÃ³rio criado: $dir/CCOS_REPORT_$stamp.md"

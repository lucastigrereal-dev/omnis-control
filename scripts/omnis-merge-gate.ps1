param(
  [Parameter(Mandatory=$true)][string]$Branch,
  [switch]$PreviewOnly
)

$ErrorActionPreference = "Stop"

Write-Host "CCOS Merge Gate para branch: $Branch"

git status --short
python -m pytest tests/ --import-mode=importlib -p no:warnings -q
powershell -ExecutionPolicy Bypass -File scripts/omnis-secret-scan.ps1

Write-Host "Arquivos alterados pela branch:"
git diff --name-only master $Branch

Write-Host "Preview de merge..."
git checkout master
git merge --no-commit --no-ff $Branch
git merge --abort

if ($PreviewOnly) {
  Write-Host "Preview OK. Nenhum merge executado."
  exit 0
}

Write-Host "PARADO: merge real exige autorizaÃ§Ã£o explÃ­cita do Lucas."
Write-Host "Depois da autorizaÃ§Ã£o, execute manualmente:"
Write-Host "git merge --no-ff $Branch -m `"feat: merge $Branch`""
exit 0

# OMNIS Pre-Commit Check Hook
# Executado antes de git commit para validar staged files

$ErrorActionPreference = "Stop"

# Verificar se há arquivos staged
$staged = git diff --cached --name-only 2>$null
if (-not $staged) {
    Write-Host "Nenhum arquivo staged para commit." -ForegroundColor Yellow
    exit 1
}

# Verificar secrets nos arquivos staged
$secretPatterns = @(
    "sk-",
    "api_key",
    "token=",
    "secret=",
    "password="
)

foreach ($file in $staged) {
    if ($file -match "\.env|\.key|\.pem|credentials\.json") {
        Write-Host "BLOCKED: Arquivo sensível detected: $file" -ForegroundColor Red
        exit 1
    }

    if (Test-Path $file) {
        $content = Get-Content $file -Raw -ErrorAction SilentlyContinue
        foreach ($pattern in $secretPatterns) {
            if ($content -match $pattern) {
                # Ignorar placeholders e exemplos
                if ($content -match "example|mock|placeholder|env|fake|test_|EXAMPLE|\$\{") {
                    continue
                }
                Write-Host "WARNING: Possível secret em $file (pattern: $pattern)" -ForegroundColor Yellow
            }
        }
    }
}

# Verificar se git add . foi usado (todos os arquivos modificados staged de uma vez)
$allModified = git diff --name-only 2>$null
$allUntracked = git ls-files --others --exclude-standard 2>$null
$stagedCount = ($staged | Measure-Object).Count
$totalModifiedCount = ($allModified | Measure-Object).Count + ($allUntracked | Measure-Object).Count

if ($stagedCount -gt 5 -and $stagedCount -eq $totalModifiedCount) {
    Write-Host "WARNING: Muitos arquivos staged de uma vez ($stagedCount). Confirme que não foi git add ." -ForegroundColor Yellow
}

Write-Host "Pre-commit check: $stagedCount arquivos staged." -ForegroundColor Green
exit 0

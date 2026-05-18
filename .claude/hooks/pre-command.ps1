# OMNIS Pre-Command Hook
# Executado antes de cada comando para verificar segurança

param(
    [string]$Command,
    [string]$WorkingDirectory
)

$ErrorActionPreference = "Stop"

# Lista de comandos bloqueados
$blockedPatterns = @(
    "git add -A",
    "git add \.",
    "git reset --hard",
    "git clean -fd",
    "rm -rf",
    "Remove-Item -Recurse",
    "docker compose down",
    "docker rm",
    "docker rmi"
)

foreach ($pattern in $blockedPatterns) {
    if ($Command -match [regex]::Escape($pattern)) {
        Write-Host "BLOCKED: Comando proibido detectado: $pattern" -ForegroundColor Red
        Write-Host "Este comando viola as regras de segurança do OMNIS." -ForegroundColor Red
        exit 1
    }
}

# Warning para push sem autorização
if ($Command -match "git push") {
    Write-Host "WARNING: Push detectado. Confirme que Lucas autorizou." -ForegroundColor Yellow
}

exit 0

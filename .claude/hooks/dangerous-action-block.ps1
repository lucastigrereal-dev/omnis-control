# OMNIS Dangerous Action Block Hook
# Bloqueia ações destrutivas irreversíveis

$ErrorActionPreference = "Stop"

$dangerousActions = @(
    @{pattern = "git push --force"; message = "Force push proibido. Destrói histórico remoto."},
    @{pattern = "git reset --hard"; message = "Hard reset proibido. Destrói trabalho local."},
    @{pattern = "git clean -[fdx]"; message = "Git clean proibido. Remove arquivos não trackeados."},
    @{pattern = "Remove-Item.*-Recurse.*node_modules"; message = "Remoção recursiva perigosa."},
    @{pattern = "rm -rf"; message = "rm -rf proibido no OMNIS."},
    @{pattern = "docker compose down -v"; message = "Docker down com -v remove volumes. Proibido."},
    @{pattern = "docker system prune"; message = "Docker prune proibido. Remove recursos do sistema."}
)

# Esta função seria chamada pelo sistema de hooks do Claude Code
function Test-DangerousAction {
    param([string]$Action)

    foreach ($da in $dangerousActions) {
        if ($Action -match $da.pattern) {
            Write-Host "BLOCKED: $($da.message)" -ForegroundColor Red
            return $true
        }
    }
    return $false
}

# Se chamado com argumento, verifica ação específica
if ($args.Count -gt 0) {
    $action = $args -join " "
    if (Test-DangerousAction -Action $action) {
        exit 1
    }
}

exit 0

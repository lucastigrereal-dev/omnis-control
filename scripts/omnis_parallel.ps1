# OMNIS Parallel Worktree Tools
# Uso:
# . .\scripts\omnis_parallel.ps1

function Assert-OmnisRepo {
    if (-not (Test-Path ".git")) {
        throw "Execute este script na raiz do repo omnis-control."
    }
}

function Get-OmnisBaseBranch {
    Assert-OmnisRepo
    $branch = (git branch --show-current).Trim()
    if (-not $branch) {
        throw "Nao consegui detectar branch atual."
    }
    return $branch
}

function Test-OmnisClean {
    Assert-OmnisRepo
    $status = git status --porcelain
    if ($status) {
        Write-Host "Repo com arquivos alterados:" -ForegroundColor Yellow
        git status --short
        throw "Limpe, commite ou stash antes de criar worktrees."
    }
    Write-Host "Repo limpo." -ForegroundColor Green
}

function New-OmnisSafetyTag {
    Assert-OmnisRepo
    $stamp = Get-Date -Format "yyyyMMdd-HHmm"
    $tag = "safe-before-parallel-$stamp"
    git tag $tag
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao criar tag de seguranca."
    }
    Write-Host "Tag criada: $tag" -ForegroundColor Green
}

function Start-ClaudeWorktree {
    param(
        [Parameter(Mandatory=$true)]
        [string]$FrenteName,

        [Parameter(Mandatory=$false)]
        [string]$BaseBranch = ""
    )

    Assert-OmnisRepo

    if (-not $BaseBranch) {
        $BaseBranch = Get-OmnisBaseBranch
    }

    $WorktreePath = "..\omnis-$FrenteName"
    $BranchName = "parallel/$FrenteName"

    if (Test-Path $WorktreePath) {
        throw "Worktree path ja existe: $WorktreePath"
    }

    Write-Host "Criando worktree..." -ForegroundColor Cyan
    Write-Host "Base: $BaseBranch"
    Write-Host "Branch: $BranchName"
    Write-Host "Path: $WorktreePath"

    git worktree add $WorktreePath -b $BranchName $BaseBranch

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "Worktree criada: $WorktreePath" -ForegroundColor Green
        Write-Host "Proximo:" -ForegroundColor Yellow
        Write-Host "cd $WorktreePath"
        Write-Host "claude"
    } else {
        throw "Erro ao criar worktree."
    }
}

function Get-ClaudeWorktrees {
    Assert-OmnisRepo
    git worktree list
    Write-Host ""
    git branch -vv | Select-String "parallel/"
}

function Test-ClaudeFrente {
    param(
        [Parameter(Mandatory=$true)]
        [string]$FrenteName
    )

    $WorktreePath = "..\omnis-$FrenteName"

    if (-not (Test-Path $WorktreePath)) {
        throw "Worktree nao encontrada: $WorktreePath"
    }

    Push-Location $WorktreePath

    Write-Host "Testando frente: $FrenteName" -ForegroundColor Cyan
    git status --short
    python -m pytest tests/ -q

    $code = $LASTEXITCODE
    Pop-Location

    if ($code -ne 0) {
        throw "Testes falharam na frente $FrenteName"
    }

    Write-Host "Testes passaram na frente $FrenteName" -ForegroundColor Green
}

function Commit-ClaudeFrente {
    param(
        [Parameter(Mandatory=$true)]
        [string]$FrenteName,

        [Parameter(Mandatory=$true)]
        [string]$Message
    )

    $WorktreePath = "..\omnis-$FrenteName"

    if (-not (Test-Path $WorktreePath)) {
        throw "Worktree nao encontrada: $WorktreePath"
    }

    Push-Location $WorktreePath

    git status --short
    python -m pytest tests/ -q

    if ($LASTEXITCODE -ne 0) {
        Pop-Location
        throw "Testes falharam. Commit bloqueado."
    }

    git add .
    git commit -m $Message

    if ($LASTEXITCODE -ne 0) {
        Pop-Location
        throw "Falha no commit."
    }

    Pop-Location
    Write-Host "Commit criado na frente $FrenteName" -ForegroundColor Green
}

function Merge-ClaudeFrente {
    param(
        [Parameter(Mandatory=$true)]
        [string]$FrenteName,

        [Parameter(Mandatory=$false)]
        [string]$TargetBranch = ""
    )

    Assert-OmnisRepo

    if (-not $TargetBranch) {
        $TargetBranch = Get-OmnisBaseBranch
    }

    $BranchName = "parallel/$FrenteName"

    Write-Host "Merge da frente $FrenteName em $TargetBranch" -ForegroundColor Cyan

    git checkout $TargetBranch
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao trocar para $TargetBranch"
    }

    git status --short

    git merge --no-ff $BranchName

    if ($LASTEXITCODE -ne 0) {
        throw "Conflito ou erro no merge. Resolver manualmente."
    }

    python -m pytest tests/ -q

    if ($LASTEXITCODE -ne 0) {
        throw "Testes falharam apos merge de $FrenteName."
    }

    Write-Host "Merge OK + testes OK: $FrenteName" -ForegroundColor Green
}

function Stop-ClaudeWorktree {
    param(
        [Parameter(Mandatory=$true)]
        [string]$FrenteName,

        [Parameter(Mandatory=$false)]
        [switch]$DeleteBranch
    )

    Assert-OmnisRepo

    $WorktreePath = "..\omnis-$FrenteName"
    $BranchName = "parallel/$FrenteName"

    git worktree remove $WorktreePath

    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao remover worktree $WorktreePath"
    }

    if ($DeleteBranch) {
        git branch -d $BranchName
    }

    Write-Host "Worktree removida: $WorktreePath" -ForegroundColor Green
}

function New-OmnisParallelWave {
    param(
        [Parameter(Mandatory=$false)]
        [string[]]$Frentes = @(
            "mission-adapter",
            "p11-app-factory-skeleton",
            "p12-automation-skeleton"
        )
    )

    Test-OmnisClean
    New-OmnisSafetyTag

    foreach ($frente in $Frentes) {
        Start-ClaudeWorktree -FrenteName $frente
    }

    Get-ClaudeWorktrees
}

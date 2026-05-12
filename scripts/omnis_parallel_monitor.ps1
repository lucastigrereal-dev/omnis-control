# omnis_parallel_monitor.ps1
# Monitor de esteira paralela OMNIS — carregue com: . .\scripts\omnis_parallel_monitor.ps1

function Assert-OmnisRepo {
    $gitDir = Join-Path (Get-Location) ".git"
    if (-not (Test-Path $gitDir)) {
        throw "Este script deve ser executado a partir da raiz do repositorio omnis-control."
    }
}

function Get-OmnisFrontStatus {
    param(
        [Parameter(Mandatory)]
        [string]$FrontName,
        [string]$Path = "",
        [string]$Branch = ""
    )

    # Resolve path
    if (-not $Path) {
        $Path = "C:\Users\lucas\omnis-$FrontName"
    }

    # Resolve branch
    if (-not $Branch) {
        $Branch = "parallel/$FrontName"
    }

    $exists    = Test-Path $Path
    $lastCommit = ""
    $dirtyCount = 0
    $isClean    = $true

    if ($exists) {
        $logOut = git -C $Path log -1 --oneline 2>$null
        if ($LASTEXITCODE -eq 0 -and $logOut) {
            $lastCommit = $logOut.Trim()
        }
        $statusOut = git -C $Path status --short 2>$null
        if ($statusOut) {
            $lines = @($statusOut | Where-Object { $_ -ne "" })
            $dirtyCount = $lines.Count
            $isClean    = ($dirtyCount -eq 0)
        }
    }

    # has_report: any .md in docs/ that matches the front name
    $hasReport = $false
    $docsPath  = Join-Path (Get-Location) "docs"
    if (Test-Path $docsPath) {
        $mdFiles = Get-ChildItem -Path $docsPath -Recurse -Filter "*.md" -ErrorAction SilentlyContinue |
                   Where-Object { $_.Name -match $FrontName -or $_.DirectoryName -match $FrontName }
        $hasReport = ($null -ne $mdFiles -and @($mdFiles).Count -gt 0)
    }

    $readyForMerge = (
        $exists -and
        $Branch.StartsWith("parallel/") -and
        $isClean -and
        ($lastCommit -ne "")
    )

    $notes = @()
    if (-not $exists)       { $notes += "path nao existe" }
    if (-not $isClean)      { $notes += "$dirtyCount arquivo(s) sujo(s)" }
    if (-not $lastCommit)   { $notes += "sem commit detectado" }
    if (-not $hasReport)    { $notes += "sem relatorio em docs/" }

    [PSCustomObject]@{
        front          = $FrontName
        path           = $Path
        branch         = $Branch
        exists         = $exists
        last_commit    = $lastCommit
        dirty_count    = $dirtyCount
        is_clean       = $isClean
        has_report     = $hasReport
        ready_for_merge = $readyForMerge
        notes          = if ($notes.Count -gt 0) { $notes -join "; " } else { "ok" }
    }
}

function Get-OmnisParallelStatus {
    param(
        [string[]]$Fronts = @()
    )

    Assert-OmnisRepo

    # Discover from git worktree list
    $worktreeLines = git worktree list 2>$null | Select-Object -Skip 1  # skip master
    $discovered    = @()

    foreach ($line in $worktreeLines) {
        if ($line -match "^(\S+)\s+\w+\s+\[parallel/(.+)\]") {
            $discovered += [PSCustomObject]@{
                Path  = $Matches[1]
                Front = $Matches[2]
            }
        }
    }

    # Also scan C:\Users\lucas\omnis-* directories not already found via worktree list
    # Normalize paths to backslash for comparison (git uses forward slashes, FS uses backslashes)
    $omnisBase = "C:\Users\lucas"
    $potentialDirs = Get-ChildItem -Path $omnisBase -Directory -ErrorAction SilentlyContinue |
                     Where-Object { $_.Name -like "omnis-*" -and $_.Name -ne "omnis-control" }

    $discoveredNormalized = $discovered | ForEach-Object { $_.Path -replace "/", "\" }

    foreach ($dir in $potentialDirs) {
        $normalizedFull = $dir.FullName -replace "/", "\"
        if ($discoveredNormalized -notcontains $normalizedFull) {
            $frontName = $dir.Name -replace "^omnis-", ""
            # Only include if it is a git worktree: .git is a FILE, not a directory
            $gitEntry = Join-Path $dir.FullName ".git"
            $isWorktree = (Test-Path $gitEntry) -and (-not (Test-Path $gitEntry -PathType Container))
            if ($isWorktree) {
                $discovered += [PSCustomObject]@{
                    Path  = $dir.FullName
                    Front = $frontName
                }
            }
        }
    }

    # Merge with manually provided Fronts
    foreach ($f in $Fronts) {
        $alreadyFound = $discovered | Where-Object { $_.Front -eq $f }
        if (-not $alreadyFound) {
            $discovered += [PSCustomObject]@{
                Path  = "C:\Users\lucas\omnis-$f"
                Front = $f
            }
        }
    }

    if ($discovered.Count -eq 0) {
        Write-Host "Nenhuma frente paralela detectada." -ForegroundColor Yellow
        return @()
    }

    $results = foreach ($d in $discovered) {
        Get-OmnisFrontStatus -FrontName $d.Front -Path $d.Path
    }

    # Display table
    $results | Format-Table -AutoSize -Property `
        front, branch, exists, last_commit, dirty_count, is_clean, has_report, ready_for_merge, notes

    return $results
}

function Watch-OmnisParallelStatus {
    param(
        [int]$IntervalSeconds = 20,
        [string[]]$Fronts = @()
    )

    Assert-OmnisRepo

    Write-Host "Monitorando esteira paralela OMNIS. Ctrl+C para sair." -ForegroundColor Cyan
    Write-Host "Intervalo: $IntervalSeconds segundos" -ForegroundColor Cyan

    while ($true) {
        Clear-Host
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Write-Host "=== OMNIS Parallel Monitor === $timestamp ===" -ForegroundColor Green
        Write-Host ""
        Get-OmnisParallelStatus -Fronts $Fronts | Out-Null
        Start-Sleep -Seconds $IntervalSeconds
    }
}

function Export-OmnisParallelStatusJson {
    param(
        [string[]]$Fronts = @(),
        [string]$OutputPath = "reports\parallel_status.json"
    )

    Assert-OmnisRepo

    $results = Get-OmnisParallelStatus -Fronts $Fronts

    $reportsDir = Split-Path $OutputPath -Parent
    if ($reportsDir -and -not (Test-Path $reportsDir)) {
        New-Item -ItemType Directory -Force $reportsDir | Out-Null
        Write-Host "Criado diretorio: $reportsDir" -ForegroundColor Yellow
    }

    $payload = [PSCustomObject]@{
        generated_at = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
        fronts       = $results
    }

    $json = $payload | ConvertTo-Json -Depth 5
    Set-Content -Path $OutputPath -Value $json -Encoding UTF8
    Write-Host "Exportado: $OutputPath" -ForegroundColor Green
}

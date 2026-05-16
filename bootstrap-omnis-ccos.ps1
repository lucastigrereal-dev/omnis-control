<# 
.SYNOPSIS
  OMNIS CCOS Bootstrap — Claude Code Operating System para OMNIS Control.

.DESCRIPTION
  Cria uma infraestrutura segura e reutilizável para operar o OMNIS com Claude Code:
  - .claude/settings.json
  - .claude/hooks/*.ps1
  - .claude/skills/*/SKILL.md
  - .claude/agents/*.md
  - scripts/*.ps1
  - docs/CCOS_*.md

  NÃO faz merge.
  NÃO faz push.
  NÃO apaga arquivos.
  NÃO lê .env/secrets.
  NÃO executa ações reais.
  NÃO abre 5 frentes automaticamente.

.PARAMETER Apply
  Sem -Apply, roda em modo preview e só mostra o que faria.
  Com -Apply, escreve os arquivos no projeto.

.PARAMETER Force
  Sobrescreve arquivos existentes, criando backup .bak.<timestamp>.

.PARAMETER CreateWorktrees
  Opcional. Cria worktrees da Wave 7B. Use só depois de rodar bootstrap e revisar.

.PARAMETER RunValidation
  Opcional. Roda validação segura após escrever arquivos.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\bootstrap-omnis-ccos.ps1

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\bootstrap-omnis-ccos.ps1 -Apply

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\bootstrap-omnis-ccos.ps1 -Apply -Force -RunValidation
#>

[CmdletBinding()]
param(
  [switch]$Apply,
  [switch]$Force,
  [switch]$CreateWorktrees,
  [switch]$RunValidation
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Root = (Get-Location).Path

function Write-Tigre {
  param([string]$Message, [string]$Level = "INFO")
  $prefix = switch ($Level) {
    "OK" { "[OK]" }
    "WARN" { "[WARN]" }
    "ERR" { "[ERR]" }
    "ACTION" { "[ACTION]" }
    default { "[INFO]" }
  }
  Write-Host "$prefix $Message"
}

function Assert-ProjectRoot {
  $git = Join-Path $Root ".git"
  if (-not (Test-Path $git)) {
    Write-Tigre "Este diretório não parece ser raiz de repositório Git: $Root" "ERR"
    throw "Execute na raiz do projeto OMNIS."
  }
}

function Ensure-Dir {
  param([string]$Path)
  if ($Apply) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
  }
  Write-Tigre "Diretório: $Path" "ACTION"
}

function Backup-IfExists {
  param([string]$Path)
  if ((Test-Path $Path) -and $Force) {
    $backup = "$Path.bak.$Timestamp"
    Copy-Item -Path $Path -Destination $backup -Force
    Write-Tigre "Backup criado: $backup" "WARN"
  }
}

function Write-TextFile {
  param(
    [string]$Path,
    [string]$Content,
    [switch]$Executable
  )

  $exists = Test-Path $Path
  if ($exists -and (-not $Force)) {
    Write-Tigre "Pulado, já existe: $Path (use -Force para sobrescrever)" "WARN"
    return
  }

  if ($Apply) {
    $parent = Split-Path -Parent $Path
    if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    Backup-IfExists -Path $Path
    Set-Content -Path $Path -Value $Content -Encoding UTF8
  }

  Write-Tigre "Arquivo: $Path" "ACTION"
}

function Test-ForbiddenPath {
  param([string]$Path)
  $normalized = $Path -replace "\\", "/"
  $forbidden = @(
    ".env",
    ".env.",
    "secrets/",
    ".pem",
    ".key",
    "exports/",
    "data/runtime/"
  )
  foreach ($pattern in $forbidden) {
    if ($normalized -like "*$pattern*") {
      return $true
    }
  }
  return $false
}

function Invoke-SafeCommand {
  param([string]$Command)
  $blocked = @(
    "rm -rf",
    "Remove-Item -Recurse",
    "git reset --hard",
    "git clean -fd",
    "docker compose down",
    "git push --force"
  )
  foreach ($b in $blocked) {
    if ($Command -like "*$b*") {
      throw "Comando bloqueado pelo CCOS: $Command"
    }
  }
  Write-Tigre "Comando seguro detectado: $Command" "OK"
}

Assert-ProjectRoot

Write-Tigre "OMNIS CCOS Bootstrap iniciado em: $Root"
if (-not $Apply) {
  Write-Tigre "Modo PREVIEW. Nada será escrito. Use -Apply para implementar." "WARN"
}

# ---------------------------------------------------------------------------
# Conteúdos principais
# ---------------------------------------------------------------------------

$settingsJson = @'
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "env": {
    "OMNIS_CCOS_MODE": "safe",
    "OMNIS_DRY_RUN_DEFAULT": "true",
    "OMNIS_REQUIRE_LUCAS_APPROVAL": "true"
  },
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Bash(git log:*)",
      "Bash(git diff:*)",
      "Bash(git branch:*)",
      "Bash(git worktree list:*)",
      "Bash(python -m pytest tests/*)",
      "Bash(python -m pytest tests/ --import-mode=importlib -p no:warnings -q)",
      "Bash(grep -r:*)",
      "Bash(ls:*)",
      "Bash(find:*)",
      "Bash(cat:*)",
      "Bash(pwd:*)"
    ],
    "deny": [
      "Bash(rm -rf:*)",
      "Bash(git reset --hard:*)",
      "Bash(git clean -fd:*)",
      "Bash(git push --force:*)",
      "Bash(docker compose down:*)",
      "Bash(Remove-Item -Recurse:*)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "powershell -ExecutionPolicy Bypass -File .claude/hooks/pre-tool-guard.ps1"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash|Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "powershell -ExecutionPolicy Bypass -File .claude/hooks/post-tool-log.ps1"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "powershell -ExecutionPolicy Bypass -File .claude/hooks/session-stop-report.ps1"
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "powershell -ExecutionPolicy Bypass -File .claude/hooks/subagent-stop-report.ps1"
          }
        ]
      }
    ]
  }
}
'@

$preToolGuard = @'
# OMNIS CCOS — PreTool Guard
# Lê JSON do Claude Code via STDIN quando disponível e bloqueia padrões perigosos.
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
    Write-Error "OMNIS CCOS BLOCKED: padrão proibido detectado: $pattern"
    exit 2
  }
}

exit 0
'@

$postToolLog = @'
# OMNIS CCOS — PostTool Logger
$ErrorActionPreference = "Continue"
$raw = [Console]::In.ReadToEnd()
$logDir = "reports/ccos"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path "$logDir/post-tool-events.log" -Value "[$timestamp] RAW=$raw"
exit 0
'@

$sessionStop = @'
# OMNIS CCOS — Session Stop Report
$ErrorActionPreference = "Continue"
$logDir = "reports/ccos"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$gitStatus = git status --short 2>$null
$branch = git branch --show-current 2>$null
$report = @"
# CCOS Session Stop Report

- Time: $timestamp
- Branch: $branch

## Git status
```
$gitStatus
```

## Reminder
- Sem push sem autorização explícita do Lucas.
- Sem merge sem QA report e suite completa verde.
- dry_run=True como default universal.
"@
$path = "$logDir/session-stop-$((Get-Date).ToString('yyyyMMdd_HHmmss')).md"
Set-Content -Path $path -Value $report -Encoding UTF8
exit 0
'@

$subagentStop = @'
# OMNIS CCOS — Subagent Stop Report
$ErrorActionPreference = "Continue"
$raw = [Console]::In.ReadToEnd()
$logDir = "reports/ccos"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path "$logDir/subagent-stop-events.log" -Value "[$timestamp] RAW=$raw"
exit 0
'@

$claudeMaster = @'
# CLAUDE.md — OMNIS Control / CCOS

## Identidade
Você é a Control Tower do OMNIS, um sistema operacional agêntico local-first.

KRATOS vê. Aurora interpreta. OMNIS age. Akasha lembra. Lucas decide.

Você coordena, planeja, audita e prepara merges. Você NÃO é um único dev codando tudo em sequência.

## Stack real
- Python 3.12
- pytest
- dataclasses
- zero Pydantic, salvo autorização explícita
- in-memory first
- mock adapters
- file-backed persistence quando necessário
- Git worktrees para paralelização controlada
- PowerShell hooks para guardrails no Windows 11

## Estado base
- Wave 7A completa: P30–P36
- Suite base informada: 5428 passed, 2 skipped, 0 failures
- Wave 7B: P37–P42

## Regras absolutas
- dry_run=True como default universal.
- Nenhuma ação real sem aprovação explícita de Lucas.
- Nunca ler `.env`, `.env.*`, `secrets/`, `*.key`, `*.pem`.
- Nunca escrever em `exports/` ou `data/runtime/`.
- Nunca executar `rm -rf`, `Remove-Item -Recurse`, `git reset --hard`, `git clean -fd`, `docker compose down`.
- Sem push sem autorização explícita.
- Sem merge sem suite completa passando.
- Sem chamadas externas a APIs sem validação mock-first.
- Conflito com CLAUDE.md global: regras de segurança do projeto prevalecem.

## Workflow obrigatório por wave
1. Plan the wave usando skill `wave-plan`.
2. Lock scope usando skill `scope-lock`.
3. Criar worktrees usando skill `spawn-worktrees`, se aplicável.
4. Executar com testes locais por módulo.
5. Gerar handoff report por squad.
6. Rodar conflict scan entre worktrees.
7. Merge sequencial com suite completa entre cada merge.
8. Gerar final report.
9. Push apenas com autorização explícita de Lucas.

## Definição de pronto
Um módulo está DONE quando:
- Testes unitários passando sem warnings relevantes.
- dry_run=True em toda lógica de efeito.
- Nenhum import direto de secret ou env real.
- Handoff report gerado em docs/.
- Conflict scan executado antes do merge.
- Suite completa verde após merge.

## Formato de resposta obrigatório
- Objetivo
- Contexto
- Dependências
- O que roda em paralelo
- Plano de execução
- Riscos
- Checklist de validação
- Pedido de aprovação ou execução
'@

$roadmap7b = @'
# OMNIS — Wave 7B / Sprint 2

## P37 — RuntimeBridge
Criar ponte explícita entre `execution_graph` e `execution_queue`.

## P38 — Approval Core
Unificar `approval_center` e `approval_runtime` em `approval_core`, mantendo backward compatibility.

## P39 — CapabilityForge
Consolidar `capability_forge_lite`, `capability_forge_real` e `capabilityforge` em `capability_forge`.

## P40 — Memory Core
Unificar `memory`, `memory_intel` e `knowledge_context` em camadas claras.

## P41 — Akasha Event Sink
Criar pipeline de eventos persistidos para histórico auditável.

## P42 — Live Cockpit v2
Painel operacional com status vivo dos agentes.

## Ordem recomendada
1. P37 RuntimeBridge
2. P38 Approval Core
3. P39 CapabilityForge
4. P41 Akasha Event Sink
5. P40 Memory Core
6. P42 Live Cockpit v2

## Regra
Se dois épicos tocam os mesmos arquivos, merge sequencial obrigatório.
'@

$mergeFlow = @'
# OMNIS — Merge Flow CCOS

Merge é gate, não atalho.

## Antes do merge
1. Ver branch.
2. Rodar testes do módulo.
3. Rodar suite completa.
4. Rodar scan de secrets/chamadas reais.
5. Confirmar handoff report em docs/.
6. Gerar QA report.
7. Pedir aprovação explícita de Lucas.

## Comandos de QA
```powershell
git log --oneline -5
python -m pytest tests/ --import-mode=importlib -p no:warnings -q
grep -r "secret\|token=\|api_key=\|password=\|OAuthReal\|publish_real\|send_real\|deploy_real" src/ --include="*.py"
git diff --name-only master HEAD
```

## Preview obrigatório
```powershell
git checkout master
git merge --no-commit --no-ff feat/<branch>
git merge --abort
```

## Merge real somente após aprovação
```powershell
git merge --no-ff feat/<branch> -m "feat(P<N>): <descrição>"
python -m pytest tests/ --import-mode=importlib -p no:warnings -q
```

## Se falhar
```powershell
git revert HEAD --no-edit
```

## Nunca fazer
- git push --force
- git reset --hard
- git clean -fd
- merge sem suite verde
- push sem autorização explícita de Lucas
'@

$worktreesScript = @'
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
'@

$safeTestScript = @'
param(
  [string]$Module = ""
)

$ErrorActionPreference = "Stop"

if ($Module -and (Test-Path "tests/$Module")) {
  python -m pytest "tests/$Module" --import-mode=importlib -p no:warnings -v
} else {
  python -m pytest tests/ --import-mode=importlib -p no:warnings -q
}
'@

$secretScanScript = @'
$ErrorActionPreference = "Continue"
$pattern = "secret\|token=\|api_key=\|password=\|OAuthReal\|publish_real\|send_real\|deploy_real"
grep -r $pattern src/ --include="*.py"
'@

$syncClaudeScript = @'
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
    Write-Host "Pulado, worktree não existe: $path"
  }
}
'@

$mergeGateScript = @'
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

Write-Host "PARADO: merge real exige autorização explícita do Lucas."
Write-Host "Depois da autorização, execute manualmente:"
Write-Host "git merge --no-ff $Branch -m `"feat: merge $Branch`""
exit 0
'@

$reportScript = @'
$ErrorActionPreference = "Continue"
$dir = "reports/ccos"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$branch = git branch --show-current
$status = git status --short
$worktrees = git worktree list
$tests = "Não executado neste relatório. Rode scripts/omnis-safe-test.ps1."

$content = @"
# OMNIS CCOS Report — $stamp

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
- Sem push sem autorização explícita de Lucas.
- Sem merge sem suite completa verde.
- dry_run=True como default.
- Não ler secrets.
"@

Set-Content -Path "$dir/CCOS_REPORT_$stamp.md" -Value $content -Encoding UTF8
Write-Host "Relatório criado: $dir/CCOS_REPORT_$stamp.md"
'@

# Skills
function SkillContent {
  param([string]$Name,[string]$Description,[string]$Body)
@"
---
name: $Name
description: $Description
---

# $Name

$Body
"@
}

$skills = @{
"wave-plan" = SkillContent "wave-plan" "Planejar wave do OMNIS antes de qualquer execução." @'
## Objetivo
Transformar roadmap em plano executável, com dependências, riscos e ordem de merge.

## Processo
1. Ler `CLAUDE.md`.
2. Ler roadmap/sprint atual.
3. Identificar módulos tocados.
4. Separar paralelo vs sequencial.
5. Definir gates.
6. Gerar plano em `docs/<WAVE>_PLAN.md`.

## Saída obrigatória
- Objetivo
- Dependências
- Frentes paralelas
- O que NÃO pode paralelizar
- Ordem de merge
- Riscos
- Checklist de validação
'@

"scope-lock" = SkillContent "scope-lock" "Travar escopo de um épico antes de codar." @'
## Objetivo
Impedir expansão caótica de escopo.

## Processo
1. Definir entrada e saída do épico.
2. Listar arquivos/módulos permitidos.
3. Listar arquivos proibidos.
4. Definir testes mínimos.
5. Confirmar handoff report esperado.

## Regra
Não implementar nada fora do escopo sem pedir aprovação.
'@

"spawn-worktrees" = SkillContent "spawn-worktrees" "Criar plano seguro de worktrees paralelas." @'
## Objetivo
Preparar worktrees sem colisão.

## Processo
1. Validar branch atual.
2. Rodar `git status`.
3. Listar worktrees existentes.
4. Criar apenas worktrees aprovados.
5. Sincronizar `.claude/` com `scripts/omnis-sync-claude.ps1`.

## Regra
Não criar worktree para épico dependente antes do gate anterior.
'@

"feature-scaffolder" = SkillContent "feature-scaffolder" "Criar feature nova com scaffold, testes e dry_run." @'
## Objetivo
Criar módulo novo sem efeito real por padrão.

## Processo
1. Criar contrato público.
2. Criar implementação mínima.
3. Criar testes antes de ampliar lógica.
4. dry_run=True como default.
5. Gerar handoff report.

## Proibido
- Chamada externa real.
- Escrita em secrets/export/data runtime.
- Ação destrutiva.
'@

"repo-architect" = SkillContent "repo-architect" "Mapear arquitetura, dependências e contratos." @'
## Objetivo
Entender o repositório antes de mexer.

## Processo
1. Mapear imports.
2. Identificar módulos centrais.
3. Detectar acoplamento.
4. Listar arquivos de alto risco.
5. Propor fronteiras de paralelização.
'@

"refactor-guardian" = SkillContent "refactor-guardian" "Refatorar sem quebrar contratos públicos." @'
## Objetivo
Consolidar código legado mantendo compatibilidade.

## Processo
1. Inventariar APIs públicas.
2. Criar módulo canônico.
3. Adicionar backward compatibility.
4. Migrar testes.
5. Não deletar legado na mesma wave sem aprovação.
'@

"qa-merge-gate" = SkillContent "qa-merge-gate" "Validar branch antes de merge." @'
## Objetivo
Impedir regressão.

## Checklist
1. Teste do módulo.
2. Suite completa.
3. Scan de secrets/chamadas reais.
4. Handoff report existe.
5. Conflict scan.
6. QA report PASS/FAIL.

## Regra
Sem PASS, sem merge.
'@

"docs-release" = SkillContent "docs-release" "Gerar handoff, QA report, changelog e release notes." @'
## Objetivo
Manter rastro operacional.

## Saídas
- `docs/<EPICO>_HANDOFF.md`
- `docs/<EPICO>_QA_REPORT.md`
- changelog curto
- próximos passos
'@
}

# Agents
function AgentContent {
  param([string]$Name,[string]$Tools,[string]$Body)
@"
---
name: $Name
tools: $Tools
---

# $Name

$Body
"@
}

$agents = @{
"agent-architect.md" = AgentContent "agent-architect" "Read, Grep, Glob, Bash" @'
Você é o arquiteto do OMNIS.

Responsabilidades:
- Mapear módulos.
- Definir contratos.
- Separar paralelo vs sequencial.
- Bloquear refactor amplo sem impacto claro.
- Produzir plano em lotes.

Nunca implemente feature grande. Seu papel é clarear o tabuleiro.
'@

"agent-executor.md" = AgentContent "agent-executor" "Read, Grep, Glob, Edit, MultiEdit, Bash" @'
Você executa features de escopo travado.

Regras:
- dry_run=True por padrão.
- Teste antes de concluir.
- Não mexer em arquivos fora do escopo.
- Gerar handoff report.
- Não fazer merge nem push.
'@

"agent-refactor.md" = AgentContent "agent-refactor" "Read, Grep, Glob, Edit, MultiEdit, Bash" @'
Você consolida módulos redundantes.

Regras:
- Inventariar API pública primeiro.
- Manter backward compatibility.
- Não deletar legado sem aprovação.
- Rodar suite completa.
- Documentar impacto.
'@

"agent-qa.md" = AgentContent "agent-qa" "Read, Grep, Glob, Bash, Edit" @'
Você é o guardião de QA e merge.

Responsabilidades:
- Rodar suite completa.
- Rodar scan de secrets/chamadas reais.
- Verificar handoff report.
- Fazer conflict scan.
- Gerar QA report PASS/FAIL.
- Nunca mergear sem autorização explícita de Lucas.
'@

"agent-docs-release.md" = AgentContent "agent-docs-release" "Read, Grep, Glob, Edit, Bash" @'
Você mantém documentação operacional.

Responsabilidades:
- Handoff reports.
- QA reports.
- Changelog.
- Release notes.
- Atualização de docs/WORKTREES_ACTIVE.md.
'@
}

$playbook = @'
# PLAYBOOK — Frentes Paralelas OMNIS CCOS

## Regra maior
Não abrir todas as frentes ao mesmo tempo antes de gates de segurança.

## Ordem segura inicial
1. Agent Architect: P37 RuntimeBridge planning.
2. Agent QA: validação da suite base e merge gate.
3. Depois liberar P38 e P39 em paralelo, se não houver colisão.
4. P41 só depois de P37 estabilizado.
5. P40 depois de P37 + P41.
6. P42 depois de base de eventos/status.

## Frentes
- `../omnis-runtime-bridge` — feat/p37-runtime-bridge
- `../omnis-approval-core` — feat/p38-approval-core
- `../omnis-capability-forge` — feat/p39-capability-forge
- `../omnis-memory-core` — feat/p40-memory-core
- `../omnis-akasha-sink` — feat/p41-akasha-sink

## Prompt coordenador
Leia `CLAUDE.md`, `docs/OMNIS_WAVE_7B.md`, `docs/MERGE_FLOW_CCOS.md` e este playbook.
Atue como `agent-architect`.
Diga quais frentes podem iniciar agora, quais dependências existem e qual a melhor ordem de merge.
Não implemente nada ainda.
'@

# ---------------------------------------------------------------------------
# Estrutura
# ---------------------------------------------------------------------------

$dirs = @(
  ".claude",
  ".claude/hooks",
  ".claude/skills",
  ".claude/agents",
  "scripts",
  "docs",
  "reports/ccos"
)

foreach ($d in $dirs) { Ensure-Dir (Join-Path $Root $d) }

Write-TextFile -Path (Join-Path $Root ".claude/settings.json") -Content $settingsJson
Write-TextFile -Path (Join-Path $Root ".claude/hooks/pre-tool-guard.ps1") -Content $preToolGuard
Write-TextFile -Path (Join-Path $Root ".claude/hooks/post-tool-log.ps1") -Content $postToolLog
Write-TextFile -Path (Join-Path $Root ".claude/hooks/session-stop-report.ps1") -Content $sessionStop
Write-TextFile -Path (Join-Path $Root ".claude/hooks/subagent-stop-report.ps1") -Content $subagentStop

Write-TextFile -Path (Join-Path $Root "CLAUDE.md") -Content $claudeMaster
Write-TextFile -Path (Join-Path $Root "docs/OMNIS_WAVE_7B.md") -Content $roadmap7b
Write-TextFile -Path (Join-Path $Root "docs/MERGE_FLOW_CCOS.md") -Content $mergeFlow
Write-TextFile -Path (Join-Path $Root "docs/PLAYBOOK_FRENTES_CCOS.md") -Content $playbook

Write-TextFile -Path (Join-Path $Root "scripts/omnis-create-worktrees.ps1") -Content $worktreesScript
Write-TextFile -Path (Join-Path $Root "scripts/omnis-safe-test.ps1") -Content $safeTestScript
Write-TextFile -Path (Join-Path $Root "scripts/omnis-secret-scan.ps1") -Content $secretScanScript
Write-TextFile -Path (Join-Path $Root "scripts/omnis-sync-claude.ps1") -Content $syncClaudeScript
Write-TextFile -Path (Join-Path $Root "scripts/omnis-merge-gate.ps1") -Content $mergeGateScript
Write-TextFile -Path (Join-Path $Root "scripts/omnis-report.ps1") -Content $reportScript

foreach ($key in $skills.Keys) {
  $skillDir = Join-Path $Root ".claude/skills/$key"
  Ensure-Dir $skillDir
  Write-TextFile -Path (Join-Path $skillDir "SKILL.md") -Content $skills[$key]
}

foreach ($key in $agents.Keys) {
  Write-TextFile -Path (Join-Path $Root ".claude/agents/$key") -Content $agents[$key]
}

# ---------------------------------------------------------------------------
# Validação opcional
# ---------------------------------------------------------------------------

if ($RunValidation) {
  Write-Tigre "Rodando validação básica..." "ACTION"
  if ($Apply) {
    powershell -ExecutionPolicy Bypass -File (Join-Path $Root "scripts/omnis-report.ps1")
    git status --short
  } else {
    Write-Tigre "Validação real pulada porque Apply não foi usado." "WARN"
  }
}

if ($CreateWorktrees) {
  Write-Tigre "CreateWorktrees solicitado." "WARN"
  if (-not $Apply) {
    Write-Tigre "Modo preview. Nenhum worktree será criado." "WARN"
  }
  powershell -ExecutionPolicy Bypass -File (Join-Path $Root "scripts/omnis-create-worktrees.ps1") -Apply:$Apply
}

Write-Tigre "Bootstrap finalizado." "OK"
if (-not $Apply) {
  Write-Tigre "Para aplicar: powershell -ExecutionPolicy Bypass -File .\bootstrap-omnis-ccos.ps1 -Apply" "WARN"
}
else {
  Write-Tigre "Agora rode: git status --short" "OK"
  Write-Tigre "Depois abra Claude Code e peça: leia CLAUDE.md e docs/PLAYBOOK_FRENTES_CCOS.md; atue como agent-architect; não implemente nada ainda." "OK"
}

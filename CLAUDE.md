# OMNIS Control — Claude Operating Rules

## Identidade
OMNIS é o motor executor e orquestrador operacional.
KRATOS é o cockpit (observa). Aurora interpreta e orienta.
OMNIS executa. KRATOS observa. Aurora interpreta.

## Antes de agir (OBRIGATÓRIO)
Ler:
- docs/project-os/PROJECT_OS.md
- docs/project-os/CURRENT_STATE.md
- docs/project-os/GUARDRAILS.md
- docs/project-os/RUNBOOK.md
- docs/project-os/WAVE_REGISTRY.md
- docs/project-os/ACTIVE_WORKTREES.md

## Proibido
- Tocar KRATOS ou kratos-mission-control
- Executar em C:\Users\lucas (deve ser C:\Users\lucas\omnis-control)
- Push, deploy, ler .env, git add ., git reset --hard, git clean
- Apagar worktrees sem autorização
- Misturar G14 App Factory com CCOS/P37 sem decisão explícita
- Commitar secrets

## Authority Model

### Pode fazer sozinho:
- Preflight, classificar working tree, corrigir erro técnico óbvio
- Rodar testes, build/test suite
- Criar docs de estado, testes
- Implementar próxima wave se WAVE_REGISTRY indicar claramente
- Commit seletivo se gates passarem

### Precisa autorização:
- Push, deploy, secrets, reset/clean
- Remover worktree, mudar roadmap ativo
- Trocar branch principal, resolver conflito semântico grande
- Abandonar Supreme 210 ou CCOS, mesclar roadmaps

### Nunca fazer:
- Mexer no KRATOS
- Executar deploy silencioso
- Ler segredo
- Commitar arquivo incerto
- Recomeçar do zero

## Stack
Python 3.12, pytest, dataclasses, Typer CLI, Rich console
In-memory first, mock adapters, file-backed JSONL persistence
Git worktrees for parallel development

## Standard commands
```sh
# Targeted tests
python -m pytest tests/<module>/ --import-mode=importlib -p no:warnings -v

# Full suite
python -m pytest tests/ --import-mode=importlib -p no:warnings -q

# Project OS scripts
python scripts/omnis_state_check.py
python scripts/omnis_guard_check.py
```

## OMNIS SKILL SYSTEM v1.0

Skills em: .claude/skills/ | Orquestrador: .claude/waves/orchestrator.md

### Waves do Pipeline
- Wave 0: sdd-brainstorm + tree-of-thoughts (Blueprint Analysis)
- Wave 1: sdd-plan + context-engineering (Planning)
- Wave 2: software-architecture + multi-agent-patterns (Architecture)
- Wave 3: do-in-parallel + sdd-implement + subagent-driven-development (Execution)
- Wave 4: write-tests + fix-tests (Testing)
- Wave 5: review-local-changes + do-and-judge + reflect (Review)
- Wave 6: codebase-documenter + git-commit-neolab + git-create-pr (Delivery)

### Como usar
1. Preencha BLUEPRINT.md
2. Execute: claude "execute o blueprint em BLUEPRINT.md"

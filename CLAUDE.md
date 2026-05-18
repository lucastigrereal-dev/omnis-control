# OMNIS SUPREME 210 — Project Context (G14 Ready)

**Phase:** G14 App Factory (W131-W140)
**Prompt mestre:** `PROMPT_MESTRE_OMNIS_SUPREME.md`

## Identity
OMNIS is a local-first agentic operating system for content operations.
It coordinates, plans, audits, executes, and generates Mission Packages.
OMNIS is separate from KRATOS (frontend/cockpit), Aurora (interpreter), Akasha (memory), and HOMINIS (human-assisted actions).

## Operating model
KRATOS sees. Aurora interprets. OMNIS acts. Akasha remembers. Lucas decides.

## Supreme 210 Progress
- 130/210 waves complete (Groups 01-13 DONE)
- Current group: **G14 — App Factory (W131-W140)**
- Next wave: **W131 — app-idea-intake**
- Suite: **6955 passed, 2 skipped**

## G14 App Factory — W131-W140
```
W131 — app-idea-intake: Sistema de entrada de ideias
W132 — app-prd-generator: Gerador de PRD automatizado
W133 — app-db-schema-planner: Planejador de schema de banco
W134 — app-api-contract: Construtor de contrato de API
W135 — app-frontend-plan: Plano de frontend
W136 — app-test-plan: Plano de testes
W137 — app-repo-scaffold: Scaffold de repositório
W138 — app-openhands-mock: Mock do adaptador OpenHands
W139 — app-package-export: Export de pacote de app
W140 — app-factory-e2e: E2E da fábrica de apps
```

Each wave = 10 blocos (B1-B10): model → logic → security → dry-run → CLI → audit → tests → docs → edge-cases → validate.

## Absolute rules
- dry_run=True as universal default — NO exceptions
- No real action without explicit approval
- Never read .env, .env.*, secrets/, *.key, *.pem
- Never write exports/ or data runtime
- Never execute: rm -rf, Remove-Item -Recurse, git reset --hard, git clean -fd, docker compose down
- No push without authorization
- No merge without full test suite
- No external API calls without mock-first validation
- App Factory: never overwrite existing app without explicit approval
- Generated code must pass tests before human review
- If conflict with global CLAUDE.md: project safety rules take precedence

## Standard commands
```sh
# Targeted tests
python -m pytest tests/<module>/ --import-mode=importlib -p no:warnings -v

# Full suite
python -m pytest tests/ --import-mode=importlib -p no:warnings -q

# Import scan
grep -r "secret\|token=\|api_key=\|password=\|OAuthReal\|publish_real\|send_real\|deploy_real" src/ --include="*.py"
```

## Workflow (per wave)
1. Audit pre-wave (git status, suite verde, progress tracking)
2. Execute 10 blocos (B1→B10)
3. Targeted tests after each bloco
4. Wave report in docs/supreme_210/reports/
5. Commit with conventional message
6. Update progress tracking

## Namespaces
- **W** = Supreme 210 wave (W131-W140 current)
- **G** = Macro group (G14 App Factory current)
- **B** = Bloco dentro de wave (B1-B10)
- src/app_factory/ = G14 source modules

## Stack
- Python 3.12, pytest, dataclasses (zero Pydantic except missions)
- In-memory first, mock adapters, file-backed JSONL persistence
- Git worktrees for parallel development
- PowerShell hooks for guardrails (Windows 11)

## OMNIS Project OS

Before any implementation, read:

1. `omnis.project.yaml`
2. `omnis_state.yaml`
3. `omnis_wave_registry.yaml`
4. `omnis_worktrees.yaml`
5. `omnis_blocked_items.yaml`
6. `omnis_guardrails.yaml`
7. `docs/OMNIS_GUARDRAILS.md`
8. `docs/OMNIS_CLAUDE_RUNBOOK.md`
9. `docs/OMNIS_NEXT_ACTIONS.md`

Rules:
- Do not push without human authorization.
- Do not expose or commit secrets.
- Do not use `git add .`.
- Do not duplicate waves.
- Do not edit outside the current branch/worktree scope.
- If P0 exists, resolve/report it before new feature work.

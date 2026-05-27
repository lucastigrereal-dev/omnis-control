# OMNIS Control — Claude Operating Rules

## ⚡ Próximas waves (W23-W26)

**Master das waves W23-W26 (Notion):** https://www.notion.so/36d22eba8f08813daa28e1789aa668b6

Quando `omnis-w22-monetization-mvp` estiver tagueada: iniciar W23 lendo a página acima.
Executar exatamente conforme os 10 blocos com paralelismo marcado.
Tag obrigatória ao fechar: `omnis-w23-saneamento`.

---

## ⚡ Política Oficial de Roteamento de Modelos v2.0 — Ollama-First

**Verdade institucional (Notion):** https://www.notion.so/36d22eba8f0881519268f05675380a8c

SEMPRE consulte esta página antes de alterar `infra/litellm/litellm_config.yaml`, `core/llm/router.py`, ou qualquer chamada de modelo nos agentes.

### Stack oficial:
- `ollama-fast` → glm-5.1:cloud (operação, ~70% das chamadas)
- `ollama-code` → kimi-k2.6:cloud (App Factory, builds)
- `ollama-smart` → deepseek-v4-pro:cloud (raciocínio profundo)
- `ollama-backup` → qwen3.5:cloud (backup open)
- `fallback-cheap` → claude-haiku-4-5 (só fallback)
- `fallback-premium` → claude-sonnet-4-6 (só Aurora premium ou análise crítica)

### Regras invioláveis:
- ❌ NUNCA usar claude-opus*, gpt-4*, gpt-4o*
- ❌ NUNCA chamar Anthropic SDK direto (sempre via LiteLLM @ :4001)
- ✅ SEMPRE usar nomes lógicos (ollama-fast/code/smart, fallback-*)
- ✅ Aurora default = ollama-smart; premium = fallback-premium sob `/aurora premium`

### Budget:
- Ollama Pro: $20/mês (assinatura)
- Anthropic via LiteLLM: $25/mês HARD CAP (alerta em $20)

## Identidade
OMNIS é o motor executor e orquestrador operacional.
KRATOS é o cockpit (observa). Aurora interpreta e orienta.
OMNIS executa. KRATOS observa. Aurora interpreta.

## Estado atual canônico
- Branch atual: `feature/omnis-5waves-runtime-supreme`.
- Wave 0 retomada após queda do Claude Code/Ollama.
- Checkpoint verde confirmado: `8846 passed, 4 skipped`.
- Último commit de código verde: `fix(wave-0): restore green suite after interrupted claude run`.
- Freio obrigatório: NÃO avançar para Wave 1 sem GO explícito do Lucas.

## Antes de agir (OBRIGATÓRIO)
Ler:
- docs/project-os/PROJECT_OS.md
- docs/project-os/CURRENT_STATE.md
- docs/project-os/GUARDRAILS.md
- docs/project-os/RUNBOOK.md
- docs/project-os/WAVE_REGISTRY.md
- docs/project-os/ACTIVE_WORKTREES.md
- docs/project-os/OMNIS_REFINAMENTO_50_DECISOES.md

Referências externas somente leitura:
- C:\Users\lucas\Downloads\OMNIS_BLUEPRINT_CANONICO.md
- C:\Users\lucas\Downloads\OMNIS_ORQUESTRADOR.md
- C:\Users\lucas\Downloads\OMNIS_RUNBOOK_CLAUDE_CODE.md
- C:\Users\lucas\Downloads\OMNIS_RUNBOOK_RETOMADA.md
- C:\Users\lucas\Downloads\Downloads_COMET\REPOS_SKILLS_LEGO.md

## Proibido
- Tocar KRATOS ou kratos-mission-control
- Executar em C:\Users\lucas (deve ser C:\Users\lucas\omnis-control)
- Push, deploy, ler .env, git add ., git reset --hard, git clean
- Apagar worktrees sem autorização
- Misturar G14 App Factory com CCOS/P37 sem decisão explícita
- Commitar secrets
- Rodar `C:\Users\lucas\Downloads\OMNIS_INTEGRATION_MASTER_SCRIPT.md` como script automático.
- Instalar pacotes, subir/reiniciar Docker ou criar gateway novo sem GO explícito.

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
# Git baseline
git status --short

# Targeted tests
python -m pytest tests/<module>/ --import-mode=importlib -p no:warnings -v

# Full suite
python -m pytest tests/ --import-mode=importlib -p no:warnings -q

# Project OS scripts
python scripts/omnis_state_check.py
python scripts/omnis_guard_check.py
```

## Retomada de sessão
Se a sessão cair, primeiro rode:
```sh
git status --short
python -m pytest tests/ --import-mode=importlib -p no:warnings -q
```

Depois continue só se a suite continuar verde ou se a falha estiver concentrada no cluster atual. Não refaça trabalho já commitado.

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
2. Execute waves uma por vez, sempre parando no gate.
3. Para contexto grande, leia os docs canônicos acima como referência, sem mover arquivos de Downloads.

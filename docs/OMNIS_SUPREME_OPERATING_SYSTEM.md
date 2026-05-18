# OMNIS SUPREME Operating System

**Fonte machine-readable:** `omnis.project.yaml`

## O que é o OMNIS

OMNIS é um sistema operacional agentivo local-first para operações de conteúdo.
Ele coordena, planeja, audita, executa e gera Pacotes de Missão.

KRATOS vê. Aurora interpreta. OMNIS age. Akasha lembra. Lucas decide.

## Objetivo Supreme

Transformar o repositório OMNIS em uma fonte de verdade viva para Claude Code,
reduzindo o vai-e-volta humano, evitando duplicação de waves/worktrees,
impedindo commits perigosos e permitindo execução autônoma segura.

## Camadas

```
Intake (ideias, briefings) → Core (models, logic) → Memory (Akasha, state)
→ Domains (Runtime, Health, AppFactory, Maintenance, Templates)
→ Capability Forge (geração de skills/agents)
→ Execution Pipeline (dry-run → validate → execute → store)
→ Tools/Bridges (CLI, HTTP, KRATOS bridge)
→ Outputs (reports, packages, exports)
→ Feedback Loop (metrics, audit, state update)
```

## MVP Operacional vs Supreme Futuro

**MVP (agora):**
- Runtime Missions consolidado (W181-W195)
- Health Bridge /health (G23)
- Maintenance sem P0 (W201-W205)
- Project OS (governança, registries, guardrails)
- AppFactory inicial (W131-W132)

**Supreme (depois):**
- AppFactory completo (W133-W162)
- Templates (W206-W215)
- Capability Forge
- KRATOS collector/UI
- Automações externas

## Princípios

- **Estado explícito > memória humana** — YAMLs são fonte de verdade
- **dry-run > arrependimento** — nunca executar ação real sem simulação
- **Staging seletivo > tragédia** — nunca `git add .`
- **Branch isolada > conflito** — cada domínio em seu worktree
- **Segredo fora do Git > incêndio** — nunca commitar credenciais

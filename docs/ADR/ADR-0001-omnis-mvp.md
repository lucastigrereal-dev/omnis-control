# ADR-0001: Definição do MVP Operacional do OMNIS

**Data:** 2026-05-17
**Status:** Aceito
**Autor:** Lucas Tigre + Claude Code

## Contexto

O projeto OMNIS CONTROL cresceu com múltiplos worktrees paralelos (Runtime, Health, AppFactory, Maintenance, Templates). Sem uma definição clara do que constitui o MVP operacional, há risco de:
- Duplicação de trabalho entre worktrees
- Escopo infinito sem entregas consolidadas
- Dependência excessiva da memória humana do Lucas

## Decisão

O MVP Operacional do OMNIS é definido como o conjunto mínimo de domínios que permitem operação autônoma segura com Claude Code:

**ENTRA no MVP:**
1. Runtime Missions consolidado (W181-W195) — executor, scheduler, result store, events, logs, metrics, export
2. Health Bridge `/health` (G23) — HTTP server com health checks básicos
3. Maintenance sem P0 — auditoria de paths, config, reports, skills
4. Project OS — governança, YAMLs de estado, guardrails, runbooks, prompts
5. AppFactory inicial (W131-W132) — idea intake + PRD generator

**NÃO ENTRA no MVP (futuro):**
- AppFactory Supreme (W133-W162) — schema/API/scaffold avançado
- Templates (W206-W215) — templates de missão e QA final
- Capability Forge — geração automatizada de skills/agents
- KRATOS collector/UI — dashboard e visualização
- Automações externas — OAuth Meta, publishing real

## Consequências

**Positivas:**
- Escopo claro e finito para o MVP
- Redução de duplicação entre worktrees
- Foco em consolidar antes de expandir
- YAMLs machine-readable permitem agentes autônomos

**Negativas:**
- AppFactory Supreme e Templates precisam aguardar
- Funcionalidades avançadas ficam para depois do MVP
- Worktrees existentes para domínios futuros ficam paused/redundant

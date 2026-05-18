# OMNIS Next Actions

**Fonte machine-readable:** `omnis_state.yaml` → `next_safe_actions`
**Atualizado:** 2026-05-18

## P0 — Ação Manual do Lucas

1. **Rotacionar/revogar chave LiteLLM** — valor removido do código. Chave real pode ainda ser válida.

## P1 — Decisão do Lucas

2. **Resolver conflito de namespace Health:**
   - **Branch omnis-health** tem implementação completa: `src/omnis_health/` com doctor, checkers (disk, docker, memory, obsidian, publisher, skills), server 269 linhas, timeout/fallback, CLI start/stop/status. 17 arquivos, ~1988 LOC.
   - **Principal** tem `src/health_bridge/`: minimal, 2 checks, server 82 linhas. 2 arquivos.
   - **Recomendação:** Mergear omnis_health como canônico, arquivar health_bridge.

## P1 — Limpeza

3. **Arquivar worktrees redundantes** (0 commits únicos):
   - `omnis-templates` — mesmo commit `233cdf4` da principal
   - `omnis-runtime` — mesmo commit `233cdf4` da principal

4. **Arquivar worktrees já mergeados/concluídos:**
   - `omnis-maintenance` — mergeado em `6df8db8`
   - `omnis-p20-supreme` — experimento concluído, 0 ahead

## P2 — Manutenção

5. **Resolver arquivos fora do escopo:** `config/paths.yaml`, `docs/ESTADO_ATUAL_RESUMIDO.md`, `docs/disk_audit_report.json`, `reports/`

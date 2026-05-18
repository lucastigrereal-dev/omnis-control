# OMNIS Next Actions

**Fonte machine-readable:** `omnis_state.yaml` → `next_safe_actions`
**Atualizado:** 2026-05-18

## P0 — Ação Manual do Lucas

1. **Rotacionar/revogar chave LiteLLM** — valor removido do código. Chave real pode ainda ser válida.

## P1 — Limpeza Pós-Consolidação

2. **Arquivar health_bridge superseded:**
   - `src/health_bridge/` e `tests/health_bridge/` foram substituídos pelo `omnis_health` canônico
   - Remover ou marcar como superseded

3. **Arquivar worktrees redundantes** (0 commits únicos):
   - `omnis-templates`
   - `omnis-runtime`

4. **Arquivar worktrees já mergeados:**
   - `omnis-maintenance`
   - `omnis-health`

## P2 — Manutenção

5. **Resolver arquivos fora do escopo:** `config/paths.yaml`, `docs/ESTADO_ATUAL_RESUMIDO.md`, `docs/disk_audit_report.json`, `reports/`

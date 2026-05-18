# OMNIS Next Actions

**Fonte machine-readable:** `omnis_state.yaml` → `next_safe_actions`

## P0 — Ação Manual do Lucas

1. **Rotacionar/revogar chave LiteLLM** — o valor foi removido do código em `1b278ad`, mas a chave real pode ainda ser válida. Lucas deve gerar nova chave e invalidar a exposta.

## P1 — Próximo Worktree a Receber Comando

2. **Maintenance (omnis-maintenance)** — W201-W205
   - P0 de código resolvido, risco reduzido de HIGH para MEDIUM
   - Revisar commits, diffs, qualidade
   - Preparar para merge após aprovação

3. **Health (omnis-health)** — W196-W200
   - Comparar com `ed594dd` na principal
   - Se redundante: marcar como REDUNDANT, descartar ou arquivar
   - Se tiver valor adicional: documentar diferença e preparar merge incremental

## P2 — Depois da Consolidação

4. **AppFactory (omnis-appfactory)** — W133-W162
   - Continuar isolado, sem tocar em Runtime/Health
   - Dry-run para scaffold

5. **Templates (omnis-templates)** — W206-W215
   - SÓ depois que Runtime/Health estiver mergeado ou declarado canônico

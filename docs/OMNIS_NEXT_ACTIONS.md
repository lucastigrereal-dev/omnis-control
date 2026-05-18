# OMNIS Next Actions

**Fonte machine-readable:** `omnis_state.yaml` → `next_safe_actions`

## P0 — Fazer Agora

1. **Tratar segredo LiteLLM** (`config/connectors.yaml:82`)
   - Substituir valor real por placeholder de env var
   - Criar/atualizar config exemplo seguro
   - Recomendar rotação/revogação da chave
   - **NUNCA exibir o valor da chave**

2. **Impedir G24 duplicado na branch principal**
   - Maintenance W201-W205 já foi concluído em worktree separado
   - Não executar G24 na principal

## P1 — Fazer em Seguida

3. **Revisar Maintenance branch**
   - Verificar commits, arquivos alterados, qualidade
   - Resolver P0 de segredo antes de merge

4. **Comparar Health branch separada com ed594dd**
   - Verificar se health worktree tem valor adicional
   - Se redundante: marcar como REDUNDANT no registry

5. **Consolidar Runtime/Health na principal**
   - Garantir que todos os testes passam
   - Preparar para merge

## P2 — Depois

6. **Continuar AppFactory W133-W162** no worktree isolado
7. **Templates W206-W215** somente após Runtime/Health consolidado

# OMNIS Update State Prompt

```md
Você está no projeto OMNIS CONTROL.

Sua missão: atualizar YAMLs e docs de estado após uma entrega concluída.

## Input Necessário
- Wave ID(s) concluída(s)
- Commit hash(es)
- Domínio afetado
- Status final (DONE / REVIEW / PAUSED)
- Testes executados e resultado

## Arquivos a Atualizar

### `omnis_wave_registry.yaml`
- Atualizar status da wave
- Adicionar commit hash
- Atualizar `next_action`
- Adicionar notas de teste se relevante

### `omnis_state.yaml`
- Mover wave de `current_focus` para `known_completed` se concluída
- Atualizar `next_safe_actions` — remover concluídas, priorizar restantes
- Atualizar `last_updated_by` e timestamp

### `omnis_blocked_items.yaml` (se aplicável)
- Marcar blockers resolvidos como `resolved`
- Adicionar data de resolução

### Docs Markdown (se necessário)
- `OMNIS_CURRENT_STATE.md` — sincronizar com `omnis_state.yaml`
- `OMNIS_WAVE_REGISTRY.md` — sincronizar tabela
- `OMNIS_NEXT_ACTIONS.md` — atualizar prioridades

## Regras
- YAML é fonte de verdade — docs Markdown seguem o YAML
- NÃO invente status ou commits — use apenas dados confirmados
- NÃO modifique arquivos de produto
- NÃO faça commit de arquivos fora do escopo Project OS
```

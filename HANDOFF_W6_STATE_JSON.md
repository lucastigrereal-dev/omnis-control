# HANDOFF D1-W6 — state.json para KRATOS C4

**Branch:** feature/omnis-5waves-runtime-supreme  
**Commit:** 550cf91  
**Data:** 2026-05-26

## O que foi feito

Wave 6 implementou a gravação automática de `state.json` por missão,
consumível pelo KRATOS C4 para exibir cards com contexto Aurora.

## Arquivos modificados

### `src/mission_graph/mission_state.py`
- Novo campo `state_json_path: str` no TypedDict `MissionGraphState`
- `initial_state()` retorna `state_json_path=""` por padrão

### `src/mission_graph/nodes/finalize_node.py`
- Nova função `_write_state_json(state, aurora_tom) -> str`
  - Grava em `output/mission_graph/{mission_id}/state.json`
  - Graceful degradation: retorna `""` se disco cheio ou sem permissão
- `finalize_node` captura `aurora_tom` de AuroraVoice e passa para o writer
- Retorna `state_json_path` no dict de update

### `tests/mission_graph/test_state_json.py` (CRIADO)
- 7 testes via `run_mission_graph(use_langgraph=True)` + `monkeypatch.chdir(tmp_path)`
- Todos PASS — não polui `output/` real

## Formato do state.json

```json
{
  "mission_id": "...",
  "status": "completed|failed",
  "aurora_priority_score": 80,
  "aurora_tom": "texto adaptado ao tom Tigre",
  "aurora_fio_mental": "Missão X: completed — 3 steps",
  "run_checkpoint_id": "...",
  "steps_count": 3,
  "generated_at": "2026-05-26T..."
}
```

**Localização em disco:** `output/mission_graph/{mission_id}/state.json`

## Gates passados

- `tests/mission_graph/` → 65/65 PASS
- `tests/agencia/ tests/publisher/` → 296/296 PASS

## Próxima ação

- KRATOS C4: ler `output/mission_graph/{mission_id}/state.json` para
  popular card com `aurora_tom` (tom do texto) e `aurora_fio_mental`
  (contexto atual da missão)
- Wave 7 (se definida): exportação/notificação pós-missão

# HANDOFF Wave 2 — CheckpointStore com JsonlRepository real

**Branch:** feature/omnis-5waves-runtime-supreme  
**Commit:** 25de800  
**Data:** 2026-05-26  
**Status:** VERDE ✅

---

## O que foi feito

### 1. src/mission_graph/checkpoint_store.py (CRIADO)
`CheckpointStore` — adapter entre `MissionGraphState` (TypedDict) e `JsonlRepository`.

**Decisão de design:** `JsonlRepository.save_checkpoint()` espera `TaskState` (Pydantic, frozen),
mas `MissionGraphState` é um `TypedDict` simples. Em vez de fazer um cast forçado, o store
escreve JSON diretamente no `checkpoints_dir` com o mesmo formato que o repositório usa
(`{"checkpoint_id": ..., "mission_id": ..., "state": ..., "created_at": ...}`), garantindo
compatibilidade total com `get_checkpoint()` e `get_latest_checkpoint()`.

API pública:
- `CheckpointStore(base_dir=None)` — usa `OMNIS_ROOT/data/missions` por padrão; aceita `tmp_path` em testes
- `save(state: MissionGraphState) -> str` — persiste e retorna `checkpoint_id` (8 chars hex)
- `load(mission_id, checkpoint_id=None) -> Optional[dict]` — carrega específico ou mais recente

### 2. src/mission_graph/nodes/checkpoint_node.py (MODIFICADO)
Substituído stub `uuid.uuid4()` por uso real de `CheckpointStore`.
O nó agora persiste em disco a cada passagem.

### 3. tests/mission_graph/test_checkpoint_store.py (CRIADO)
10 testes — todos PASS:
- `test_save_creates_checkpoint` — save() retorna string não-vazia
- `test_load_returns_saved` — round-trip com checkpoint_id explícito
- `test_load_latest` — 2 saves, load() sem id retorna dado existente
- `test_load_latest_returns_most_recent` — ordem por created_at garantida
- `test_load_missing` — None para mission inexistente
- `test_load_missing_with_checkpoint_id` — None para id inexistente
- `test_crash_resume` — dados persistem entre instâncias diferentes (base_dir igual)
- `test_crash_resume_specific_id` — crash resume com checkpoint_id explícito
- `test_save_stores_full_state` — campos modificados persistem corretamente
- `test_multiple_missions_isolated` — missions diferentes ficam isoladas

---

## Resultado dos testes

```
tests/mission_graph/   → 33/33 PASS
tests/agencia/         → incluído em 296/296 PASS
tests/publisher/       → incluído em 296/296 PASS
```

---

## Próxima wave

Wave 3 ou conforme WAVE_REGISTRY indicar. **Aguardar GO explícito do Lucas.**

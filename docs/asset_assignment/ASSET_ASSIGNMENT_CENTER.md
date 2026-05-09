# Asset Assignment Center

**Modulo:** `src/asset_assignment/`
**Fase:** P1.9
**Status:** Ativo

---

## Responsabilidade

Liga o VideoAsset Registry ao ContentQueue ao CaptionApproval.
Determina se um slot da fila esta PRONTO para gerar pacote offline.

Um slot e considerado pronto quando:
1. Existe na fila (`content_queue.jsonl`)
2. Tem um asset atribuido (campo `asset_id` preenchido)
3. Tem uma caption aprovada (status `approved` no drafts)

---

## Modulos

```
src/asset_assignment/
  __init__.py    — exports: check_assignment_status, add_mock_asset, list_ready_candidates
  models.py      — AssetAssignmentResult (dataclass)
  service.py     — implementacao das 3 funcoes
```

---

## API

### `check_assignment_status(queue_id: str) -> AssetAssignmentResult`

Verifica estado completo de atribuicao para um slot.

```python
from src.asset_assignment import check_assignment_status
result = check_assignment_status("0b79aa1c")
print(result.ready_for_package)  # True / False
print(result.blockers)           # lista de obstaculos
print(result.next_actions)       # lista de comandos sugeridos
```

### `add_mock_asset(name, queue_id=None, format="carousel", account_handle="", registry_path=None) -> dict`

Adiciona asset mock ao registry (para testes sem arquivo real).
Opcionalmente atribui ao slot via `queue_id`.

```python
from src.asset_assignment import add_mock_asset
result = add_mock_asset("foto_natal.jpg", queue_id="0b79aa1c", format="carousel")
print(result["asset_id"])  # mock_<uuid8>
```

### `list_ready_candidates() -> list[dict]`

Lista todos os slots cruzando fila + captions aprovadas.

```python
from src.asset_assignment import list_ready_candidates
candidates = list_ready_candidates()
for c in candidates:
    print(c["queue_id"], c["has_asset"], c["has_caption"], c["ready_for_package"])
```

---

## CLI

```bash
# Verificar status de atribuicao
python jarvis.py assets assignment-status 0b79aa1c

# Adicionar asset mock e atribuir ao slot
python jarvis.py assets add-mock foto_natal.jpg --queue-id 0b79aa1c --format carousel

# Listar candidatos prontos
python jarvis.py assets ready-candidates
```

---

## Pipeline completo (P1.9)

```
assets add-mock foto.jpg --queue-id <id>
  -> registry.add(asset)
  -> queue.assign_asset(queue_id, asset_id)

offline package-carousel <id>
  -> _load_caption() -> caption dict
  -> _load_asset() -> asset dict (nao None!)
  -> status: READY

offline validate <pkg_id>
  -> score: 100/100

offline zip <pkg_id>
  -> exports/offline_factory_zips/<pkg>.zip
```

---

## Modelo AssetAssignmentResult

| Campo | Tipo | Descricao |
|---|---|---|
| `queue_id` | str | ID do slot na fila |
| `asset_id` | Optional[str] | ID do asset atribuido |
| `account_handle` | str | Perfil do slot |
| `caption_id` | Optional[str] | Draft aprovado vinculado |
| `asset_path` | Optional[str] | Caminho/path do asset |
| `asset_type` | str | Formato (carousel, reel, etc) |
| `asset_exists_on_disk` | bool | Arquivo fisico presente |
| `ready_for_package` | bool | Tem asset E caption |
| `blockers` | list[str] | O que falta |
| `next_actions` | list[str] | Comandos sugeridos |

---

## Regras

- Nunca chama Meta API
- Nunca modifica caption ou queue sem permissao explicita
- `add_mock_asset` gera asset com `mock=True` — identificavel
- `_load_asset` e patchavel em testes via `monkeypatch.setattr`

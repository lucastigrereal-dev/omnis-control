# B8C Assign Imported Asset — Relatório de Entrega

**Data:** 2026-05-09 | **Status:** ENTREGUE

## Implementado

| Arquivo | Descricao |
|---|---|
| `src/asset_inbox/assignment.py` | assign_to_queue(), assign_to_mission(), AssetAssignmentResult |
| `src/cli_commands/asset_inbox_cmd.py` | +assign command (--queue / --mission / --force) |
| `tests/asset_inbox/test_assignment.py` | 17 testes (queue + mission + CLI) |

## Arquitetura

### assign_to_queue()
1. Busca ImportedAsset no inbox registry (patchável)
2. Cria VideoAsset entry no video_assets registry (patchável)
3. Chama `Queue.update(queue_id, asset_id=...)` — evita `VIDEO_ASSETS_PATH` hardcoded em `Queue.assign_asset()`
4. Sem duplicar VideoAsset se já registrado

### assign_to_mission()
1. Busca ImportedAsset no inbox registry (patchável)
2. Verifica que mission package dir existe
3. Escreve `04_outputs/asset_reference.json`
4. Atualiza `mission_manifest.json` com `assigned_asset_id` (se existir)

## CLI

```
python jarvis.py asset-inbox assign <asset_id> --queue <queue_id>
python jarvis.py asset-inbox assign <asset_id> --mission <mission_id>
python jarvis.py asset-inbox assign <asset_id> --queue <queue_id> --force
python jarvis.py asset-inbox assign <asset_id> --queue <queue_id> --json
```

## Testes

```
tests/asset_inbox/test_assignment.py: 17 passed
tests/asset_inbox/ total: 104 passed, 1 skipped
```

## Confirmacoes

- [x] Original nunca movido, modificado ou apagado
- [x] VideoAsset criado no registry apontando para stored_path (copia)
- [x] Queue item atualizado com asset_id via update() — sem VIDEO_ASSETS_PATH hardcoded
- [x] asset_reference.json escrito em 04_outputs/
- [x] mission_manifest.json atualizado com assigned_asset_id
- [x] Sem rede, sem OAuth, sem Meta
- [x] Paths patcháveis em todos os testes

## Proximo

B8D — E2E Smoke Mission (full pipeline test)

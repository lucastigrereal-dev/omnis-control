# OMNIS State After P3

**Data:** 2026-05-09 | **Testes:** 1375 pass, 4 skip

## Módulos Ativos

| Módulo | CLI | Armazenamento | Status |
|---|---|---|---|
| `src/mission_builder` | `mission-builder plan/run` | `exports/mission_packages/` | ATIVO |
| `src/mission_report` | `mission-report close/list/show` | `data/mission_reports.jsonl` | ATIVO |
| `src/asset_inbox` | `asset-inbox scan/import/assign/list/show` | `storage/asset_inbox/` + `data/asset_inbox_registry.jsonl` | ATIVO |
| `src/content_queue` | `queue *` | `data/content_queue.jsonl` | ATIVO (pré-P3) |
| `src/video_assets` | `assets *` | `data/video_assets.jsonl` | ATIVO (pré-P3) |
| `src/offline_factory` | `offline-factory *` | `exports/offline_factory/` | ATIVO (pré-P3) |
| `src/caption_approval` | `captions *` | `data/caption_drafts.jsonl` | ATIVO (pré-P3) |
| `src/creative_production` | `creative *` | (em memória) | ATIVO (pré-P3) |

## Storage Gitignored

```
exports/mission_packages/
storage/asset_inbox/
data/asset_inbox_registry.jsonl
```

## OAuth Gate

Congelado. 0/5 Meta contas prontas. Pipeline offline funciona sem OAuth.

## Limitações Conhecidas

- `Queue.assign_asset()` usa `VIDEO_ASSETS_PATH` hardcoded — B8C usa `Queue.update()` diretamente
- `src/offline_factory/packager.py` usa `Queue()` e `Registry()` com default paths — não patchável sem monkeypatch de módulo
- Assign de asset importado para queue cria VideoAsset entry com `source_type=local`

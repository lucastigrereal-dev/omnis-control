# P1.9 — Asset Assignment Center: Report

**Data:** 2026-05-09
**Fase:** P1.9 — Asset Assignment Center
**Status:** CONCLUIDA

---

## Objetivo

Conectar VideoAsset Registry + ContentQueue + CaptionApproval.
Permitir que pacotes offline alcancem status READY com assets reais ou mock.

---

## Entregaveis

### Modulos novos

| Arquivo | Linhas | Descricao |
|---|---|---|
| `src/asset_assignment/__init__.py` | ~10 | exports publicos |
| `src/asset_assignment/models.py` | ~30 | AssetAssignmentResult |
| `src/asset_assignment/service.py` | ~90 | check, add_mock, list_ready |

### CLI novo

| Arquivo | Comando |
|---|---|
| `src/cli_commands/assets_cmd.py` | `assets assignment-status` |
| | `assets add-mock` |
| | `assets ready-candidates` |

### Correcoes

| Arquivo | Bug | Fix |
|---|---|---|
| `src/offline_factory/packager.py` | `AssetRegistry` nao existe | `Registry` |
| `src/offline_factory/packager.py` | `has_asset = False` hardcoded | `_load_asset()` dinamico |
| `tests/offline_factory/test_packager.py` | autouse local nao patchava `_load_asset` | adicionado ao fixture local |

---

## Testes

| Suite | Testes | Resultado |
|---|---|---|
| `tests/offline_factory/` | 117 | PASS |
| `tests/asset_assignment/` | 23 | PASS |
| **TOTAL** | **140** | **PASS** |

---

## Pipeline de smoke (executado em 2026-05-09)

```
assets add-mock natal_reel_01.mp4 --queue-id 0b79aa1c --format carousel
  -> asset_id: mock_80c3b530
  -> atribuido ao slot 0b79aa1c

offline package-carousel 0b79aa1c
  -> status: READY (antes: partial)
  -> 5 arquivos gerados

offline validate <pkg_id>
  -> score: 100/100

offline zip <pkg_id>
  -> ZIP: 3KB
```

---

## Dados locais (auditados)

| Dado | Quantidade |
|---|---|
| Itens na fila | 42 |
| Captions aprovadas | 1 (1d482d82 / 0b79aa1c) |
| Assets no registry | 1 (mock_80c3b530) |
| Pacotes offline gerados | varios (testes + smoke) |

---

## Decisao estrategica mantida

OAuth Meta continua congelado.
Condicao de desbloqueio: 5 pacotes READY validados ou decisao explicita de Lucas.

Ver: `docs/decisions/DECISAO_OAUTH_CONGELADO_FABRICA_PRIMEIRO.md`

# P1.8 — Offline Factory Stabilization Report

**Data:** 2026-05-09
**Branch:** master
**Commits:** 808b8ac (P1.7b) -> (P1.8 commit)
**Testes:** 856 (base P1.7b) + 49 (P1.8) = ~905

---

## O que P1.8 entregou

### Novos comandos CLI

| Comando | Descricao |
|---|---|
| `offline package-post <queue_id>` | Gera pacote de post simples |
| `offline validate <package_id>` | Verifica integridade + score 0-100 |
| `offline zip <package_id>` | Gera ZIP para entrega manual |

### Correos no packager

- `_load_asset()` implementada como funcao patchavel (era hardcode `False`)
- `_load_queue_item()` implementada com `Queue.get()` real (era stub vazio)
- Carousel agora pode chegar em `READY` quando asset presente
- Prioridade de account: caption > queue item > fallback "desconhecido"

### Novos modulos

- `src/offline_factory/validator.py` — validacao de integridade com score 0-100
- `src/offline_factory/zipper.py` — export ZIP com stdlib zipfile

### Novos testes

- `tests/offline_factory/conftest.py` — FAKE_CAPTION, FAKE_ASSET, autouse fixtures
- `tests/offline_factory/test_post_package.py` — 14 testes
- `tests/offline_factory/test_validate.py` — 13 testes
- `tests/offline_factory/test_zip.py` — 9 testes
- `tests/offline_factory/test_smoke_regression.py` — 13 testes

### Documentacao

- `docs/decisions/DECISAO_OAUTH_CONGELADO_FABRICA_PRIMEIRO.md` — decisao estrategica permanente
- `docs/offline_factory/OFFLINE_DELIVERABLES_CATALOG.md` — catalogo de entregaveis
- `docs/offline_factory/MANUAL_PUBLISHING_RUNBOOK.md` — runbook operacional
- `docs/offline_factory/P1_8_GO_NO_GO.md` — go/no-go da fase

---

## Testes

```
tests/offline_factory/: 117/117 PASS
```

---

## Auditoria de dados locais

```powershell
python jarvis.py offline list
```

Resultado esperado: ver pacotes existentes de testes anteriores (P1.7 smoke).
Os testes nao dependem de dados reais — usam fixtures inline.

---

## Estado dos entregaveis por status possivel

| Tipo | blocked | partial | ready |
|---|---|---|---|
| Carousel | sem caption | caption sem asset | caption + asset |
| Reels | sem caption | n/a | caption presente |
| Post | sem caption | caption sem asset | caption + asset |

---

## Proxima fase

**P1.9 — Asset Assignment Center**

Implementar: atribuir video/imagem a um slot da fila via CLI.
Quando asset for atribuido, `_load_asset()` passa a retornar dado real.
Pacotes de carousel e post elevam de `partial` para `ready` automaticamente.

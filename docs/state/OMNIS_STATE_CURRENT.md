# OMNIS State — Atual (P1.8)

**Data:** 2026-05-09
**Branch:** master
**Fase concluida:** P1.8 — Offline Factory Stabilization
**Testes:** ~905 (base P1.7b + 49 novos P1.8)

---

## Decisao estrategica

**OAuth Meta congelado. Fabrica offline e prioridade.**

Ver: `docs/decisions/DECISAO_OAUTH_CONGELADO_FABRICA_PRIMEIRO.md`

---

## Entregaveis offline funcionais

| Tipo | Comando | Status possivel |
|---|---|---|
| Carrossel | `offline package-carousel` | blocked / partial / ready |
| Reels Script | `offline package-reels` | blocked / ready |
| Post Simples | `offline package-post` | blocked / partial / ready |
| Validacao | `offline validate` | score 0-100 |
| ZIP Export | `offline zip` | ok |

---

## Modulos core offline

```
src/offline_factory/
  models.py      — DeliveryPackage, PackageType, PackageStatus
  manifest.py    — generate_manifest(), read_manifest()
  packager.py    — create_*_package(), _load_asset(), _load_queue_item(), list_packages()
  validator.py   — validate_package(), validate_by_id(), ValidationResult
  zipper.py      — zip_package(), ZipResult
  errors.py      — OfflineFactoryError e subclasses
  __init__.py    — exports publicos
```

---

## Dados locais (2026-05-09)

- **Fila:** 42 itens
- **Drafts:** 42 legendas
- **Aprovadas:** 1 (1d482d82 / queue 0b79aa1c / @lucastigrereal)
- **Pacotes gerados:** 4 (testes smoke anteriores)

---

## Testes

```
tests/offline_factory/: 117/117 PASS
```

---

## Bloqueios ativos

- **OAuth Meta** — congelado por decisao estrategica
- **Asset slot** — `_load_asset()` retorna None para todos os slots (sem P1.9 ainda)
- **Post real** — bloqueado ate OAuth + revisao humana

---

## Proximas fases

| Fase | Descricao | Prioridade |
|---|---|---|
| P1.9 | Asset Assignment Center | Alta |
| P2.0 | Render Engine HTML/PNG | Media |
| P2.1 | Video Edit Plan + FFmpeg | Media |
| P2.2 | Campaign Package 10 Posts | Media |
| P1.6 | Manual OAuth Gate | CONGELADO |

---

## Roadmap offline completo

```text
P1.8 DONE -> P1.9 (asset) -> P2.0 (render) -> P2.1 (video plan)
          -> P2.2 (campaign) -> P2.3 (tracker) -> P2.4 (zip delivery)
          -> P2.5 (quality score)
          -> P1.6 (OAuth) — so quando fabrica estiver madura
```

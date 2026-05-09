# OMNIS State — Atual (P4.0 iniciando)

**Data:** 2026-05-09
**Branch:** master
**Fase concluida:** P3 Final Seal — 48be445
**Testes:** 1375 passed, 4 skipped

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

## Asset Assignment Center (P1.9)

| Comando | Descricao |
|---|---|
| `assets assignment-status <id>` | Verifica se slot tem asset + caption |
| `assets add-mock <nome> --queue-id <id>` | Adiciona asset mock ao registry |
| `assets ready-candidates` | Lista slots prontos para empacotar |

---

## Modulos core offline

```
src/offline_factory/
  models.py      — DeliveryPackage, PackageType, PackageStatus
  manifest.py    — generate_manifest(), read_manifest()
  packager.py    — create_*_package(), _load_asset(), _load_queue_item(), list_packages()
  validator.py   — validate_package(), validate_by_id(), ValidationResult
  zipper.py      — zip_package(), ZipResult

src/asset_assignment/
  models.py      — AssetAssignmentResult
  service.py     — check_assignment_status(), add_mock_asset(), list_ready_candidates()
```

---

## Dados locais (2026-05-09)

- **Fila:** 42 itens
- **Captions aprovadas:** 1 (1d482d82 / queue 0b79aa1c / @lucastigrereal)
- **Assets no registry:** 1 (mock_80c3b530 — mock, atribuido a 0b79aa1c)
- **Status do slot 0b79aa1c:** READY para empacotar

---

## Testes

```
tests/offline_factory/: 117/117 PASS
tests/asset_assignment/:  23/23  PASS
TOTAL:                   140/140 PASS
```

---

## Bloqueios ativos

- **OAuth Meta** — congelado por decisao estrategica
- **Post real** — bloqueado ate OAuth + revisao humana

---

## Proximas fases

| Fase | Descricao | Prioridade |
|---|---|---|
| P2.0 | Render Engine HTML/PNG | Media |
| P2.1 | Video Edit Plan + FFmpeg | Media |
| P2.2 | Campaign Package 10 Posts | Media |
| P1.6 | Manual OAuth Gate | CONGELADO |

---

## Roadmap offline completo

```text
P1.8 DONE -> P1.9 DONE -> P2.0 (render) -> P2.1 (video plan)
          -> P2.2 (campaign) -> P2.3 (tracker) -> P2.4 (zip delivery)
          -> P2.5 (quality score)
          -> P1.6 (OAuth) — so quando fabrica estiver madura
```

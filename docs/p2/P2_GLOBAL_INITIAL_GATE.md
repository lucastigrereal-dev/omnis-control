# P2.0-P2.4 — Global Initial Gate

**Data:** 2026-05-09
**Branch:** master
**Commit:** 0432a36

---

## Estado do repo

- Arquivos sujos conhecidos (nao comitar):
  - `config/paths.yaml` — runtime
  - `docs/ESTADO_ATUAL_RESUMIDO.md` — runtime
  - `docs/disk_audit_report.json` — runtime

## Testes baseline

```
tests/offline_factory/: 117/117 PASS
tests/asset_assignment/:  23/23  PASS
TOTAL:                   140/140 PASS
```

## CLIs funcionais

```
python jarvis.py offline --help   -> OK
python jarvis.py assets --help    -> OK
```

## OAuth

**CONGELADO** por decisao estrategica.
Ver: `docs/decisions/DECISAO_OAUTH_CONGELADO_FABRICA_PRIMEIRO.md`

## Pipeline offline validado (P1.9)

```
assets add-mock -> assign -> offline package-carousel -> READY -> validate 100/100 -> ZIP
```

## Slot canario

- queue_id: 0b79aa1c
- caption_id: 1d482d82 (aprovada)
- asset_id: mock_80c3b530 (mock carousel)
- status: READY

## Roadmap P2

| Fase | Descricao | Status |
|---|---|---|
| P2.0 | Render Engine HTML Preview | pendente |
| P2.1 | Visual Quality Layer | pendente |
| P2.2 | Campaign Package 10 Posts | pendente |
| P2.3 | Manual Publishing Tracker | pendente |
| P2.4 | Client Delivery ZIP | pendente |

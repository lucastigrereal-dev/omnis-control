# P1.5 — Initial Gate

**Data:** 2026-05-08

---

## Repo States at Entry

### OMNIS Control

| Campo | Valor |
|---|---|
| Branch | master |
| Commit | 0384548 |
| Dirty files | 3 (paths.yaml, ESTADO_ATUAL, disk_audit) |
| Tests | 723 passed, 2 skipped |

### Publisher OS

| Campo | Valor |
|---|---|
| Branch | `argos-evolucao-passo-0` |
| Commit | ff098ee |
| Dirty files | 6 modified, 7 untracked |
| Has oauth_setup.py | Yes (untracked) |

## OAuth Status at Entry

- Probe: 2 present, 2 empty, 3 missing
- Readiness: `human_required` + `blocked` (callback 404)
- Callback: HTTP 404 — NÃO existe
- Post candidate: 0b79aa1c / ready: false

## GO/NO-GO at Entry

- OAuth: **NO-GO** (secret empty + callback 404)
- Post: **NO-GO** (OAuth + no asset)

## P1.5 Goals

1. Fix callback 404 — create stub route
2. Align config docs
3. Asset gate for first post
4. Still NO OAuth real, NO post real

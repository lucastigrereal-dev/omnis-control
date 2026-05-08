# OMNIS State After P1.4

**Data:** 2026-05-08 | **Commit:** 0384548 | **Branch:** master

---

## P1.4 Deliverables

| Item | Status |
|---|---|
| env_probe.py | Criado — safe .env reader |
| test_env_probe.py | 24 tests |
| test_no_secrets_leaked.py | 7 tests |
| oauth probe CLI | Funcional |
| oauth validate CLI | Funcional |
| OAuth readiness checks | 15 checks (8 infra + 7 env vars) |
| GO/NO-GO doc | Criado |
| Env probe report | 2 present, 2 empty, 3 missing |
| Checklist Lucas | Criado |
| Post package contract | Criado |
| First post candidate | 0b79aa1c documentado |

## Test Suite

- **723 passed**, 2 skipped, 1 pre-existing (disk_audit)
- OAuth readiness: 59/59
- First post: 25/25

## Blockers at P1.4 exit

| Blocker | Status |
|---|---|
| META_APP_SECRET | empty |
| META_GRAPH_VERSION | missing |
| INSTAGRAM_BUSINESS_ACCOUNT_ID | empty (alias INSTAGRAM_BUSINESS_ID) |
| FACEBOOK_PAGE_ID | missing |
| META_ACCESS_TOKEN | missing |
| Callback route | HTTP 404 |
| Post asset | Not assigned |

## Next: P1.5

Fix callback 404 before attempting OAuth. Align config. Asset gate.

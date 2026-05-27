# HANDOFF W14 — Ampliar API FastAPI

**Branch:** feature/omnis-w11-w20
**Commit:** e035b99
**Data:** 2026-05-27
**Status:** COMPLETO ✅

## O que foi feito

### Novos routers criados

| Arquivo | Prefixo | Endpoints |
|---|---|---|
| `src/api/routers/marketing.py` | `/marketing` | GET /sprint, POST /missions, GET /agents |
| `src/api/routers/aurora.py` | `/aurora` | POST /chat (stub), GET /state |
| `src/api/routers/cost.py` | `/cost` | GET /summary |
| `src/api/routers/events.py` | `/events` | GET (SSE heartbeat) |

### Modificações em src/api/main.py
- Importa e registra os 4 novos routers
- CORS `allow_methods` atualizado: `["GET", "POST", "PATCH"]`
- Versão bumped: `1.0.0 → 1.1.0`

### Testes
- Criado `tests/api/test_new_routers.py` com 7 testes (marketing x3, aurora x3, cost x1)
- **68/68 PASS** em `tests/api/`
- **108/108 PASS** em `tests/sectors/` + `tests/mission_graph/`

## Notas de implementação

- `POST /marketing/missions` injeta `type="content_production"` como default (campo obrigatório em `MarketingMissionInput`)
- `GET /aurora/state` lê o `state.json` mais recente de `output/mission_graph/*/` — retorna `{"status": "no_state"}` se diretório não existir
- `GET /cost/summary` usa `CostTracker.generate_report()` como staticmethod — instância não é necessária
- SSE em `GET /events` envia heartbeat a cada 30s, fecha ao detectar client disconnect

## Próxima wave sugerida

W15 — Sectors/Events router ou autenticação da API (JWT stub para KRATOS).

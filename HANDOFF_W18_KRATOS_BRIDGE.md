# HANDOFF W18 — KRATOS Bridge (OMNIS side)
Data: 2026-05-27

## Status: ✅ W18-B1 + W18-B2 completos

---

## W18-B1 — Auth API Key

**Arquivo:** `src/api/auth.py`

### Comportamento
- **Dev mode** (sem `OMNIS_API_KEY` no ambiente): todas as requisições são aceitas.
- **Prod mode** (`OMNIS_API_KEY` setado): requer um dos headers:
  - `X-API-Key: <chave>`
  - `Authorization: Bearer <chave>`
  - Retorna `HTTP 403` se ausente ou incorreto.

### Uso nos endpoints
```python
from fastapi import Depends
from src.api.auth import require_api_key

@router.get("/endpoint", dependencies=[Depends(require_api_key)])
def endpoint(): ...
```

### Endpoints protegidos (W18)
- `GET /events` — SSE principal
- `GET /events/status` — status do bus

### KRATOS precisa fazer
Para conectar em prod, enviar no request HTTP:
```http
X-API-Key: <valor de OMNIS_API_KEY>
```

---

## W18-B2 — SSE EventBus

**Arquivos:**
- `src/api/event_bus.py` — singleton `EventBus` + helpers de publicação
- `src/api/routers/events.py` — SSE endpoint integrado ao bus

### Endpoint SSE
```
GET /events
```

Resposta: `text/event-stream` (protocolo SSE padrão).

### Formato de evento
```
event: mission_started
data: {"type":"mission_started","data":{"mission_id":"m1","brief":{}},"ts":1748300000.0}

event: heartbeat
data: {"type":"heartbeat","data":{"ts":1748300000.0},"ts":1748300000.0}
```

### Eventos disponíveis

| Evento | Quando dispara | Campos em `data` |
|--------|---------------|-----------------|
| `connected` | Ao conectar ao SSE | `ts` |
| `heartbeat` | A cada 30s | `ts` |
| `mission_started` | Início de run do grafo | `mission_id`, `brief` |
| `mission_completed` | Finalização bem-sucedida | `mission_id`, `cost_usd` |
| `mission_failed` | Erro no grafo | `mission_id`, `error` |
| `cost_updated` | Atualização de custo | `mission_id`, `cost_usd`, `token_count` |
| `agent_result` | Agente de marketing concluiu | `mission_id`, `agent`, `squad`, `success` |

### Como publicar de dentro do OMNIS
```python
from src.api.event_bus import publish_mission_started, get_event_bus

# Async (dentro de node do grafo async):
await publish_mission_started(mission_id, brief)

# Sync (código síncrono):
bus = get_event_bus()
bus.publish_sync("custo_atualizado", {"mission_id": "m1"})
```

### Status endpoint
```
GET /events/status
→ {"subscribers": 2, "status": "ok", "ts": 1748300000.0}
```

---

## W18-B3 — E2E com KRATOS
**Status: ⏸ SKIP — reservado para sessão separada.**

KRATOS precisa conectar via SSE e consumir os eventos acima.
Aguardar KRATOS Onda 3 para integração completa.

---

## API version: 1.2.0

---

## Testes
- `tests/api/test_w18_auth_eventbus.py` — **23/23 PASS**
- Cobertura: dev mode, prod mode, X-API-Key, Bearer, 403, EventBus pub/sub,
  multiple subscribers, shutdown, singleton, helpers de publicação.

---

## Variáveis de ambiente

| Var | Padrão | Descrição |
|-----|--------|-----------|
| `OMNIS_API_KEY` | não setado | Se setado, activa autenticação prod |

---

## O que falta (fora do escopo W18)
- Integrar `publish_*` helpers nos nodes do mission_graph (W19/W20)
- KRATOS consumir SSE (KRATOS Onda 3)
- Rate limiting / IP allowlist (futuro)

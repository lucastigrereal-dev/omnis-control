# OMNIS ↔ KRATOS Contract v1

Status: draft-final (ready to implement)  
Version: `v1`  
Date: `2026-05-27`  
Owners: OMNIS + KRATOS

## 1) Scope

This contract defines exactly three integration surfaces:

1. Mission routes
2. SSE endpoint + event names
3. Authentication header

No other implicit contract is allowed.

## 2) Base URL and Versioning

- Base URL: `http://<omnis-host>:<port>`
- Version prefix: `/v1`
- All KRATOS reads from versioned routes only.

## 3) Authentication (v1)

Canonical header (required in production):

- `X-KRATOS-KEY: <token>`

Temporary compatibility window (for migration only):

- Accept `X-API-Key` and `Authorization: Bearer <token>` as aliases.
- Sunset aliases after migration freeze.

Error contract:

- `401` when missing key (prod mode)
- `403` when invalid key

## 4) Mission Routes (v1)

### 4.1 List missions

`GET /v1/missions?status=<optional>&limit=<1..200>`

Response:

```json
{
  "data": [
    {
      "mission_id": "mis_123",
      "title": "Parallel Fabric P2",
      "sector": "produto-tecnologia",
      "status": "running",
      "current_step": "wave-status-skill",
      "retry_count": 1,
      "max_retries": 3,
      "checkpoint_id": "chk_001",
      "checkpoint_label": "after_router",
      "checkpoint_at": "2026-05-27T17:00:00Z",
      "cumulative_cost_usd": 0.0042,
      "last_event_type": "mission:update",
      "last_event_at": "2026-05-27T17:05:00Z",
      "event_count": 22,
      "error_count": 0,
      "budget_exceeded": false,
      "approval_pending": false,
      "approval_reason": null
    }
  ],
  "total": 1,
  "source": "live",
  "updated_at": "2026-05-27T17:05:00Z"
}
```

### 4.2 Mission detail

`GET /v1/missions/{mission_id}`

Response:

```json
{
  "data": {
    "mission_id": "mis_123",
    "contract": {},
    "summary": {},
    "updated_at": "2026-05-27T17:05:00Z"
  }
}
```

### 4.3 Mission event log

`GET /v1/missions/{mission_id}/events?limit=<1..500>`

Response:

```json
{
  "mission_id": "mis_123",
  "total": 2,
  "data": [
    {
      "sequence": 10,
      "event_type": "mission:update",
      "timestamp": "2026-05-27T17:04:00Z",
      "payload": {
        "status": "running",
        "current_step": "router"
      }
    },
    {
      "sequence": 11,
      "event_type": "cost:update",
      "timestamp": "2026-05-27T17:05:00Z",
      "payload": {
        "cumulative_cost_usd": 0.0042,
        "token_count": 1200
      }
    }
  ]
}
```

## 5) SSE Contract (v1)

### 5.1 Endpoint

`GET /v1/events/stream`

Headers:

- `Accept: text/event-stream`
- `X-KRATOS-KEY: <token>` (prod)

### 5.2 Canonical event names

- `mission:update`
- `aurora:response`
- `sprint:task:done`
- `lead:new`
- `health:alert`
- `cost:update`
- `heartbeat`

### 5.3 Envelope

Each SSE frame must serialize:

```json
{
  "type": "mission:update",
  "ts": 1770000000.0,
  "data": {}
}
```

## 6) Compatibility Mapping (legacy -> v1)

Legacy events accepted during migration only:

- `mission_started` -> `mission:update` with `payload.status=running`
- `mission_completed` -> `mission:update` with `payload.status=completed`
- `mission_failed` -> `mission:update` with `payload.status=failed`
- `cost_updated` -> `cost:update`

Legacy route bridge (temporary):

- `/missions/active` -> `/v1/missions`
- `/missions/{id}/events` -> `/v1/missions/{id}/events`
- `/live/stream` -> `/v1/events/stream`

## 7) Rollout Order (safe)

1. OMNIS exposes all `/v1/*` routes + SSE aliases.
2. KRATOS switches hooks to `/v1/*`.
3. Auth switches to `X-KRATOS-KEY`.
4. Remove aliases after freeze window.

## 8) Done Criteria

- KRATOS reads missions from `/v1/missions`.
- KRATOS consumes `/v1/events/stream`.
- SSE events use canonical names.
- Auth header `X-KRATOS-KEY` validated in prod.
- No direct unversioned integration remains.

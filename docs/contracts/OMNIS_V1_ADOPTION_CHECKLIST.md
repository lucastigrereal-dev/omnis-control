# OMNIS v1 Adoption Checklist

Reference: `docs/contracts/OMNIS_KRATOS_CONTRACT_V1.md`

## Required changes

1. Expose versioned mission routes:
   - `GET /v1/missions`
   - `GET /v1/missions/{mission_id}`
   - `GET /v1/missions/{mission_id}/events`
2. Expose versioned SSE route:
   - `GET /v1/events/stream`
3. Normalize SSE event names to v1 canonical names.
4. Accept `X-KRATOS-KEY` as canonical auth header.

## Temporary compatibility aliases

- Keep `/missions/active` -> `/v1/missions`
- Keep `/missions/{id}/events` -> `/v1/missions/{id}/events`
- Keep `/live/stream` -> `/v1/events/stream`
- Keep `X-API-Key` and `Authorization: Bearer` during migration window.

## Current gap (as audited)

- Mission list/detail currently served by unversioned `/missions` router.
- SSE currently served by `/events`.
- Auth currently centered on `X-API-Key`/Bearer.

## Definition of done

- All KRATOS mission/sse calls hit `/v1/*`.
- Auth in prod validated via `X-KRATOS-KEY`.
- Legacy aliases removable without breaking KRATOS.

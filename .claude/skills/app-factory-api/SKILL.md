# app-factory-api

## When to use
- After schema generated, before frontend scaffolding
- When operator says "gerar API", "scaffold endpoints", "W133"

## When NOT to use
- Without approved schema models
- For real API deployment (mock-first only at this stage)

## Inputs
- Schema models from W132
- PRD routes from W131

## Steps
1. Read schema models (entity list + fields)
2. Read PRD routes (endpoint list)
3. For each route: generate CRUD or custom endpoint
4. Generate mock handlers (return sample data, no real DB)
5. Generate route registry with FastAPI/Flask adapter
6. Generate openapi.json from route definitions

## Output
- `src/app_factory/api/<app_slug>/routes.py`
- `src/app_factory/api/<app_slug>/handlers.py`
- `src/app_factory/api/<app_slug>/openapi.json`
- `tests/app_factory/api/test_<app_slug>_routes.py` (skeleton)

## Blocking criteria
- Schema not found → cannot map entities to endpoints
- Route conflicts with existing apps → flag

# app-factory-builder

## Description
Executes the App Factory pipeline end-to-end: reads architecture blueprint,
generates all source modules (schema, API, frontend, auth, migrations, config,
tests), validates each layer, and produces a deployable package.

## When to use
- After architecture blueprint approved
- When operator says "build app", "generate app", "factory run"

## When NOT to use
- Without approved architecture blueprint
- For partial generation (use individual wave skills)

## Inputs
- Architecture blueprint YAML from app-factory-architect
- PRD YAML from W131

## Steps
1. Load blueprint → validate completeness
2. Generate schema models (W132)
3. Generate API routes + handlers (W133)
4. Generate frontend scaffolds (W134)
5. Generate auth middleware (W135)
6. Generate DB migrations (W136)
7. Generate app config (W137)
8. Generate test skeletons (W138)
9. Package all artifacts (W139)
10. Run E2E validation (W140)

## Output (per app)
- `src/app_factory/schema/<app_slug>/` — models
- `src/app_factory/api/<app_slug>/` — routes, handlers, openapi
- `src/app_factory/frontend/<app_slug>/` — components, pages
- `src/app_factory/auth/<app_slug>/` — roles, policies
- `src/app_factory/migration/<app_slug>/` — SQL up/down
- `src/app_factory/config/<app_slug>/` — YAML config
- `tests/app_factory/` — test skeletons
- `bundles/<app_slug>.zip` — deployable package

## Safety
- All generation is dry-run by default
- Package must pass integrity check before deploy
- Operator must approve before real file write

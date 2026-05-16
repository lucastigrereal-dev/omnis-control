# App Factory Rules

## Identity
App Factory generates complete application packages from structured briefings.
It produces: PRD → schema → API → frontend → auth → migrations → config → tests → package.

## Absolute rules
1. **Never overwrite** existing app without explicit operator approval
2. **dry_run=True** — always simulate before writing real files
3. **Validate schema** before generating API or frontend code
4. **Mock-first** — all external integrations start as mocks
5. **No real credentials** — generated apps never contain real keys
6. **Test scaffold before logic** — B8 test skeleton must pass before B4 implementation
7. **Package integrity** — generated zip must pass round-trip verify
8. **Operator review gate** — human approves PRD before code generation begins

## App Factory pipeline
```
briefing → PRD (W131) → Schema (W132) → API (W133) → Frontend (W134)
                            ↓
              Auth (W135) → Migration (W136) → Config (W137) → Tests (W138) → Package (W139)
```

## Gates per wave
1. PRD approved by operator
2. Schema validates against PRD requirements
3. API contracts match schema entities
4. Frontend scaffolds match PRD pages
5. Auth roles cover all API endpoints
6. Migrations are reversible (up + down)
7. Config is environment-agnostic (no hardcoded URLs)
8. Tests cover all endpoints + edge cases
9. Package is self-contained + deployable
10. E2E passes full pipeline with mock adapters

## No-touch
- Never read .env or secrets during generation
- Never hardcode ports, hosts, or credentials in templates
- Never generate code that calls real APIs without feature flags

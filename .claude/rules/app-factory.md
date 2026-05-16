# App Factory Rules

## Identity
App Factory generates complete application packages from structured briefings.
It produces: idea-intake → PRD → db-schema → API-contract → frontend-plan → test-plan → repo-scaffold → openhands-mock → package-export → E2E.

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
idea-intake (W131) → PRD (W132) → DB Schema (W133) → API Contract (W134)
                              ↓
              Frontend Plan (W135) → Test Plan (W136) → Repo Scaffold (W137) → OpenHands Mock (W138) → Package Export (W139) → E2E (W140)
```

## Gates per wave
1. W131 — Idea intake captured with app name, domain, target users
2. W132 — PRD generated and approved by operator
3. W133 — DB schema validates against PRD entities
4. W134 — API contracts match schema models
5. W135 — Frontend plan matches PRD routes
6. W136 — Test plan covers all endpoints + edge cases
7. W137 — Repo scaffold includes all generated modules
8. W138 — OpenHands mock adapter passes dry-run
9. W139 — Package is self-contained + deployable
10. W140 — E2E passes full pipeline with mock adapters

## No-touch
- Never read .env or secrets during generation
- Never hardcode ports, hosts, or credentials in templates
- Never generate code that calls real APIs without feature flags

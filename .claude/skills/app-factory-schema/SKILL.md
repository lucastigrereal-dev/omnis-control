# app-factory-schema

## When to use
- After PRD approved, before API generation
- When operator says "gerar schema", "design entities", "W132"

## When NOT to use
- Without approved PRD (needs entity list)
- For simple config files (use app-factory-config)

## Inputs
- PRD YAML: entities, relationships, constraints from W131
- Stack preference: dataclasses (default) or Pydantic

## Steps
1. Read PRD entities from data/app_factory/prds/<slug>.yaml
2. For each entity: define fields, types, defaults, validators
3. Define relationships (1:1, 1:N, N:M)
4. Generate dataclass/Pydantic models
5. Generate __init__.py with exports
6. Validate round-trip: to_dict() / from_dict()

## Output
- `src/app_factory/schema/<app_slug>/models.py`
- `src/app_factory/schema/<app_slug>/__init__.py`
- `tests/app_factory/schema/test_<app_slug>_models.py` (skeleton)

## Blocking criteria
- PRD not found → cannot proceed
- Duplicate entity names → flag in PRD

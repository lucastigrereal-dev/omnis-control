# Scope Definitions

Each parallel squad gets a scope file:
`.claude/scopes/<wave>-<squad>.md`

## Scope file format

```markdown
# Scope: <wave> - <squad>

## Allowed paths
- src/<module>/**
- tests/<module>/**
- docs/<module>/**

## Forbidden paths
- .env, secrets/, exports/, data/
- other squads' src/ directories
- KRATOS repo
- War Room canon/

## Allowed actions
- Read, Write, Edit in allowed paths
- pytest in allowed test paths

## Forbidden actions
- External API calls
- Real OAuth
- Real publish/send/deploy
- git push, merge, rebase

## Handoff
- Report path: docs/reports/<SQUAD>_REPORT.md
```

## Active scopes
(None yet — created during wave execution)

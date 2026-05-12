# P18 Governance/Audit — Skeleton Report

**Date:** 2026-05-12
**Status:** COMPLETE
**Phase:** P18
**Wave:** 2

## Overview

Governance layer skeleton providing risk classification, approval policy engine, scope guarding, and audit log planning for the OMNIS control ecosystem.

## Package Structure

```
src/governance/
    __init__.py       # Public API re-exports (37 symbols)
    models.py         # 4 dataclass models + constants
    service.py        # 4 service classes
    errors.py         # 6 exception classes

tests/governance/
    __init__.py
    test_models.py    # 30 tests
    test_service.py   # 38 tests

docs/governance/
    P18_GOVERNANCE_AUDIT.md  # This file
```

## Models

### Constants (string-based enums)

| Group | Values |
|---|---|
| **RiskLevel** | `low`, `medium`, `high`, `critical` |
| **ActionType** | `read`, `write`, `send`, `deploy`, `delete`, `financial`, `configure` |
| **Verdict** | `approved`, `denied`, `requires_approval` |

### Default Risk Mapping

| Action | Risk Level |
|---|---|
| `read` | `low` |
| `write` | `medium` |
| `send` | `high` |
| `configure` | `high` |
| `deploy` | `critical` |
| `delete` | `critical` |
| `financial` | `critical` |

### Dataclass Models

- **ApprovalPolicy** — Defines when approval is required or auto-denied
- **ScopeRule** — Defines allowed/blocked actions and paths
- **AuditEvent** — Immutable record of a governance-relevant action
- **GovernanceDecision** — Verdict + reasoning for an action

All models follow the standard pattern: `.new()` factory, `.to_dict()`, `.from_dict()`.

## Services

### RiskClassifier
Classifies actions into risk levels using a configurable `action_type → risk_level` map.

### ApprovalPolicyEngine
Evaluates actions against registered policies. First-matching-policy-wins. Destructive actions (`deploy`, `delete`, `financial`) always require approval by default.

### ScopeGuard
Validates actions against allowed/blocked scope rules. Checks blocked actions, blocked paths, and explicit allow-rules. Disabled rules are ignored.

### AuditLogPlanner
Records audit events and governance decisions. Provides filtering by risk level, action type, and verdict. Generates merged audit log with event→decision linking.

## Design Decisions

1. **No real hooks** — This skeleton does not integrate with actual execution hooks, CLI middleware, or settings. That is deferred to future phases.
2. **String constants over Python enums** — Follows the existing project convention (e.g., `TRIGGER_WEBHOOK = "webhook"`).
3. **Dataclass models with `.new()` / `.to_dict()` / `.from_dict()`** — Consistent with P11 (app_factory) and P12 (automation) patterns.
4. **Deterministic, synchronous services** — No I/O, no async, no external dependencies. Pure business logic.
5. **Destructive actions as a concept** — `deploy`, `delete`, `financial` are treated as inherently dangerous and always require approval.

## Test Coverage

- **Test file:** `tests/governance/test_models.py`
- **Test file:** `tests/governance/test_service.py`
- **Total tests:** 68 (30 models + 38 services)
- **Status:** All passing

### test_models.py (30 tests)

| Class | Tests |
|---|---|
| `TestApprovalPolicy` | 7 |
| `TestScopeRule` | 7 |
| `TestAuditEvent` | 7 |
| `TestGovernanceDecision` | 7 |
| `TestConstants` | 5 |

### test_service.py (38 tests)

| Class | Tests |
|---|---|
| `TestRiskClassifier` | 8 |
| `TestApprovalPolicyEngine` | 9 |
| `TestPolicyEvalResult` | 2 |
| `TestScopeGuard` | 12 |
| `TestAuditLogPlanner` | 10 |
| `TestDestructiveActions` | 5 |

## Verification Checklist

- [x] Package `src/governance/` created with `__init__.py`, `models.py`, `service.py`, `errors.py`
- [x] 6 risk/action/decision constants + 4 dataclass models
- [x] 4 service classes: RiskClassifier, ApprovalPolicyEngine, ScopeGuard, AuditLogPlanner
- [x] Risk rules: read=low, write=medium, send/deploy/delete/financial=high/critical
- [x] Destructive action always requires approval
- [x] Tests pass: `python -m pytest tests/governance/ -q`
- [x] No changes to core, CLI, existing packages, .claude/settings, or pyproject.toml
- [x] Documentation complete

# Skills Used and Missing — OMNIS System Consolidation

**Date:** 2026-05-21

---

## Personas Requested vs Existing Skills

| Requested Persona | Existing Skill | Status |
|---|---|---|
| `system-architect` | `architect` | ✅ Exact match |
| `governance-auditor` | `qa` + `auditor` | ✅ Equivalent via qa |
| `skill-registry-auditor` | `registry` | ✅ Exact equivalent |
| `capability-graph-architect` | `architect-omnis` | ✅ Equivalent |
| `observability-engineer` | `monitoring` → `qa-guard` + `auditor` | ⚠️ Partial — no dedicated observability skill |
| `backend-architect` | `builder` + `schema-planner` | ✅ Equivalent pair |
| `api-contract-auditor` | `integration-architect` | ✅ Equivalent |
| `security-architect` | `guardian` + `git_guardian` | ✅ Equivalent pair |
| `mission-control-product-owner` | `mission-control-mapper` | ✅ Exact match |
| `operational-truth-engineer` | `auditor` + `mission-control-mapper` | ⚠️ Partial — no dedicated operational-truth skill |
| `expression-system-architect` | `brand` + `design` + `humanizer` | ✅ Equivalent trio |
| `integration-boundary-auditor` | `integration-architect` | ✅ Equivalent |
| `git-guardian` | `git_guardian` | ✅ Exact match |

## Missing Skills

| Skill | Impact | Recommended Action |
|---|---|---|
| `observability-engineer` | No dedicated observability monitoring skill | Use `qa-guard` + `auditor` for now |
| `operational-truth-engineer` | No skill that explicitly tracks "what is true right now" across systems | Use `auditor` + `mission-control-mapper` for now |

No new skills need to be created — all personas can be emulated by existing skills.

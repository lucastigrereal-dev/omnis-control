# OMNIS Governance, Risk & Runtime Gap

**Date:** 2026-05-21

---

## Governance Levels (L0-L5)

| Level | Name | OMNIS Coverage | Status |
|---|---|---|---|
| L0 | No governance | Raw terminal access | ❌ Not blocked |
| L1 | Observer | Read-only monitoring | ✅ Health checks, audit |
| L2 | Approval gates | Human-in-loop for sensitive actions | ✅ `approval_runtime/`, `guardian` |
| L3 | Constrained execution | Pre-flight validation + boundaries | ✅ `skill_execution/boundaries.py` |
| L4 | Policy-as-code | Automated policy enforcement | ⚠️ Partial (`governance/` module) |
| L5 | Self-governance | System adapts to risk | ❌ Not implemented |

## SAFE / CAUTION / DANGER Classification

| Zone | Definition | Examples | Gate Required |
|---|---|---|---|
| 🟢 SAFE | Read-only, no side effects | Health checks, skill listing, report generation | None |
| 🟡 CAUTION | Local side effects | File writes to reports/, git add, skill execution | `guardian` pre-flight |
| 🔴 DANGER | External/production side effects | Publishing, API calls, OAuth, production DB writes | `guardian` + `approval_runtime` + human |

## Governance Modules (in omnis-control)

| Module | Function | Status |
|---|---|---|
| `governance/` | Approval gate, enforcer, service | ✅ Complete |
| `approval_runtime/` | Runtime policy, tokens, store | ✅ Complete |
| `approval_center/` | Approval workflow | ✅ Complete |
| `execution_contracts/` | Permissions, validators, outcomes | ✅ Complete |
| `skill_execution/boundaries.py` | Skill-level boundaries | ✅ Complete |
| `skill_execution/permission_gate.py` | Permission enforcement | ✅ Complete |
| `guardian` (skill) | Pre-flight validation | ✅ Active |
| `merge-gate` (skill) | Merge decision | ✅ Active |
| `real_world_actions/` | Approval chain, sandbox, rate limiter, registry | ✅ Complete |
| `control_tower/` | Decision engine, risk, boundaries, next action | ✅ Complete |

## Dangerous Actions — Guard Mapping

| Action | Guardian | Approval Gate | Human Required |
|---|---|---|---|
| Instagram publish | ✅ `guardian` | ✅ `approval_runtime` | ✅ Yes |
| Send DM | ✅ `guardian` | ✅ `approval_runtime` | ✅ Yes |
| Delete files | ⚠️ `git_guardian` | ⚠️ Partial | ✅ Yes |
| Database write (prod) | ✅ `guardian` | ✅ `approval_runtime` | ✅ Yes |
| OAuth token use | ❌ Not gated | ✅ `approval_runtime` | ✅ Yes |
| Financial record change | ✅ `guardian` | ✅ `approval_runtime` | ✅ Yes |
| n8n automation start | ✅ `automation/n8n_safety_gate.py` | ✅ | ✅ Yes |
| Webhook send | ✅ `webhook-guardian` | ✅ | Configurable |

## What Can Be Automatic

| Action | Gate | Rationale |
|---|---|---|
| Health checks | None | Read-only |
| Skill listing/registry | None | Read-only |
| Report generation | None | File write to reports/ only |
| Code audit | None | Read-only |
| Content draft generation | None | No publication |
| Schedule optimization | None | Config change only |

## What Requires Approval

| Action | Approver |
|---|---|
| Instagram post publication | Human (Tigrão) |
| DM campaign send | Human |
| Production DB migration | Human |
| Financial action | Human |
| Skill registry modification | Human |
| Work order execution with side effects | Human or `approval_runtime` policy |

## What Must Be Blocked

| Action | Mechanism |
|---|---|
| `rm -rf /` | Shell safety |
| Env var exposure | `git_guardian`, `.env` in `.gitignore` |
| Publishing without approval | `guardian` + `approval_runtime` |
| Production write without gate | `skill_execution/permission_gate.py` |
| Swarm activation | Not implemented yet (P2) |

## Gap Analysis

| Gap | Impact | Priority |
|---|---|---|
| No L4 policy-as-code engine | Policies are in code but not declarative | P1 |
| No L5 self-governance | System can't auto-adapt | P2 |
| `governance/` module exists but unused by skills | Skills bypass formal governance | P1 |
| OAuth token usage not explicitly gated | Risk of credential exposure | P0 |
| No audit trail for `guardian` decisions | Can't review past gates | P1 |

## Summary
**Governance Status: L2 OPERATIONAL.** Human-in-loop for dangerous actions. Guardian + approval_runtime + boundaries form a working chain. L4 and L5 are roadmap. OAuth token gating is a P0 gap.

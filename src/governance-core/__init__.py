"""governance-core — canonical governance authority for the OMNIS ecosystem.

7 modules:
  policies/     — risk taxonomy, translation tables, provider policy
  permissions/  — unified action classifier, forbidden patterns
  approvals/    — single canonical approval gate + human slot
  manifests/    — capability, system, mission governance manifests
  contracts/    — governance, enforcement, audit contracts
  risks/        — single canonical risk classifier
  audit/        — single canonical decision log

Authority: ABA 4 L0-L5 risk taxonomy (canonical).
Enforcement: governance_runtime.py (KRATOS runtime) + jarvis-guardrails (CLI).
"""

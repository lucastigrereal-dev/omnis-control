---
title: Fix bug in login flow
aba: aba-0
type: bugfix
status: READY
risk: LOW
project: omnis-control
allowed_paths: src/auth/, tests/auth/
forbidden_paths: src/.kratos/, C:\Users\lucas\.kratos
requires_approval: false
dry_run: true
---

Investigate and fix the login redirect issue reported by users.

Steps:
1. Reproduce the bug locally
2. Identify root cause
3. Apply fix
4. Run tests
5. Generate report

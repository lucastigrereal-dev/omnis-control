# architecture-auditor

## When to use
- Before implementing a new module
- Before merging a squad's work
- When a module exceeds 10 files

## Checks
1. God Module: single file >500 lines or >20 methods → flag
2. Circular imports: module A imports B, B imports A → block
3. Boundary violations: OMNIS importing from KRATOS → block
4. Duplicate responsibility: two modules doing the same thing → flag
5. Missing __init__.py exports → flag

## Forbidden files
- .env, secrets/, .kratos/

## Output
- PASS: no issues
- FLAG: warnings, can proceed with caution
- BLOCK: must fix before proceeding

## Checklist
- [ ] All imports resolve
- [ ] No module >500 lines
- [ ] No boundary violations
- [ ] No duplicate responsibility
- [ ] __init__.py exports are complete

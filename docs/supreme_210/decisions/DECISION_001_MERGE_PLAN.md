# DECISION 001 — Merge Plan: feature/omnis-5waves-runtime-supreme → master

**Date:** 2026-05-15 | **Status:** PLAN_ONLY — awaiting authorization

## Pre-conditions
1. Working tree clean
2. Full suite green: `python -m pytest tests/ --import-mode=importlib -p no:warnings -q`
3. On branch `feature/omnis-5waves-runtime-supreme`
4. Zero conflicts with master (fast-forward possible)

## Merge sequence

```sh
# Step 1: Verify state
git status --short          # Must be clean
git log --oneline -5        # Confirm HEAD

# Step 2: Full suite (final gate)
python -m pytest tests/ --import-mode=importlib -p no:warnings -q

# Step 3: Checkout master
git checkout master
git log -1 --oneline        # Confirm baseline: c136065

# Step 4: Fast-forward merge
git merge --ff-only feature/omnis-5waves-runtime-supreme

# Step 5: Post-merge verification
git log --oneline -5        # Confirm merge
python -m pytest tests/ --import-mode=importlib -p no:warnings -q

# Step 6: Push (REQUIRES SEPARATE AUTHORIZATION)
git push origin master
```

## Rollback plan
If merge fails or post-merge tests fail:
```sh
git checkout master
git reset --hard c136065    # Back to baseline
```
If already pushed (shouldn't happen without auth):
```sh
git revert <merge-commit>   # Safe undo
```

## What's in the merge
- 39 commits (W8-W12 + W001 + cleanup)
- 81+ new files (29 source, 30 test, 22+ docs)
- 5,902 tests passing
- 100% dry-run coverage
- Zero external API dependencies
- Zero credential exposure

## Authorization required
- [ ] Lucas approves merge
- [ ] Full suite re-run immediately before merge
- [ ] Git status clean confirmed
- [ ] Push requires SEPARATE second authorization

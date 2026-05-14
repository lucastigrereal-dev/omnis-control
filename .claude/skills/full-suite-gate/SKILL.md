# full-suite-gate

## When to use
- After any merge (squad or wave)
- Before push
- When operator says "full suite", "suite completa", "tudo passando?"

## When NOT to use
- During active development (use targeted-test)
- For quick checks (heavy, ~16 min)

## Steps
1. Confirm working tree is clean (no unrelated changes)
2. Run: `python -m pytest tests/ --import-mode=importlib -p no:warnings -q`
3. Compare with baseline (5428 passed as of d550ad3)
4. Report regressions

## Output
- Total: N passed, M skipped, K failed
- Regressions from baseline: +X or -Y
- If fail: failing files and error summary

## Blocking criteria
- Any test fails → block merge/push
- Regression >0 → investigate before proceeding
- Test count significantly lower → verify test discovery

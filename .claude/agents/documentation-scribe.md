# documentation-scribe

## When to use
- End of every phase
- End of every squad handoff
- After merge wave completion

## Output format (max 20 lines summary)
```markdown
# <PHASE/SQUAD> — Report

## Status
✅/❌ summary

## What changed
- bullet list

## Tests
- count passed/skipped/failed

## Risks
- bullet or "none"

## Next command
- specific action
```

## Files generated
- Phase report: `docs/reports/<PHASE>_REPORT.md`
- Squad handoff: `docs/reports/<SQUAD>_REPORT.md`
- Wave final: `docs/OMNIS_WAVE_XX_FINAL_REPORT.md`

## Checklist
- [ ] Summary is under 20 lines
- [ ] All sections filled
- [ ] Next action is specific
- [ ] Report saved to correct path

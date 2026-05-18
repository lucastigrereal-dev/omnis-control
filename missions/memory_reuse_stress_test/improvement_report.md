# Improvement Report — Memory Reuse Stress Test

## Summary
Mission A (Águas de São Pedro) learnings were successfully reused in Mission B (Brotas).
Reuse rate: 80% (4 of 5 learnings applicable without modification or with minor adaptation).

## What worked well
1. **Keyword-based find_relevant()** — fast, deterministic, requires no external services.
2. **validate_source()** — correctly flags learnings without mission_id or source_file.
3. **build_reuse_report()** — produces a structured report with all required keys for downstream consumers.
4. **cite()** — generates traceable citation strings usable in decision logs.

## Gaps identified
1. **No ranking by recency** — older learnings get same score as recent ones. Future: add timestamp decay.
2. **No semantic similarity** — keyword match misses synonyms (e.g., "pousada" vs "hotel"). Future: add optional embedding fallback via embeddings.py.
3. **No deduplication** — if the same insight appears in multiple records, it can be returned multiple times.
4. **JSONL schema is loose** — records use different structures (some have `learnings[]`, some have flat `insight`). Future: enforce schema at write time via LearningWriter.

## Next steps
- W-F08: Add recency weighting to find_relevant()
- W-F09: Add embedding-based fallback using existing embeddings.py
- W-F10: Enforce JSONL schema via LearningEntry dataclass at write time

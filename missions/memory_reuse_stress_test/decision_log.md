# Decision Log — Memory Reuse Stress Test

## Decision 1: Use keyword match, not embeddings
**Context:** find_relevant() implementation strategy
**Options:** A) keyword match  B) embedding similarity
**Decision:** Keyword match (option A)
**Rationale:** Embeddings require a running vector DB (Qdrant :6333); keyword match works offline and is deterministic for tests. Embeddings can be added in a future wave.
**Risk:** Low — stress test validates reuse logic, not semantic ranking.

## Decision 2: Simulate with real _learnings.jsonl
**Context:** test_load_learnings_real_file uses the actual JSONL from missions/
**Decision:** Use real file as test fixture
**Rationale:** Validates that the loader works on production data, not just synthetic fixtures.
**Risk:** Low — read-only operation; no mutation of the file.

## Decision 3: Missions Águas de São Pedro → Brotas
**Context:** A/B simulation pair selection
**Decision:** Use both as Interior SP tourism destinations
**Rationale:** They share sector (turismo SP), same target audience (hotéis/pousadas), similar content formats — maximizing expected reuse. This is the highest-signal test case.

## Decision 4: validate_source requires mission_id OR source_file
**Context:** What counts as a "proven" source?
**Decision:** At least one of: mission_id, source_file
**Rationale:** Learnings without any traceability reference cannot be trusted for reuse in new missions.

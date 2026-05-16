# W122+W123 — SDR Prospect List + Outreach Sequencer Report

**Date:** 2026-05-15
**Status:** COMPLETE
**Tests:** 72/72 PASS (0.14s) | Commercial+Sales: 273/273 PASS

## Scope
W122: `src/commercial/prospect_list.py` — file-backed registry for HotelLead prospects with filtering, prioritization, and scoring.
W123: `src/commercial/outreach_sequence.py` — 3-step outreach sequencer (D+0, D+2, D+5) across 5 channels, all dry-run.

## Files Created
| File | Lines | Description |
|---|---|---|
| `src/commercial/prospect_list.py` | 230 | ProspectEntry model + ProspectList registry |
| `src/commercial/outreach_sequence.py` | 394 | OutreachMessage, OutreachStep, OutreachSequence, OutreachSequencer |
| `tests/commercial/test_prospect_list.py` | 179 | 31 tests for ProspectList/ProspectEntry |
| `tests/commercial/test_outreach_sequence.py` | 405 | 41 tests for OutreachSequence/OutreachSequencer |

## Files Modified
None — zero existing file changes.

## Architecture

### W122 — Prospect List

**ProspectEntry** wraps HotelLead with list metadata:
- `priority_score` property — deterministic composite: `fit_score + priority_weight(0-30) + tier_bonus(0-15) + region_priority(0-10)`. Range ~0-155.
- `to_dict()/from_dict()` roundtrip with nested HotelLead serialization
- `to_markdown()` for human-readable export

**ProspectList** — file-backed JSONL registry:
- CRUD: `add()`, `get()`, `remove()`, `list_all()`
- Filters: `filter_by_city()`, `filter_by_state()`, `filter_by_tier()`, `filter_by_priority()`, `filter_by_niche()`, `filter_by_region()`, `filter_pursuable()`
- Prioritization: `prioritized()` (sorted by priority_score), `top(n)`, `hot_list()`
- Scoring: `compute_scores()` — adapts legacy 4-factor model (segment_fit, engagement_signal, budget_indicator, urgency) to HotelLead fields
- Export: `export_summary()` (markdown), `to_jsonl()`, `_flush()` + `load()` for file persistence
- Counters: `count`, `pursuable_count`, `premium_candidates`

### W123 — Outreach Sequencer

**Enums:**
- `OutreachChannel` — whatsapp, instagram_dm, email, call, manual
- `StepStatus` — pending, ready, completed, skipped
- `CADENCE_DAYS = [0, 2, 5]` — D+0 (abertura), D+2 (reforco), D+5 (ultimo contato)

**OutreachMessage** — template-generated, never sent:
- Channel-specific templates per step (15 combinations: 3 steps x 5 channels)
- Premium candidate highlighting in D+2 messages
- `sent=False` enforced everywhere, `requires_approval=True` universal
- `to_dict()/from_dict()` roundtrip

**OutreachStep** — single sequence step:
- Links message to position, delay, and status
- `to_dict()/from_dict()` with nested message

**OutreachSequence** — 3-step cadence for one HotelLead:
- `next_action` property — first pending/ready step
- `next_action_date` — computed from delay_days + created_at
- `complete_step(n)`, `skip_step(n)`, `cancel()`
- Auto-transitions to "completed" status when all steps done
- `to_dict()/from_dict()` + `to_markdown()`

**OutreachSequencer** — orchestrator:
- `generate_sequence(hotel_lead, channel)` — builds full 3-step sequence
- `generate_for_prospect_list(prospect_list)` — sequences for all pursuable entries
- `generate_for_hot_list(prospect_list)` — sequences for hot-priority only
- `list_due_actions()` — all ready steps across active sequences
- `advance_all_ready()` — advance one step per active sequence
- File-backed with `to_jsonl()`, `_flush()`, `load()`

### Legacy Integration
W122 `compute_scores()` adapts the 4-factor `score_prospect()` model from `src/commercial_sdr/service.py` to HotelLead fields. The legacy module provides a richer 7-step cadence (~25 day) as an alternative — the new sequencer uses a simpler 3-step (8 day) cadence optimized for hotel outreach speed.

## Security Verification
- Zero env reads, zero API calls, zero network
- All messages: `sent=False`, `dry_run=True`, `requires_approval=True`
- `dry_run=True` universal default on all models
- No real contact data — all fields use HotelLead placeholders
- No Instagram/WhatsApp/Email real API

## Test Results (72/72 PASS)

**W122 — 31 tests:**
- ProspectEntry: create, priority_score (3 variants), dict roundtrip, markdown
- ProspectList: empty, add, add_multiple, get, get_nonexistent, remove, remove_nonexistent
- Filters: by_city, by_state (case insensitive), by_tier, by_priority, by_niche, by_region (case insensitive), pursuable
- Prioritization: prioritized_order, top_n, hot_list (sorted by fit_score desc)
- Counters: pursuable_count, premium_candidates
- Scoring: compute_scores (composite ranking), export_summary
- Persistence: to_jsonl, file_backed_save_load
- Safety: no_external_calls, dry_run_default

**W123 — 41 tests:**
- OutreachMessage: create, to_dict roundtrip
- OutreachStep: create, to_dict roundtrip with message
- Message generation: d0/d2/d5 for email, instagram_dm, whatsapp, call, manual
- Message validation: all_channels_produce_body, no_real_send (15 combinations verified)
- D+2 premium highlight detection
- OutreachSequence: empty, next_action_none, complete_step, complete_already_completed, skip, cancel (verifies all steps transition), to_dict roundtrip, to_markdown
- OutreachSequencer: generate (3 steps, all channels), cadence_days_match_spec, first_step_ready, next_action, complete_and_advance, complete_all_steps
- Integration: generate_for_prospect_list (hot+warm only), generate_for_hot_list (hot only)
- Batch: list_due_actions, advance_all_ready (one step per sequence)
- Management: get, get_nonexistent, list_by_hotel_lead, list_active
- Safety: all_messages_are_dry_run, file_backed_save_load, to_jsonl, no_external_calls

## INDEX vs Prompt
No divergence for W122/W123. INDEX says: W122="Prospect List Contract", W123="Outreach Message Package" — matches prompt exactly.

## Risks
- None. All new files, zero existing code touched.
- `advance_all_ready()` bug caught and fixed during testing (loop was chaining through all steps instead of one-per-sequence).

## Bug Fix
`advance_all_ready()` initially iterated `for i, step in enumerate(seq.steps)` which caused newly-activated steps to be processed in the same loop iteration (6 advances instead of 2). Fixed by using `seq.next_action` to only advance one step per sequence per call.

## Contracts Created
- `ProspectEntry.to_dict()` → compatible with `ProspectEntry.from_dict()` + `HotelLead.from_dict()`
- `OutreachSequence.to_dict()` → compatible with `OutreachSequence.from_dict()` + `OutreachStep.from_dict()` + `OutreachMessage.from_dict()`

## Next Step
Per cadence policy: **W124 solo** — Lead Qualifier (BANT). INDEX labels it "Partnership Offer Builder" — follow prompt per established policy.

### Pontos de atencao para W124 (Lead Qualifier BANT):
- BANT = Budget, Authority, Need, Timeline
- Deve integrar com HotelLead + ProspectList sem duplicar scoring
- Legacy `OpportunityScore` ja cobre Budget/Need parcialmente — wrapper ou extend?
- Risco de divergencia INDEX vs prompt (INDEX: "Partnership Offer" vs prompt esperado: "Lead Qualifier")
- Manter dry_run, zero API, file-backed

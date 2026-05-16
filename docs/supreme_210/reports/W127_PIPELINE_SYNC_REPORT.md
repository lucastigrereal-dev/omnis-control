# W127 — Commercial Pipeline Sync Bridge Report

**Date:** 2026-05-15
**Status:** COMPLETE
**Tests:** W127: 34/34 PASS | Commercial+Sales: 413/413 PASS

## Scope
Create `src/commercial/pipeline_sync.py` — unidirectional bridge connecting the Commercial SDR layer (W121-W126) to Sales/CRM pipeline stages (W111-W120). Generates unified `PipelineSyncEntry` per lead with suggested pipeline stage, 1-page SDR Meeting Brief (markdown), and batch export summary.

Delivers both INDEX divergences resolved:
- INDEX says `sdr-meeting-brief` — Meeting Brief markdown included
- Recap says "Pipeline CRM Sync" — Stage mapping bridge included
- No full dashboard — reserved for W129 (`sdr-metrics` per INDEX)

## Files Created

| File | Lines | Description |
|---|---|---|
| `src/commercial/pipeline_sync.py` | 373 | PipelineSyncBridge + PipelineSyncEntry + stage mapping + meeting brief |
| `tests/commercial/test_pipeline_sync.py` | 337 | 34 tests: SuggestStage (9) + PipelineSyncEntry (5) + PipelineSyncBridge (20) |

## Files Modified
None — zero existing file changes.

## Architecture

### Stage Mapping (unidirectional, no import from src/sales/)

| Commercial Status | → | Suggested Stage |
|---|---|---|
| DISQUALIFIED | → | `arquivado` |
| MISSING_INFO | → | `novo` |
| LOW_FIT | → | `novo` |
| NURTURE + hot/warm | → | `qualificado` |
| NURTURE + cold | → | `novo` |
| QUALIFIED (no package) | → | `qualificado` |
| QUALIFIED + PackageMatch | → | `proposta` |
| Any + ProposalBrief | → | `negociacao` |

### PipelineSyncBridge API
- `sync(hl, bant, pkg_match?, proposal_brief?)` → PipelineSyncEntry
- `sync_batch(leads, bant_results, pkg_matches?, proposal_briefs?)` → sorted list
- `sync_from_prospect_list(prospect_list, ...)` → batch via ProspectList
- `summary_by_stage(entries)` → dict[stage, count]
- `summary_actionable(entries)` → actionable/non_actionable/total
- `export_report(entries)` → markdown report by stage

### Meeting Brief (8 sections)
1. Qualificacao BANT (reasons + risks)
2. Pacote Recomendado (rationale)
3. Angulo Comercial
4. Talking Points
5. Valor Esperado
6. Canais Recomendados (+ profiles)
7. Objecoes Mapeadas (count + types)
8. Estrategia de Abordagem (next action)

### PipelineSyncEntry properties
- `is_actionable` — True if stage in (qualificado, proposta, negociacao)
- `stage_index` — Position in STAGE_ORDER (0=novo, 3=negociacao, -1=unknown)

## Contracts Consumed (read-only)

| Module | Wave | What |
|---|---|---|
| `hotel_lead.py` | W121 | HotelLead fields |
| `lead_qualifier.py` | W124 | BANTResult, tiers, reasons, risks |
| `package_matcher.py` | W125 | PackageMatch, rationale, channels |
| `proposal_brief.py` | W126 | ProposalBrief, angle, talking points, objections |
| `prospect_list.py` | W122 | ProspectList for batch sync |
| `src/sales/pipeline.py` | legacy | PipelineStage mirrored as SyncStage constants (NOT imported) |

## INDEX vs Prompt Divergence — RESOLVED

| Source | W127 Definition |
|---|---|
| INDEX_W011_W210.md | `sdr-meeting-brief` — Meeting Brief |
| Recap anterior | "Pipeline CRM Sync" |
| Prompt atual | Pipeline Sync Bridge |

**Resolution:** W127 delivers BOTH. The sync bridge maps commercial status → pipeline stage, AND generates a Meeting Brief markdown per lead. No full dashboard — that belongs in W129 (`sdr-metrics`).

## Test Results (34/34 PASS)

- **TestSuggestStage (9):** disqualified→arquivado, missing_info→novo, low_fit→novo, nurture_hot→qualificado, nurture_cold→novo, qualified_no_package→qualificado, qualified_with_package→proposta, with_proposal→negociacao, nurture_with_proposal→negociacao
- **TestPipelineSyncEntry (5):** create, not_actionable, stage_index_unknown, to_dict_roundtrip, from_dict_empty_defaults
- **TestPipelineSyncBridge (20):** full_pipeline_flow, qualified_no_proposal, disqualified_no_package, nurture_no_package, stage_correct_all_leads, sync_batch, batch_sorted, batch_with_proposals, from_prospect_list, summary_by_stage, summary_actionable, export_report, dry_run_default, deterministic, no_network, meeting_brief_sections, meeting_brief_no_match, sync_with_none, stage_order_constant, stage_matches_valid

### Commercial + Sales: 413/413 PASS
Zero regressions.

## Risks
- None. All new files, zero existing code touched.
- Stage mapping is SUGGESTION only — clearly marked in disclaimer. Not connected to real sales pipeline.

## Next Step
Per cadence policy: **W128+W129 together** — INDEX says W128=`sdr-followup-schedule`, W129=`sdr-metrics`. But since W123 already implemented OutreachSequencer, scope alignment read-only is recommended before execution.

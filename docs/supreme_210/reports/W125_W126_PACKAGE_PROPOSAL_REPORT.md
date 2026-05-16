# W125+W126 — Package Matcher & Proposal Brief Report

**Date:** 2026-05-15
**Status:** COMPLETE
**Tests:** W125: 23/23 PASS | W126: 35/35 PASS | Commercial+Sales: 379/379 PASS

## Scope

### W125 — Commercial Package Matcher
Combined Media Kit Generator + Collab Package Matcher into `src/commercial/package_matcher.py`. Deterministic decision tree matching HotelLead + BANTResult to Starter/Growth/Premium packages with inline media kit brief generation.

### W126 — Commercial Proposal & Objection Brief
Combined Commercial Proposal Brief + Objection Mapping into `src/commercial/proposal_brief.py`. Generates complete proposal briefs from PackageMatch with pre-written objection responses, BANT risk mapping, commercial angles, talking points, and expected value statements.

## Files Created

| File | Lines | Description |
|---|---|---|
| `src/commercial/package_matcher.py` | 473 | PackageMatcher + PackageMatch + MediaKitBrief + NICHE_PROFILES |
| `src/commercial/proposal_brief.py` | 564 | ProposalBriefBuilder + ProposalBrief + ObjectionEntry + objection map |
| `tests/commercial/test_package_matcher.py` | 330 | 23 tests: PackageMatch (5) + PackageMatcher (16) + MediaKitBrief (2) |
| `tests/commercial/test_proposal_brief.py` | 521 | 35 tests: ObjectionEntry (4) + ProposalBrief (5) + CommercialAngle (4) + TalkingPoints (4) + ExpectedValue (3) + ProposalBriefBuilder (15) |

## Files Modified
None — zero existing file changes.

## Architecture

### W125 — PackageMatcher Decision Tree
- **Input:** HotelLead (W121) + BANTResult (W124)
- **Decision flow:** DISQUALIFIED → no match | LOW_FIT → Starter (if Premium + fit>=70) | NURTURE → Growth/Starter by tier | QUALIFIED → Premium/Growth by fit | MISSING_INFO → no match
- **Output:** PackageMatch with package, rationale, channels, profiles, media kit brief, risk notes, next_action
- **Package tiers:** Starter (R$350), Growth (R$990/mês), Premium (R$1.200)
- **References:** PACKAGE_DETAILS (mirrors src/sales/proposals.py, read-only)

### W126 — ProposalBriefBuilder
- **Input:** PackageMatch (W125) + BANTResult (W124) + HotelLead (W121)
- **6 standard objections:** preço, timing, autoridade, concorrência, resultado, urgência — with tier-specific responses
- **BANT risks → objections:** BANTResult.risks mapped as ObjectionEntry with source="bant_risk"
- **Commercial angles by niche:** resort, pousada, boutique, fazenda, eco_resort, glamping + generic fallback
- **Talking points:** tier-adaptive (Premium=dominância, Growth=consistência, Starter=teste)
- **Expected value:** ROI comparison vs Meta Ads (CPM R$0,15 vs R$15-25)
- **Output:** ProposalBrief with 10-section markdown ready for human review
- `build_for_disqualified()` — no-recommendation brief with risks
- `export_batch()` — multi-brief summary report

## INDEX vs Prompt Divergence

| Source | W125 Definition | W126 Definition |
|---|---|---|
| INDEX_W011_W210.md | W125 = "sdr-content-calendar" | W126 = "sdr-response-templates" |
| Prompt atual | Package Matcher + Media Kit | Proposal Brief + Objection Mapping |

**Decision:** Followed prompt. INDEX divergence registered. INDEX entries are placeholder names from earlier roadmap; actual implementation follows commercial SDR pipeline logic.

## Contracts Reused

| Module | Wave | Contract |
|---|---|---|
| `src/commercial/hotel_lead.py` | W121 | HotelLead (composition) |
| `src/commercial/lead_qualifier.py` | W124 | BANTResult, QUALIFIED/NURTURE/LOW_FIT/DISQUALIFIED |
| `src/commercial/prospect_list.py` | W122 | ProspectList (match_from_prospect_list) |
| `src/sales/proposals.py` | legacy | TIER_DETAILS (read-only reference, NOT imported) |

## Test Results

### W125 — Package Matcher: 23/23 PASS
- **TestPackageMatch (5):** create, no_recommendation, to_dict roundtrip, to_markdown with/without match
- **TestPackageMatcher (16):** qualified→Premium/Growth, nurture→Growth/Starter, low_fit→Starter/empty, disqualified→empty, fazenda niche, media_kit_brief, rationale not empty, valid tier always, deterministic, batch sorted, from prospect list, summary_by_package, export report, dry_run, channels by package, niche profiles coverage
- **TestMediaKitBrief (2):** resort brief, pousada brief

### W126 — Proposal Brief: 35/35 PASS
- **TestObjectionEntry (4):** create, to_dict, default source, bant_risk source
- **TestProposalBrief (5):** create with/without package, total_objections, to_dict roundtrip, from_dict empty lists
- **TestCommercialAngle (4):** resort, pousada, fazenda, fallback unknown niche
- **TestTalkingPoints (4):** Premium, Growth, Starter, resultado_garantido always last
- **TestExpectedValue (3):** Premium, Growth, Starter
- **TestProposalBriefBuilder (15):** build from qualified, markdown sections, objection map 6 types, all responses non-empty, BANT risks as objections, no package match, build_for_disqualified, pousada nurture, fazenda niche, dry_run, deterministic, export_batch, export_batch no_match, objection tone adapts by tier, Starter objection mentions R$350

### Commercial + Sales: 379/379 PASS
Full suite clean, zero regressions.

## Risks
- None. All new files, zero existing code touched.

## Next Step
Per cadence policy: **W127 solo** — next microphase in Grupo 13 Commercial/SDR Hotels.

# OMNIS Cockpit Frontend — Audit Report

**Date:** 2026-05-18
**Session:** OF01 — Blueprint Phase

---

## Existing Assets Inventory

### Python Backend (3 modules, ~950 lines)

| Module | Lines | Status |
|--------|-------|--------|
| `src/live_cockpit/` (6 files) | ~350 | Terminal cockpit, fully functional |
| `src/offline_dashboard/service.py` | ~130 | Factory data aggregator |
| `src/reports/cockpit_generator.py` | ~450 | Static HTML generator |

### Existing Cockpit HTML (9 files in `cockpit/`)

| File | Size | Generation |
|------|------|------------|
| index.html | Mission list + stats cards | Auto-generated |
| mission.html | Mission detail (JS-driven) | Auto-generated |
| approvals.html | Pending approvals table | Auto-generated |
| outputs.html | Outputs & exports view | Auto-generated |
| carousel_preview.html | Slide viewer | Pre-existing |
| styles.css | Dark theme (~70 lines) | Auto-generated |
| missions_data.js | All mission metadata JSON | Auto-generated |
| outputs_data.js | Output-specific data | Auto-generated |
| ops_data.js | Operations data | Auto-generated |

### Available Data Sources (13 sources mapped)

14 mission directories, outputs_manifest.json per mission, checksums.json per mission, quality_scores.jsonl, template_registry.json (39 entries), search engine (~761 items), backlog (S09), run batches (S10), brand presets (6 profiles), render presets (5 presets), mission reports, files_index.md per mission, live_cockpit snapshots.

### Data Gaps

- No `data/backlog.json` yet (BacklogManager creates on first use)
- No `cockpit/data/` directory (need to create generator script)
- No `search_index.json` export (need to add JSON export to SearchEngine)
- Quality scores sparse (only test data in quality_scores.jsonl)

---

## Blueprint Summary

**Architecture:** Standalone static HTML + vanilla JS, served from `localhost:3100/cockpit/`, embeddable in KRATOS via iframe.

**8 screens:** Dashboard, Missions, Mission Detail, Backlog (Kanban), Quality, Templates, Runs, Search, System.

**Data pipeline:** Python generator script → static JSON files → vanilla JS reads via `fetch()`.

**Security:** Read-only, no CDN, no framework, no build step, no POST endpoints.

**KRATOS integration:** iframe with sandbox, token via URL param, zero shared state.

---

## Next Step

Sprint OF02: Implement 8 screens + data pipeline following the blueprint.
Commit: `docs(omnis): design frontend cockpit blueprint`

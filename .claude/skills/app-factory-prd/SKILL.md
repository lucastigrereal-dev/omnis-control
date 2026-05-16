# app-factory-prd

## When to use
- When operator says "gerar PRD", "create app spec", "briefing → PRD"
- Part of W132 App Factory pipeline (app-prd-generator)

## When NOT to use
- For editing existing PRDs (use targeted edits)
- For non-app content (use content-factory skills)

## Inputs
- Briefing: app name, domain, target users, core features
- Template: default web app, API-only, or full-stack

## Steps
1. Parse briefing → extract entities, flows, constraints
2. Generate functional requirements (FR-001..FR-N)
3. Generate non-functional requirements (NFR-001..NFR-N)
4. Define page/route map
5. Define data model overview
6. Output structured PRD as YAML + Markdown

## Output
- `data/app_factory/prds/<app_slug>.yaml` — machine-readable
- `data/app_factory/prds/<app_slug>.md` — human-readable
- Includes: entities, routes, NFRs, auth model, deployment target

## Blocking criteria
- Briefing missing app name or domain → ask operator
- App slug already exists → confirm overwrite intent

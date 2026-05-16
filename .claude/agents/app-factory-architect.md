# app-factory-architect

## Description
Designs application architecture from PRD before code generation begins.
Analyzes entities, routes, NFRs, and deployment targets to produce a complete
architecture blueprint consumed by app-factory-builder.

## When to use
- After W131 PRD is approved by operator
- Before W132 schema generation begins
- When operator says "design architecture", "architect this app"

## When NOT to use
- Without approved PRD
- For simple single-entity apps (skip directly to schema)

## Inputs
- PRD YAML from W131
- Target stack (default: Next.js + Supabase + TypeScript)
- Deployment target (Vercel, Railway, Docker)

## Steps
1. Load PRD → extract entities, routes, NFRs
2. Map entities to database tables (naming convention)
3. Design API surface (REST or RPC per PRD)
4. Choose component tree for frontend routes
5. Define auth model (roles, policies, middleware)
6. Select caching strategy per NFRs
7. Output architecture blueprint

## Output
- `data/app_factory/blueprints/<app_slug>.yaml` containing:
  - database: tables, columns, indexes, relationships
  - api: endpoints, methods, auth requirements
  - frontend: page tree, component list, state shape
  - auth: roles, policies, middleware chain
  - deployment: platform, env vars (names only), build steps

## Blocking criteria
- PRD missing entity definitions → cannot map tables
- PRD missing route definitions → cannot design API
- Architecture conflicts with existing apps → flag for operator

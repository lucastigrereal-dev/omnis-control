# OMNIS Wave Registry

| Wave | Grupo | Nome | Status | Branch | Commit | Testes |
|---|---|---|---|---|---|---|
| W001-W130 | G01-G13 | Supreme 210 base | DONE | — | — | — |
| W131 | G14 | app-idea-intake | DONE | — | — | — |
| W132 | G14 | app-prd-generator | DONE | — | d6f61e6 | 109 |
| W133 | G14 | app-db-schema-planner | DONE | master | — | — |
| W134 | G14 | app-api-contract | DONE | master | — | — |
| W135 | G14 | app-frontend-plan | DONE | master | — | — |
| W136 | G14 | app-test-plan | DONE | master | — | — |
| W137 | G14 | app-repo-scaffold | DONE | master | — | — |
| W138 | G14 | app-openhands-mock | DONE | master | — | — |
| W139 | G14 | app-package-export | DONE | master | — | — |
| W140 | G14 | app-factory-e2e | DONE | master | — | — |
| W141-W162 | G14 | AppFactory Advanced | DONE | master | 06caa49 | — |
| W181-W185 | G20 | First Real Missions | DONE | supreme | 5dd22c9 | 87 |
| W191 | G22 | Mission Event Bus | DONE | supreme | f397eca | — |
| W192 | G22 | Mission Logs | DONE | supreme | b539c3f | — |
| W193 | G22 | Mission Metrics | DONE | supreme | 18e234f | — |
| W194-W195 | G22 | Failure Taxonomy + Export | DONE | supreme | 8f48bbb | — |
| G23 | G23 | Health Bridge (minimal) | SUPERSEDED | supreme | ed594dd | — |
| W196-W200 | G23 | Health canonical (omnis_health) | CANONICAL | supreme | 190520a | 86 |
| W201-W205 | G24 | Maintenance Audit | MERGED | supreme | e882432 | — |
| W206-W215 | G25-G26 | Templates + QA | REDUNDANT_ARCHIVE_RECOMMENDED | templates | 233cdf4 | 0 unique |
| P37-P42 | CCOS | RuntimeBridge | DONE | supreme | 28881f9 | 26 |
| W-F1 | G27 | Cockpit Index HTML | DONE | supreme | — | 17 |
| W-F2 | G27 | Cockpit Mission Viewer | DONE | supreme | — | — |
| W-F3 | G27 | Cockpit Approvals Panel | DONE | supreme | — | — |
| W-F4 | G27 | Cockpit Outputs Viewer | DONE | supreme | — | — |
| W-F5 | G27 | Cockpit HTML Generator | DONE | supreme | — | 17 |
| W-A1-A5 | G28 | Mission Engine + Intake + Report | DONE | supreme | — | — |
| W-B1-B5 | G29 | Task Dispatcher + Skill Runner + Learning | DONE | supreme | — | — |
| W-C1-C5 | G30 | Approval Gate + Guardrails + Autonomy | DONE | supreme | — | — |
| W-D1-D5 | G31 | Squad Selector + Squads Especializados | DONE | supreme | — | — |
| W-E1-E4 | G32 | Gap Detector + Forge Orchestrator | DONE | supreme | — | — |
| W-O1 | ONDA10 | WF1 DeepResearchWorkflow (molde) | DONE | omnis-5waves | 4e11859 | 32 |
| W-O2 | ONDA10 | WF2 VideoEditWorkflow (molde) | DONE | omnis-5waves | 0f02a50 | 38 |
| W-O3 | ONDA10 | WF3 AppFactoryWorkflow (molde) | DONE | omnis-5waves | 93fcab3 | 35 |
| W-O4 | ONDA11 | Agency como organismo | DONE | omnis-5waves | 5fc5ab5 | 30 |
| W-O5 | ONDA12 | WF4 CodeRunWorkflow (molde) | DONE | omnis-5waves | 541e398 | 25 |
| W-O6 | ONDA13 | WorkflowRegistry (catalogo) | DONE | omnis-5waves | c961a49 | 28 |
| W-O7 | ONDA14 | MissionOrchestrator | DONE | omnis-5waves | 2d99621 | 18 |
| W-O8 | ONDA15 | SystemHealthWorkflow (health snapshot) | DONE | omnis-5waves | 393b629 | 17 |
| W-O9 | ONDA16 | LeadScoringWorkflow (SDR scoring) | DONE | omnis-5waves | 54c2d88 | 21 |
| W-O10 | ONDA17 | ContentCalendarWorkflow (calendario editorial) | DONE | omnis-5waves | fb7fc01 | 30 |
| W-O11 | ONDA18 | OutreachSequenceWorkflow (SDR 7-passos) | DONE | omnis-5waves | 010e379 | 24 |
| W-O12 | ONDA19 | SDRBatchWorkflow (score+outreach pipeline) | DONE | omnis-5waves | 4f246d5 | 26 |

## Legenda
- DONE: concluído e commitado
- CANONICAL: implementação canônica (supersede alternativas)
- SUPERSEDED: substituído por implementação canônica
- MERGED: mergeado na principal
- REDUNDANT_ARCHIVE_RECOMMENDED: zero commits únicos — remover worktree quando autorizado
- VERIFY: precisa confirmação de estado

## Nota RuntimeBridge P37-P42
- `src/runtime_bridge/` implementado: bridge.py, models.py, errors.py
- Conecta ExecutionGraph → ExecutionQueue com dry_run=True por padrão
- 26/26 testes em tests/runtime_bridge/test_bridge.py
- Verificado em 2026-05-18 — sprint de finalização

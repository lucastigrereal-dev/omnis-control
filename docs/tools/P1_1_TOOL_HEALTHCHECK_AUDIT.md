# P1.1 — Tool Healthcheck Audit

**Data:** 2026-05-07

## Modelos existentes
- `ToolRecord` (Pydantic v2) — tool_id, status, healthcheck, last_validated_at, validation_status, notes
- `ToolStatus`: not_configured, manual, read_only, dry_run, semi_automatic, automatic, blocked, deprecated
- `ToolRegistry` — CRUD + update_status + mark_validated + validation_log.jsonl

## Checkers existentes (src/checkers/)
| Checker | O que verifica | Reutilizável |
|---|---|---|
| docker_check | docker ps, containers | Sim |
| disk_check | psutil disk usage | Sim |
| memory_check | Qdrant + Akasha | Sim |
| publisher_check | Porta 8000 + health endpoints | Sim |
| obsidian_check | Vault .md count | Sim |
| skills_check | Skill files | Parcial |
| video_pipeline_check | Video pipeline | Parcial |
| sectors_check | Setores | Não |
| daily_prophet_check | Daily Prophet | Não |

## Ferramentas verificáveis localmente (read-only)
local_filesystem, docker, akasha_postgres, qdrant, obsidian_vault, publisher_local_dry_run, publisher_os_argos

## Ferramentas NÃO verificáveis agora
instagram_graph_api (OAuth), publer, metricool, gmail, google_drive (creds externas), canva, perplexity (manual), n8n (workflows), openai_api, gemini_api (keys externas), github (remoto), claude_code (sessão manual)

## Riscos
- Tool Registry vazio (precisa discover) — não quebra, mas healthcheck sem tools = sem alvos
- 44 runs órfãs na Metrics Spine — cosmético
- Docker volume prune recomendado contra na P1.0 — sem risco pra P1.1
- Disco 9.6% — não bloqueia P1.1 (read-only)

## Plano de integração
1. `src/tool_registry/healthcheck.py` — ToolHealthResult model + dispatcher
2. Integrar `run_healthcheck(tool_id)` no ToolRegistry
3. Métricas via quick_record_metric
4. CLI: tools health / health-all / health-report
5. Testes + docs + commit

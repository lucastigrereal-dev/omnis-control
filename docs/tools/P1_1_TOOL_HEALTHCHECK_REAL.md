# P1.1 — Tool Registry Healthcheck Real

**Data:** 2026-05-07
**Branch:** master

## Objetivo

Transformar o Tool Registry de cadastro estático em verificador real read-only, sem OAuth, sem APIs externas, sem side effects.

## O que foi construído

### Modelos
- `ToolHealthResult` (Pydantic v2) — tool_id, status_before, status_after, health_status, checked_at, checker_name, duration_ms, message, error_code, evidence, recommendation
- `HealthStatus`: ok, degraded, blocked, not_configured, not_checked, failed

### Healthchecks implementados (8 read-only)

| Ferramenta | Checker | O que verifica |
|---|---|---|
| local_filesystem | check_local_filesystem | Acesso ao repo omnis-control |
| docker | check_docker | docker ps (containers running) |
| obsidian_vault | check_obsidian_vault | Vault .md count |
| akasha_postgres | check_akasha_postgres | Container docker akasha-postgres |
| qdrant | check_qdrant | GET /collections no localhost:6333 |
| publisher_local_dry_run | check_publisher_local_dry_run | Modulo DryRunClient |
| publisher_os_argos | check_publisher_os_argos | Porta 8000 aberta |
| n8n | check_n8n | Porta 5678 aberta |

### Ferramentas NÃO verificadas (10)

| Ferramenta | Motivo |
|---|---|
| instagram_graph_api | OAuth pendente (retorna blocked com recommendation) |
| github | Manual |
| canva | Manual |
| perplexity | Manual |
| publer | Sem credenciais |
| metricool | Sem credenciais |
| gmail | Sem OAuth Google |
| google_drive | Sem token |
| openai_api | Sem key |
| gemini_api | Sem key |
| claude_code | Sessão manual |

### Integração com ToolRegistry
- `registry.run_healthcheck(tool_id)` — executa + persiste log + atualiza last_validated_at
- `registry.run_all_healthchecks()` — executa apenas ferramentas com checker seguro
- `registry.get_last_healthcheck(tool_id)` — busca ultimo resultado
- `registry.get_healthcheck_report()` — relatorio de todas as ferramentas

### Storage
- `data/tool_registry/healthcheck_log.jsonl` — append-only JSONL
- Gitignored (dados de runtime)

### Métricas
- `tool_healthcheck_completed` — emitido quando health_status=ok
- `tool_healthcheck_failed` — emitido quando health_status!=ok
- Campos: tool_id, health_status, duration_ms, status_before, status_after

### CLI (3 novos comandos)

```bash
python jarvis.py tools health <tool_id>        # healthcheck individual
python jarvis.py tools health-all              # todas as ferramentas seguras
python jarvis.py tools health-report           # relatorio do ultimo estado
```

Todos com `--json`.

### Testes
- 35 novos testes (25 unit + 11 CLI)
- `tests/tool_registry/test_tool_healthcheck.py` — modelos, allowlist, checkers, dispatcher, integracao
- `tests/tool_registry/test_tool_health_cli.py` — health, health-all, health-report, --json
- Suite completa: 639 passed, zero regressões

## Limitações

- Healthchecks locais dependem de Docker (docker ps, akasha-postgres)
- Qdrant depende de rede local (:6333)
- ARGOS/n8n verificam apenas porta — nao validam API funcional
- Ferramentas externas (10) permanecem manuais/nao verificadas
- Disco 9.6% — ainda critico, mas nao bloqueia healthcheck

## Por que nao rodou OAuth

Instagram Graph API retorna `blocked` com error_code `OAUTH_REQUIRED` e recommendation clara. Nao chama endpoint externo. Aguarda P1.2.

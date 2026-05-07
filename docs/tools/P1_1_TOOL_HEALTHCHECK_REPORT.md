# P1.1 — Tool Registry Healthcheck Report

**Data:** 2026-05-07
**Branch:** master
**Commit base:** 27e45a7 (P1.0 DISK-1)

---

## Status final por ferramenta

| Tool ID | Status operacional | Health status | Mensagem |
|---|---|---|---|
| local_filesystem | read_only | ok | Repo acessivel |
| docker | read_only | ok | Docker Engine respondendo — 11 containers |
| obsidian_vault | read_only | ok | Vault encontrado — 7833 .md |
| akasha_postgres | read_only | ok | akasha-postgres: Up (healthy) |
| qdrant | blocked | blocked | Qdrant inacessivel |
| publisher_local_dry_run | dry_run | ok | Modulo DryRunClient disponivel |
| publisher_os_argos | degraded | degraded | Porta 8000 fechada |
| n8n | degraded | degraded | Porta 5678 fechada |
| instagram_graph_api | blocked | blocked | OAuth Meta pendente |
| github | manual | not_checked | Manual |
| canva | manual | not_checked | Manual |
| perplexity | manual | not_checked | Manual |
| publer | not_configured | not_checked | Sem credenciais |
| metricool | not_configured | not_checked | Sem credenciais |
| gmail | not_configured | not_checked | Sem OAuth Google |
| google_drive | not_configured | not_checked | Sem token |
| openai_api | not_configured | not_checked | Sem key |
| gemini_api | not_configured | not_checked | Sem key |
| claude_code | manual | not_checked | Sessão manual |

---

## Resumo por health_status

| Health | Quantidade |
|---|---|
| ok | 5 |
| degraded | 2 |
| blocked | 2 |
| not_checked | 10 |

---

## Testes

- **639 passed, 2 skipped, 1 failed**
- +35 novos testes (healthcheck + CLI)
- Falha pré-existente: test_disk_audit_readonly.py (nao relacionado)

---

## Métricas registradas

- 7 tool_healthcheck_completed (ok)
- 2 tool_healthcheck_failed (degraded/blocked)
- Campos: tool_id, duration_ms, health_status, status_before, status_after

---

## Comandos validados

```bash
python jarvis.py tools discover          # ✅ 19 tools descobertas
python jarvis.py tools health docker     # ✅ ok, 125ms
python jarvis.py tools health qdrant     # ✅ blocked
python jarvis.py tools health instagram_graph_api  # ✅ blocked (OAuth)
python jarvis.py tools health-all        # ✅ 7 verificadas
python jarvis.py tools health-report     # ✅ 19 no relatorio
```

---

## Go / No-Go para OAuth (P1.2)

**NO-GO ainda.**

- Qdrant bloqueado — memory search offline
- Publisher OS parado (porta 8000 fechada)
- n8n parado — automacoes offline
- Disco 9.6% — ainda critico
- 2 containers unhealthy (crm-tigre-backend, jarvis_frontend)

**Requisitos para GO:**
1. Resolver Qdrant (container parado/porta)
2. Subir Publisher OS (docker compose up)
3. Mirar disco > 12% livre
4. Healthcheck confirmar 7/8 ferramentas locais ok

---

## Próxima fase recomendada

**P1.2 — OAuth Meta controlado** (após resolver Qdrant + Publisher OS)

Ou alternativamente:
**P1.1b — Qdrant + Publisher OS fix** (reparar serviços parados antes do OAuth)

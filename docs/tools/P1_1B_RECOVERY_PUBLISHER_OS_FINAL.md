# P1.1b — Recovery Publisher OS Final

**Data:** 2026-05-07
**Commits publisher-os:** ff098ee (requirements.txt fix)

---

## Causa

P1.0 `docker image prune -a -f` + `docker container prune -f` removeu containers parados e imagens do stack publisher-os. 3 serviços core offline.

## Recuperação

### Imagens puxadas (5)

| Imagem | Tamanho |
|---|---|
| redis:latest | 204 MB |
| docker.n8n.io/n8nio/n8n:latest | 2.36 GB |
| qdrant/qdrant:latest | 285 MB |
| ghcr.io/berriai/litellm:main-latest | 5.6 GB |
| supabase/postgres:15.1.0.14 | 2.1 GB |

### Imagem rebuildada

| Imagem | Dockerfile |
|---|---|
| publisher-os-publisher-core:latest | core/api/Dockerfile |

**Bug corrigido:** fastapi e uvicorn[standard] adicionados ao requirements.txt. Eram dependências transitivas via MCP/CrewAI que sumiram com versões novas.

### Containers recriados (6)

| Container | Status |
|---|---|
| publisher-os-redis-1 | Up |
| publisher-os-supabase-db-1 | Up |
| publisher-os-qdrant-1 | Up |
| publisher-os-litellm-1 | Up |
| publisher-os-n8n-1 | Up |
| publisher-os-publisher-core-1 | Up |

### Volumes preservados (zero alteração)

| Volume | Dados |
|---|---|
| publisher-os_redis_data | Sessões/fila |
| publisher-os_supabase_db_data | Postgres |
| publisher-os_qdrant_data | 3 collections |
| publisher-os_n8n_data | Workflows (2 ativos) |
| publisher-os_ollama_data | Modelos |
| publisher-os_open_webui_data | Config |

### Portas e health

| Serviço | Porta | Resposta |
|---|---|---|
| Redis | 6382 | PONG |
| Supabase/Postgres | 5434 | accepting connections |
| Qdrant | 6333 | status ok — 3 collections |
| LiteLLM | 4002 | 401 (auth requerida — normal) |
| n8n | 5678 | HTTP 200 |
| Publisher Core | 8000 | {"status":"healthy"} |

### Warnings conhecidos

- JWT_SECRET / MY_WHATSAPP_NUMBER não setados (esperado)
- Field name "copy" shadows attribute (pré-existente)
- LangChainPendingDeprecationWarning (pré-existente)
- LiteLLM 401 no /health (esperado com master key)

## Resultado OMNIS health

| Ferramenta | Antes | Depois |
|---|---|---|
| qdrant | blocked | ok |
| publisher_os_argos | degraded | ok |
| n8n | degraded | ok |
| docker | ok | ok |
| akasha_postgres | ok | ok |
| local_filesystem | ok | ok |

**6 ok, 1 degraded, 0 blocked** (antes: 5 ok, 2 degraded, 2 blocked)

## GO/NO-GO

- GO para preparação OAuth
- GO para testes e desenvolvimento
- NO-GO para OAuth real sem Lucas acordado
- NO-GO para publicação real sem aprovação humana

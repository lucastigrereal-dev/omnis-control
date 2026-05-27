# HANDOFF — W11-W20 OMNIS Evolution COMPLETO
Data: 2026-05-27
Branch: feature/omnis-w11-w20

---

## STATUS FINAL: ✅ W11-W20 Entregues

---

## Commits W11-W20

| Wave | Commit | Descrição |
|------|--------|-----------|
| W11 | `adc14d9` | Marketing sector acoplado ao mission_graph |
| W12 | `c4ab8d4` | LiteLLM config + model validator + deps |
| W13 | `597468a` | Qdrant collections + OmnisMemoryClient |
| W14 | `e035b99` | FastAPI routers /marketing /aurora /cost /events |
| W15 | `0f8935a` | n8n bridge docker + webhook receiver + N8NClient |
| W16 | `7f6f36f` | Multi-agent squads asyncio (instagram/comercial/growth) |
| W17 | `59529b4` | Obsidian indexer script + obsidian_search.py |
| W18 | `6d758ff` | KRATOS bridge: auth API key + SSE EventBus |
| W19 | `570bd7a` | Production hardening: logging + budget guardrail + docker-compose.prod |
| W20 | `aba2d0f` | Validação baseline utópico (documento) |

---

## Arquivos criados (W11-W20)

### Sectors & Agents
- `src/sectors/marketing/__init__.py`
- `src/sectors/marketing/mission_types.py`
- `src/sectors/marketing/router.py` — MarketingRouter + SQUAD_MAP
- `src/sectors/marketing/graph_node.py` — marketing_sector_node
- `src/sectors/marketing/agents/__init__.py`
- `src/sectors/marketing/agents/base.py` — BaseMarketingAgent
- `src/sectors/marketing/agents/content_agent.py`
- `src/sectors/marketing/agents/sdr_agent.py`
- `src/sectors/marketing/squads/__init__.py`
- `src/sectors/marketing/squads/squad_instagram.py` (paralelo)
- `src/sectors/marketing/squads/squad_comercial.py` (sequencial)
- `src/sectors/marketing/squads/squad_growth.py` (paralelo)
- `src/mission_graph/nodes/squad_orchestrator.py` — asyncio gather

### Infra
- `infra/litellm/litellm_config.yaml`
- `infra/litellm/docker-compose.yml`
- `infra/qdrant/docker-compose.yml`
- `infra/n8n/docker-compose.yml`
- `infra/docker-compose.prod.yml` ← prod completo

### Memory
- `src/memory/__init__.py`
- `src/memory/qdrant_collections.py`
- `src/memory/memory_client.py` — OmnisMemoryClient
- `src/memory/obsidian_search.py`

### API
- `src/api/routers/marketing.py`
- `src/api/routers/aurora.py`
- `src/api/routers/cost.py`
- `src/api/routers/events.py` (atualizado W18)
- `src/api/routers/webhooks.py`
- `src/api/auth.py` — require_api_key
- `src/api/event_bus.py` — EventBus pub/sub
- `src/api/structured_logging.py` — JsonFormatter + middleware

### Integrations
- `src/integrations/__init__.py`
- `src/integrations/n8n_client.py`

### Agentic
- `src/agentic/model_validator.py` — bloqueia opus

### Agencia
- `src/agencia/budget_guardrail.py` — BudgetGuardrail hard limit

### Scripts
- `scripts/__init__.py`
- `scripts/index_obsidian.py`

### Tests
- `tests/sectors/marketing/test_marketing_router.py`
- `tests/sectors/marketing/test_squads.py`
- `tests/memory/test_qdrant_collections.py`
- `tests/memory/test_memory_client.py`
- `tests/memory/test_obsidian_search.py`
- `tests/api/test_new_routers.py`
- `tests/api/test_w18_auth_eventbus.py`
- `tests/api/test_structured_logging.py`
- `tests/agencia/test_budget_guardrail.py`
- `tests/scripts/test_index_obsidian.py`
- `tests/integrations/test_n8n_client.py`
- `tests/agentic/test_model_validator.py`

---

## Contagem de testes novos (W11-W20)

| Cluster | Testes | Commit |
|---------|--------|--------|
| marketing router + agents | 12 | W11 |
| mission_graph (D1+W16) | 96 | W16 |
| sectors/marketing squads | 20 | W16 |
| model_validator | 5 | W12 |
| memory (qdrant+obsidian) | 32 | W13+W17 |
| scripts/index_obsidian | 25 | W17 |
| api (new routers+auth+SSE) | 80 | W14+W18+W19 |
| budget_guardrail | 10 | W19 |
| n8n_client | 5 | W15 |
| **Total novos** | **~285** | W11-W19 |

---

## O que Lucas precisa fazer para produção

### Imediato (Docker GO)
```bash
# 1. Subir Qdrant
docker compose -f infra/qdrant/docker-compose.yml up -d

# 2. Subir LiteLLM (requer chaves em .env)
docker compose -f infra/litellm/docker-compose.yml up -d

# 3. Subir n8n
docker compose -f infra/n8n/docker-compose.yml up -d

# 4. Subir tudo em prod
OMNIS_API_KEY=<sua-chave> docker compose -f infra/docker-compose.prod.yml up -d
```

### Configurar variáveis (em .env — NUNCA commitar)
```
OMNIS_API_KEY=<chave secreta que KRATOS vai usar>
QDRANT_HOST=qdrant  # dentro do docker compose
N8N_HOST=n8n
LITELLM_HOST=litellm
OBSIDIAN_VAULT_PATH=C:/Users/lucas/Obsidian  # para W17
```

### Indexar Obsidian (overnight)
```bash
python scripts/index_obsidian.py
```

### KRATOS consumir SSE (KRATOS Onda 3)
- URL: `GET http://omnis-api:8765/events`
- Header: `X-API-Key: <OMNIS_API_KEY>`
- Eventos: mission_started, mission_completed, cost_updated, agent_result, heartbeat

---

## Gaps conhecidos (documentados em VALIDATION_W20)

| Gap | Prioridade |
|-----|-----------|
| Docker containers não iniciados | P1 — requer GO explícito |
| W18-B3 E2E com KRATOS | P1 — KRATOS Onda 3 |
| _render_clips() bug no AgenciaPipeline | P2 |
| KRATOS ArenaScreen fake financeiro hardcoded | P2 |

---

## Merge para master

```bash
# Master está bloqueado pelo worktree omnis-appfactory
# Quando liberar:
git checkout master
git merge --ff-only feature/omnis-w11-w20
```

---

**Branch:** `feature/omnis-w11-w20`
**Estado:** verde — aguardando merge para master

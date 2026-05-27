# MEGAPROMPT OMNIS EVOLUTION — W11-W20
# Branch: feature/omnis-w11-w20 | Base: 392 testes verdes

## DELTA REAL (auditado antes de executar)

| Item | Status |
|------|--------|
| FastAPI `src/api/main.py` | JÁ EXISTE — não duplicar |
| `LiteLLMAdapter` `src/agentic/llm_adapter.py` | JÁ EXISTE — reusar |
| `CostTracker` no grafo | JÁ EXISTE via finalize_node |
| `production_hardening/` | JÁ EXISTE — só wiring falta |
| `qdrant-client` em pyproject.toml | JÁ DECLARADO |
| `MarketingRouter` | FALTA CRIAR |
| Agentes de marketing | FALTAM |
| fastapi/uvicorn em pyproject.toml | FALTAM (instalados mas não declarados) |
| `sectors/` com agentes | NÃO EXISTE — criar `src/sectors/` |
| `omnis-server/` diretório separado | NÃO CRIAR — usar `src/api/` |

## WAVES

### W11 — Marketing Sector Acoplado
- Criar `src/sectors/marketing/` (não submodule)
- Reusar `src/marketing/models.py` existente
- Criar MarketingRouter + agentes stub
- Integrar nó marketing no mission_graph

### W12 — LiteLLM Gateway
- LiteLLMAdapter JÁ EXISTS — declarar `litellm` no pyproject.toml
- Docker compose config em `infra/litellm/`
- Foco: config + health check

### W13 — Qdrant Memória
- qdrant-client já declarado — criar collections setup
- `src/memory/qdrant_collections.py` + `src/memory/memory_client.py`

### W14 — omnis-server (ampliar src/api/)
- NÃO criar diretório novo — ampliar `src/api/main.py` existente
- Adicionar routers: /marketing, /sectors, /cost, /aurora
- Adicionar SSE /events

### W15 — n8n Bridge
- Docker setup
- Webhook receiver no FastAPI existente

### W16 — Multi-Agent Squads
- Squad orchestrator em `src/mission_graph/nodes/squad_orchestrator.py`
- Squads em `src/sectors/marketing/squads/`

### W17 — Obsidian Indexing (background)
- Script `scripts/index_obsidian.py`

### W18 — KRATOS Bridge (apenas lado OMNIS)
- Auth API key no FastAPI
- SSE broadcast
- NÃO tocar kratos-mission-control

### W19 — Production Hardening
- Docker compose completo `infra/docker-compose.prod.yml`
- Logging estruturado
- Budget guardrail

### W20 — Validação baseline utópico

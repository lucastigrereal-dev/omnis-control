# HANDOFF W11 — Marketing Sector acoplado ao grafo LangGraph

**Branch:** feature/omnis-w11-w20
**Commit:** adc14d9
**Data:** 2026-05-27
**Status:** COMPLETO ✅

---

## Arquivos criados

### Pacote setores
- `src/sectors/__init__.py` — pacote raiz dos setores do OMNIS
- `src/sectors/marketing/__init__.py` — setor marketing

### Tipos de missão
- `src/sectors/marketing/mission_types.py`
  - `MarketingMissionType` (Enum): CONTENT_PRODUCTION, LEAD_PROCESSING, WEEKLY_REVIEW, CAMPAIGN_STRATEGY
  - `MarketingMissionInput`: type, squad, priority, goal, deadline, inputs, model, page
  - `MarketingMissionOutput`: mission_id, status, outputs, cost_usd, tokens_used + model_dump()

### Agentes (stubs)
- `src/sectors/marketing/agents/__init__.py`
- `src/sectors/marketing/agents/base.py` — BaseMarketingAgent (model=haiku, NUNCA opus)
- `src/sectors/marketing/agents/content_agent.py` — ContentAgent (geração de copy)
- `src/sectors/marketing/agents/sdr_agent.py` — SDRAgent (qualificação de lead)

### Router
- `src/sectors/marketing/router.py` — MarketingRouter
  - SQUAD_MAP: instagram→[ContentAgent], comercial→[SDRAgent], growth→[ContentAgent, SDRAgent]
  - execute(input) → MarketingMissionOutput (agrega resultados de todos os agentes do squad)

### Nó do grafo
- `src/sectors/marketing/graph_node.py` — marketing_sector_node
  - Lê state["brief"] → cria MarketingMissionInput → executa MarketingRouter
  - Retorna artifacts acumulados + cost_usd + token_count
  - Guarda retorno de erro em state["error"] se brief.goal ausente

### Modificação: grafo principal
- `src/mission_graph/mission_graph.py`
  - Novo nó: `marketing_sector`
  - Nova função: `_route_after_plan(state)` — condicional em plan
  - Rota: plan → marketing_sector (se brief["sector"] == "marketing"), senão → execute
  - Aresta: marketing_sector → checkpoint (mesmo fluxo de finalize)

### Testes
- `tests/sectors/__init__.py`
- `tests/sectors/marketing/__init__.py`
- `tests/sectors/marketing/test_marketing_integration.py` — 12 testes

---

## Resultados dos testes

| Suite | Passed | Failed |
|---|---|---|
| tests/sectors/ | 12 | 0 |
| tests/mission_graph/ | 96 | 0 |
| tests/agencia/ + tests/publisher/ | 296 | 0 |

---

## Decisões técnicas

- **Stubs determinísticos:** nenhum agente faz chamada LLM — custo e tokens são fixos (0.001 USD, 100 tokens)
- **Guard model opus:** MarketingMissionInput.__post_init__ bloqueia model="opus" com ValueError
- **Routing limpo:** a lógica de roteamento fica em _route_after_plan() no mission_graph, não no plan_node
- **marketing_sector → checkpoint:** marketing bypassa execute/retry e vai direto para checkpoint → finalize
- **Reutilização:** src/marketing/models.py e src/marketing/service.py existentes não foram tocados

---

## Próximos passos (W12)

- W12: Setor Comercial (SDR + CRM) acoplado ao grafo — mesmo padrão de W11
  - src/sectors/comercial/: mission_types, agents (HotelAgent, LeadQualifierAgent), router, graph_node
  - Rota: plan → comercial_sector se brief["sector"] == "comercial"
- Alternativa: integrar MarketingRouter com src/commercial_sdr/ já existente
- Futuramente: substituir stubs por chamadas reais haiku via Anthropic SDK (com cache)

# OMNIS LEGO Architecture Report

**Gerado em:** 2026-05-18
**Branch:** master
**Status:** Provider Layer implementada e testada (74/74 testes)

---

## 1. O que estávamos reinventando

| O que | Onde | Por que é reinvenção |
|---|---|---|
| LocalTracer JSONL | `observability/tracer_local.py` | Langfuse/OTel fazem isso + cloud dashboard |
| MockHashEmbeddingProvider | `memory/embeddings.py` | SHA-256 não é semântica — SentenceTransformers existe |
| 5 orchestrators concorrentes | `mission_orchestrator/, runtime_orchestrator/, autonomous_execution/, skill_execution/, squad_execution/` | LangGraph faz tudo com StateGraph unificado |
| Memory Intel (611 linhas) | `memory_intel/service.py` | mem0 + pgvector resolvem isso nativamente |
| Memory Pack planning sem escrita | `memory_pack/service.py` | 512 linhas de dry-run sem persistência real |
| Tool Registry JSONL manual | `tool_registry/registry.py` | FastMCP tem discovery nativo via MCP protocol |

---

## 2. O que já existia melhor (e ignoramos)

| Área | Já existia | Impacto |
|---|---|---|
| Tracing cloud | Langfuse (gratuito up to 50k traces/mês) | Zero cloud observability atual |
| Vector embeddings | SentenceTransformers, OpenAI ada, text-embedding-3 | Similarity search inútil com SHA-256 |
| Stateful workflows | LangGraph (checkpoints, HITL, retry) | 5 orquestradores sem checkpoint |
| Memory CRUD | mem0 (multi-user, persistence, semantic) | Nosso writeback é apenas plano |
| MCP protocol | FastMCP + official MCP servers | Tool registry não é MCP real |

---

## 3. O que foi absorvido (implementado nesta sprint)

### Provider Layer — `src/providers/`

| Provider | Backend padrão | Backend opcional | Testes |
|---|---|---|---|
| `TracingProvider` | `LocalJSONLProvider` | `LangfuseProvider` | 15 |
| `MemoryProvider` | `LocalMemoryProvider` | `HybridMemoryProvider` | 17 |
| `WorkflowProvider` | `SequentialWorkflowProvider` | LangGraphProvider (futuro) | 9 |
| `MCPProvider` | `LocalToolRegistryProvider` | FastMCPProvider (futuro) | 10 |
| `RuntimeProvider` | `MockRuntimeProvider` | `SubprocessRuntimeProvider` | 14 |
| `ProviderRegistry` | `registry.default()` | `registry.production()` | 9 |

**Total:** 74/74 testes passando

---

## 4. O que deve continuar proprietário (MANTER)

| Componente | Por que manter |
|---|---|
| ExecutionGraph (DAG) | Lógica de negócio específica do OMNIS |
| RuntimeBridge | Mapeia nosso StepRun → QueueItem (26 testes) |
| Mission models | OrchestratorRun, SquadTask — modelo de dados proprietário |
| SkillRouter | Lógica de roteamento por intent é nosso diferencial |
| Checkers (health, docker, disk) | Checks específicos do ecossistema OMNIS |
| Business logic dos setores | MIDIA, COMERCIAL, VENDAS — regras de negócio |
| omnis_health server | Health endpoint canônico |

---

## 5. O que deve virar provider (ADAPTAR)

| Componente atual | Provider | Backend alvo |
|---|---|---|
| `observability/tracer_local.py` | `TracingProvider` | `LangfuseProvider` (já implementado, aguarda credencial) |
| `memory/embeddings.py` MockHash | `MemoryProvider` | `HybridMemoryProvider(Akasha, Mem0)` |
| `mission_orchestrator/` | `WorkflowProvider` | `LangGraphProvider` (fase 2) |
| `tool_registry/` | `MCPProvider` | `FastMCPProvider` (fase 3) |
| `runners/skill_runner.py` | `RuntimeProvider` | `SubprocessRuntimeProvider` (já implementado) |

---

## 6. O que deve ser removido (SUBSTITUIR)

| Componente | Motivo | Prazo |
|---|---|---|
| `observability/tracer_local.py` | Substituído por `LocalJSONLProvider` | Após validação TracingProvider |
| `memory_pack/` (512 linhas dry-run) | Nunca persistiu — sem valor real | Após MemoryProvider com Akasha |
| `runtime_orchestrator/` | Duplicata de `mission_orchestrator/` | Após WorkflowProvider unificado |
| `MockHashEmbeddingProvider` | SHA-256 não é semântica | Imediato (usar real embeddings) |

---

## 7. O que é hype (NÃO USAR)

| Tecnologia | Por que evitar |
|---|---|
| OpenAI Agents SDK | Lock-in total em um provider |
| CrewAI como núcleo | Instável, muda API a cada versão |
| Chroma como fundação | Supera Qdrant sem razão clara, lock-in |
| "Swarm AGI mágico" | Marketing > substância |
| LangChain direto no core | Vulnerabilidades recentes + API instável |

---

## 8. Stack recomendado (validado)

```
OBSERVABILIDADE:  Langfuse + OpenTelemetry → TracingProvider
MEMÓRIA:          mem0 + pgvector + Qdrant  → MemoryProvider (HybridMemoryProvider)
MCP:              FastMCP + official servers → MCPProvider
WORKFLOW:         LangGraph (stateful)       → WorkflowProvider (fase 2)
RUNTIME:          FastMCP local              → RuntimeProvider (fase 3)
MODELOS:          Claude via Anthropic SDK   → já implementado
GUARDRAILS:       NeMo (experimental)        → avaliar antes de adotar
```

---

## 9. Roadmap incremental

### Fase 1 (DONE — esta sprint)
- [x] Provider base protocol
- [x] TracingProvider (Local + Langfuse fallback)
- [x] MemoryProvider (Local + Hybrid)
- [x] WorkflowProvider (Sequential)
- [x] MCPProvider (LocalRegistry)
- [x] RuntimeProvider (Mock + Subprocess)
- [x] ProviderRegistry (default + production)
- [x] 74 testes

### Fase 2 — Langfuse real (1 dia)
- [ ] Configurar LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY
- [ ] Instrumentar 1 fluxo crítico (omnis doctor ou first_missions)
- [ ] Validar trace_id, duration_ms, cost no dashboard

### Fase 3 — MemoryProvider real (2 dias)
- [ ] AkashaProvider (PostgreSQL + pgvector)
- [ ] Substituir MockHashEmbeddingProvider
- [ ] Ligar HybridMemoryProvider(Akasha, LocalMemory)

### Fase 4 — WorkflowProvider LangGraph (3 dias)
- [ ] LangGraphProvider com StateGraph
- [ ] Migrar 1 orchestrator (mission_orchestrator) para LangGraphProvider
- [ ] Checkpointing básico

### Fase 5 — MCPProvider FastMCP (2 dias)
- [ ] FastMCPLocalProvider com stdio
- [ ] Expor skill_runner como MCP tool
- [ ] Registrar filesystem + git MCP servers

---

## 10. Ganhos rápidos (menos de 1 dia cada)

1. **Ativar Langfuse** — apenas variáveis de ambiente → cloud tracing imediato
2. **Usar ProviderRegistry.default()** em qualquer módulo novo → sem lock-in
3. **Substituir MockHashEmbedding** por `sentence-transformers` (pip install, 3 linhas)
4. **Consolidar runtime_orchestrator e mission_orchestrator** → usar SequentialWorkflowProvider
5. **Expor omnis doctor via MCPProvider** → tool de health disponível via MCP

---

## 11. Riscos

| Risco | Severidade | Mitigação |
|---|---|---|
| LangGraph API muda | MÉDIO | Isolar em WorkflowProvider — core não importa LangGraph |
| Langfuse custo em escala | BAIXO | Fallback local sempre disponível |
| mem0 timeout/falha | BAIXO | HybridMemoryProvider com fallback local |
| FastMCP não suporta Windows stdio | MÉDIO | Testar antes de adotar em prod |
| LangChain vulnerabilidades | ALTO | Nunca usar LangChain diretamente — apenas LangGraph isolado via provider |

---

## 12. Próximo passo único

**Configurar Langfuse** (ação externa — Lucas):
1. Criar conta em cloud.langfuse.com (gratuito)
2. Setar no ambiente: `LANGFUSE_PUBLIC_KEY` e `LANGFUSE_SECRET_KEY`
3. Mudar `ProviderRegistry.default()` para `ProviderRegistry.production()` em 1 módulo
4. Executar `omnis doctor` e ver o trace no dashboard Langfuse

Depois: `pip install langfuse` e o `LangfuseProvider` já está pronto.

---

## Arquitetura final (diagrama)

```
┌─────────────────────────────────────────────────────────┐
│                    OMNIS Business Logic                  │
│  (missions, orchestrator, skills, health, app_factory)  │
└──────────────────────┬──────────────────────────────────┘
                       │ imports only Provider interfaces
┌──────────────────────▼──────────────────────────────────┐
│                  ProviderRegistry                        │
│           registry.get("tracing")                       │
│           registry.get("memory")                        │
│           registry.get("workflow")                      │
│           registry.get("mcp")                           │
│           registry.get("runtime")                       │
└──┬─────────────┬──────────────┬──────────────┬──────────┘
   │             │              │              │
   ▼             ▼              ▼              ▼
TracingP    MemoryP        WorkflowP       MCPProvider
   │             │              │              │
Local      Local+Hybrid   Sequential    LocalRegistry
Langfuse   Akasha+mem0    LangGraph     FastMCP
  OTel      Qdrant        Celery        Remote MCP
```

**OMNIS = kernel. Frameworks = peças substituíveis.**

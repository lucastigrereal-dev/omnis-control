# Migração Política de Roteamento v2.0 → v2.1 Quality-First

**Data:** 2026-05-27 | **Branch:** `feature/omnis-w11-w20`

## Decisão

**Quality-First > Economy-First.** A v2.0 (Ollama-First) usava modelos locais leves (llama3.2:3b, llama3.1:8b) priorizando custo zero. A v2.1 migra para 6 modelos Ollama Pro Cloud premium — mesma assinatura $20/mês, qualidade superior comprovada em benchmarks.

- 🔗 **Política v2.1:** https://www.notion.so/36d22eba8f088199a2d6cf5a7e958cee
- 🔗 **Benchmarks:** https://www.notion.so/36d22eba8f08815b9b29c5de05d032fb

---

## Stack v2.1

| Nome lógico | Modelo | Uso principal |
|-------------|--------|---------------|
| `ollama-fast` | glm-5.1:cloud | Operação/volume (~70% chamadas) |
| `ollama-code` | kimi-k2.6:cloud | Código, SDR, conversação |
| `ollama-build` | minimax-m2.7:cloud | App Factory builds |
| `ollama-smart` | deepseek-v4-pro:cloud | Raciocínio profundo |
| `ollama-longctx` | minimax-m2.7:cloud | RAG, Akasha, docs longos |
| `ollama-backup` | qwen3.5:397b:cloud | Fallback geral |

**Anthropic:** comentado na config (desativado). Reativar adicionando ANTHROPIC_API_KEY ao .env.

---

## Tabela Antes/Depois — 12 Agentes

| Agente | v2.0 | v2.1 | Observação |
|--------|------|------|------------|
| Secretaria | ollama-fast (llama3.2:3b) | ollama-fast (glm-5.1:cloud) | Modelo trocado |
| Operacional | ollama-fast | ollama-fast (glm-5.1) | Modelo trocado |
| Conteudo | ollama-fast | ollama-fast (glm-5.1) | Modelo trocado |
| Design | ollama-fast | ollama-fast (glm-5.1) | Modelo trocado |
| SDR | ollama-fast | **ollama-code (kimi-k2.6)** | ⚠️ MUDOU |
| Arquivo | ollama-fast | ollama-fast (glm-5.1) | Modelo trocado |
| Performance | ollama-smart | ollama-smart (deepseek-v4-pro) | Mantido |
| Inteligencia | ollama-smart | ollama-smart (deepseek-v4-pro) | Mantido |
| SprintOrchestrator | ollama-fast | ollama-fast (glm-5.1) | Modelo trocado |
| Aurora | ~~ollama-smart~~ | **ollama-code (kimi-k2.6)** | ⚠️ MUDOU |
| AppFactory | ~~ollama-code~~ | **ollama-build (minimax-m2.7)** | ⚠️ MUDOU |
| ACaixa | (não existia) | **ollama-longctx (minimax-m2.7)** | ⚠️ NOVO |

---

## Justificativa Mudanças Críticas

**SDR → kimi-k2.6:** Análise de leads requer compreensão contextual de perfis de hotéis/restaurantes. kimi-k2.6 supera llama3.2:3b em tarefas de raciocínio sobre dados estruturados.

**Aurora → kimi-k2.6:** Aurora é interface de conversação/interpretação — não precisa do poder de deepseek-v4-pro (custo superior), mas precisa ser mais fluente que glm-5.1.

**AppFactory → minimax-m2.7:** Geração de código completo (PRD→scaffold→testes) exige modelo dedicado a builds. minimax-m2.7 tem contexto longo nativo, essencial para scaffolding multi-arquivo.

**ACaixa (novo):** Papel de RAG/indexação Akasha justifica modelo de contexto longo dedicado. minimax-m2.7 reaproveitado (mesma instância ollama-build, alias separado).

---

## Fallback Chain v2.1

```
ollama-fast    → [ollama-backup]
ollama-code    → [ollama-backup]
ollama-build   → [ollama-code]
ollama-smart   → [ollama-code]
ollama-longctx → [ollama-smart]
ollama-backup  → []
```

---

## Arquivos Modificados

| Arquivo | Mudança |
|---------|---------|
| `infra/litellm/litellm_config.yaml` | 6 modelos cloud, api_base → ollama.com, Anthropic comentado |
| `core/llm/router.py` | NOVO — TaskType enum + route() + validate_model() |
| `core/agents/config.py` | NOVO — 12 agentes com default_model |
| `src/agentic/model_validator.py` | ALLOWED_MODELS expandido, gpt-4/gpt-5 bloqueados |
| `CLAUDE.md` | Política v2.1 substituída |

*Gerado por OMNIS Control — Migração v2.1 · 2026-05-27*

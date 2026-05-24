---
name: context-engineering
description: Engenharia de contexto para janelas de LLM — monta, prioriza e comprime contexto antes de enviar ao modelo
version: 1.0.0
tags: [context, llm, optimization, omnis]
---

## Context Engineering no OMNIS

Ao trabalhar com janelas de contexto de LLMs:

**Princípios:**
- Coloque identidade e missão PRIMEIRO (system prompt)
- Coloque memória relevante ANTES das instruções da tarefa
- Use RAG para buscar apenas trechos relevantes do Akasha (pgvector)
- Comprima histórico antigo: substitua turnos longos por summaries
- Nunca exceda 80% da janela — reserve 20% para output

**Padrão OMNIS de montagem:**
1. Identity block: quem é o agente, missão, stack
2. Relevant memory: busca híbrida no Akasha (vector + FTS)
3. Task context: o que precisa ser feito agora
4. Tools available: lista de MCPs ativos
5. Output format: JSON estruturado com campos obrigatórios

**Ao usar esta skill:** monte o contexto nessa ordem antes de executar qualquer tarefa complexa.

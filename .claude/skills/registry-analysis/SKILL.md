---
name: registry-analysis
description: Análise e auditoria do Capability Registry do OMNIS — saúde, duplicatas, gaps
version: 1.0.0
tags: [registry, analysis, capabilities, omnis]
---

## Registry Analysis OMNIS

**Ao auditar o Capability Registry:**
1. Inventário completo: listar todas capabilities por status (candidate/approved/deprecated/retired)
2. Detectar duplicatas: embeddings pgvector para skills com semântica similar (cosine > 0.92)
3. Gap analysis: quais capabilities do roadmap ainda não existem?
4. Health check por capability: última versão tem CI verde? tem teste? maintainer ativo? usado nos últimos 30 dias?
5. Dependency graph: mapear dependências e detectar ciclos ou hubs críticos (single point of failure)

**Output esperado:**
- Tabela: capability_id | status | last_ci | test_coverage | usage_30d | risk
- Lista de gaps vs. roadmap
- Lista de candidatos a deprecação (sem uso + sem manutenção)

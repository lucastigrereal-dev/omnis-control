---
name: architecture-review
description: Review de arquitetura de módulos, adapters e integrações do OMNIS
version: 1.0.0
tags: [architecture, review, design, omnis]
---

## Architecture Review OMNIS

Ao revisar ou propor mudanças arquiteturais:

**Princípios invioláveis:**
- Adapter-first: toda integração via adapter desacoplado
- Capability-first: funcionalidade exposta via registry, não hardcoded
- Docker obrigatório para execução de capabilities
- PostgreSQL/Akasha como fonte de verdade
- MCP ecosystem compatibility
- Local-first sempre que possível

**Perguntas obrigatórias em qualquer review:**
1. Isso cria lock-in em serviço externo? Se sim, tem adapter de fallback?
2. Qual o impacto se este componente falhar? Tem circuit breaker?
3. Está registrado no Capability Registry?
4. Tem observabilidade (logs estruturados + métricas)?
5. É testável isoladamente (unit test possível)?

**Red flags arquiteturais:**
- Chamadas diretas entre módulos sem interface
- Config hardcoded no código
- Estado compartilhado sem controle de concorrência
- Dependência de serviço único sem fallback

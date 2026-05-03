# PRÓXIMOS PASSOS — OMNIS

> Fases 1, 2A, 2B e 2C concluídas. Abaixo o roadmap planejado para as próximas fases.

## Fase 3 — OAuth Meta + Publisher OS ⬅️ PRÓXIMO

- Configurar `META_APP_SECRET` no `.env` do publisher-os
- Rodar fluxo OAuth: `python scripts/oauth_setup.py url`
- Autorizar no Facebook e trocar code por token
- Validar token com `python scripts/oauth_setup.py accounts`
- Conectar Content Queue ao agendamento real do Publisher OS

## Fase 3 — OAuth Meta + Publisher OS

- Configurar `META_APP_SECRET` no `.env` do publisher-os
- Rodar fluxo OAuth: `python scripts/oauth_setup.py url`
- Autorizar no Facebook e trocar code por token
- Validar token com `python scripts/oauth_setup.py accounts`
- Conectar Content Queue ao agendamento real do Publisher OS

## Fase 4 — Memória Conectada

- Obsidian: leitura estruturada do vault (read-only primeiro)
- Qdrant: search semântico nas coleções existentes
- Akasha: descoberta segura do schema
- Integração: Obsidian ↔ Qdrant ↔ skills ↔ CLI

## Fase 5 — Saneamento Docker

- Auditoria de imagens, volumes e networks não utilizados
- Identificar containers unhealthy (crm-tigre-backend, jarvis_frontend)
- Não executar prune sem backup e aprovação
- Recuperar espaço em disco

## Fase 6 — Runtime Agentic

- LangGraph para orquestração de multi-agentes
- Tool router com validação de entrada/saída
- Critic loop para auto-correção
- Browser automation (sandboxado)
- Sandbox para execução segura de código

## Fase 7 — CrewAI Integration

- Integração com crews existentes do Publisher OS
- Coordenação entre skills e crews
- Fila de tarefas com priorização

## Fase 8 — Monetização Ativa

- Pipeline de produção com approval gate
- Agendamento inteligente por perfil
- Métricas de engajamento e ROI
- Faturamento e cobrança

---

## Já concluído

| Fase | O que entregou | Testes |
|------|---------------|--------|
| Fase 1 | Cabine mínima: CLI, checkers, logs, reports | 53 |
| Fase 1.1 | Diagnóstico + Fase E + 7 E2E | +61 |
| Fase 2A | Video Asset Registry: CRUD, scan, estados, fila | +53 |
| Fase 2B | Account Mapping + Content Queue: contas, fila, assign, export | +38 |
| **Fase 2C** | **Caption Draft + Approval Gate: rascunho, revisão, aprovação, templates** | **+49** |
| **Fase 2D** | **Batch captions: 41 drafts criados + submetidos para revisão** | **—** |
| **Total** | | **201** ✅ |

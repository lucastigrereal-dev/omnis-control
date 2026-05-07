# P0.9.1 RISK REGISTER

**Data:** 2026-05-07

| ID | Risco | Módulo | Gravidade | Probabilidade | Impacto | Recomendação | Corrigir em |
|---|---|---|---|---|---|---|---|
| R1 | CLI inchado (2.001 linhas, 18 apps) | src/cli.py | medium | high | Manutenção difícil, merge conflicts | Extrair apps restantes para cli_commands/ | P1.0 |
| R2 | JSONL sem locking concorrente | metrics, missions | medium | low | Corrupção de dados sob carga | Documentar single-writer; migrate se necessário | P2.0+ |
| R3 | Observability vs Metrics sobreposição | observability, metrics | low | low | Confusão de nomenclatura | Documentar distinção (metrics_spine vs metrics/) | P1.0 |
| R4 | PipelineResult duplicado | pipeline_local | low | low | Código morto, manutenção dupla | Consolidar PipelineRunResult → MissionPipelineResult | P1.0 |
| R5 | Tool Registry sem healthcheck real | tool_registry | medium | medium | Ferramentas marcadas erradas | Implementar healthcheck periódico (docker check) | P1.1 |
| R6 | Metrics Spine sem custo real | metrics | low | high | Métricas financeiras zeradas até OAuth | Aceitar — sem API = sem custo | P1.2+ |
| R7 | OAuth Meta bloqueado | instagram_graph_api | critical | high | Sem publicação real | Configurar META_APP_SECRET, rodar OAuth | P1.1 |
| R8 | Disco C:\ crítico (8.6% livre) | infra | critical | high | Sistema para se disco lotar | Limpeza de arquivos, docker prune | Imediato |
| R9 | 2 containers unhealthy | Docker | medium | high | Serviços degradados (CRM, Jarvis FE) | Investigar healthcheck, reiniciar se necessário | Imediato |
| R10 | Qdrant inacessível | memory | medium | medium | Busca vetorial offline | Verificar container/porta Qdrant | P1.0 |
| R11 | Publisher OS porta fechada | publisher | medium | medium | Publisher local offline | Verificar serviço publisher-core | P1.0 |
| R12 | LangGraph não implementado | orchestration | low | low | Sem orchestrator multi-agente | Planejar após DISK-1 estável | P2.0 |
| R13 | Capability Forge proposal-only | security | low | low | Sem policy engine ativa | Ativar quando houver ações reais | P2.0 |
| R14 | 40 caption drafts stale (needs_review) | caption_approval | medium | medium | Fila de aprovação parada | Rodar approvals batch | Imediato |

## Resumo por gravidade

| Gravidade | Quantidade |
|---|---|
| critical | 2 (R7 OAuth, R8 Disco) |
| high | 0 |
| medium | 6 |
| low | 6 |

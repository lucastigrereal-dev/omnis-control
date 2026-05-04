# Diagnóstico Operacional — Fase 0 (Redacted)

**Data:** 2026-05-04
**Nota:** Versão sanitizada para commit. Sem valores sensíveis.

---

## Resumo

| Indicador | Valor |
|---|---|
| Disco | CRÍTICO (7.4% livre) |
| Containers saudáveis | 16/18 |
| Publisher OS | offline |
| Qdrant | inacessível |
| Akasha | OK |
| Contas IG cadastradas | 2/6 |
| Slots na fila | 42 (95% sem asset) |
| Aprovados | 1/42 |
| Saúde | 31/100 |

## Bloqueios

1. Disco crítico — risco de falha em operações de vídeo/build
2. Publisher :8000 sem resposta — produção de conteúdo bloqueada
3. Qdrant inacessível — memória semântica quebrada
4. OAuth Meta pendente — publicação real impossível
5. 4/6 contas IG não cadastradas
6. 40/42 slots sem asset — fila vazia

## Ações Sugeridas (pendentes de aprovação)

- `docker image prune` / `docker builder prune` — liberar ~70 GB
- `docker stop` containers unhealthy (crm-tigre-backend, jarvis_frontend)
- Cadastrar 4 contas IG faltantes no Account Registry
- Aprovar drafts pendentes via `omnis approvals batch`

## Próximas Fases

- Fase 1: Skill manifests + validação (não depende de infra)
- Fase 2: n8n workflow spec exportável (não depende de infra)

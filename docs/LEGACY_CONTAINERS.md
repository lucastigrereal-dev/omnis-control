# Inventário de Containers — OMNIS

**Data:** 2026-05-03
**Propósito:** Classificar containers do Docker em ativos, legados e desconhecidos.

---

## Containers Saudáveis

| Container | Classificação | Justificativa |
|-----------|--------------|---------------|
| publisher-os-publisher-core | ✅ Ativo | Motor do Publisher OS |
| publisher-os-litellm | ✅ Ativo | Gateway de LLMs |
| publisher-os-n8n | ✅ Ativo | Automação de workflows |
| publisher-os-publish-worker | ✅ Ativo | Worker de publicação |
| open-webui | ✅ Ativo | Interface Open WebUI |
| publisher-os-redis | ✅ Ativo | Cache/fila do Publisher OS |
| publisher-os-qdrant | ✅ Ativo | Vector DB (Qdrant) |
| publisher-os-supabase-db | ✅ Ativo | DB do Publisher OS |
| publisher-os-minio | ✅ Ativo | Object storage |
| akasha-postgres | ✅ Ativo | Base Akasha pgvector |
| crm-tigre-frontend | ✅ Ativo | CRM frontend |
| crm-tigre-redis | ✅ Ativo | Cache do CRM |
| crm-tigre-postgres | ✅ Ativo | DB do CRM |
| aurora_redis | ✅ Ativo | Redis da Aurora |
| jarvis_executor_api | ✅ Ativo | API executora Jarvis |

---

## Containers Unhealthy

### 1. `crm-tigre-backend`
| Campo | Valor |
|-------|-------|
| Status | 🔴 Unhealthy (Up 9 dias) |
| Classificação | 📦 Legado (ativo mas não crítico) |
| Provável causa | Health check configurado e falhando, mas app pode estar funcionando |
| Risco | Baixo — frontend está saudável |
| Ação | Documentar apenas nesta fase |

### 2. `jarvis_frontend`
| Campo | Valor |
|-------|-------|
| Status | 🔴 Unhealthy (Up 9 dias) |
| Classificação | 📦 Legado (nome confuso) |
| Provável causa | Health check falhando ou app antigo sem manutenção |
| Risco | Médio — nome sugere que era interface do Jarvis antigo |
| Ação | Investigar se ainda é usado. Se não for, planejar desligamento. |

---

## Decisões

1. **Não desligar nada agora** — todos os containers podem ser necessários.
2. **Criar diagnóstico** de health check para entender por que `crm-tigre-backend` e `jarvis_frontend` estão unhealthy.
3. **Futuro:** Quando `mission_control` estiver maduro, avaliar se `jarvis_frontend` pode ser desligado.

---

## Comandos de Diagnóstico

```bash
# Ver health check config
docker inspect crm-tigre-backend --format '{{json .Config.Healthcheck}}'
docker inspect jarvis_frontend --format '{{json .Config.Healthcheck}}'

# Ver logs
docker logs crm-tigre-backend --tail 20
docker logs jarvis_frontend --tail 20
```

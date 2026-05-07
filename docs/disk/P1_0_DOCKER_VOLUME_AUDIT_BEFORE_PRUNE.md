# P1.0 DISK-1 — Docker Volume Audit (Read-Only)

**Data:** 2026-05-07 17:36 UTC-3
**Antes de qualquer `docker volume prune`**

---

## Resumo

| Métrica | Valor |
|---|---|
| Total volumes | 42 |
| Volumes em uso (links > 0) | 9 |
| Volumes órfãos (links = 0) | 33 |
| Espaço total em órfãos | **~10.6 GB** |
| Recomendação | **NÃO fazer prune cego** |

---

## Volumes em uso (NÃO TOCAR)

| Volume | Tamanho | Container |
|---|---|---|
| akasha_akasha_pgdata | 12.44 GB | akasha-postgres |
| publisher-os_open_webui_data | 1.12 GB | open-webui |
| publisher-os_publish_worker_whatsapp_session | 0 B | publish-worker-1 |
| crm-tigre_postgres_data | 49.64 MB | crm-tigre-postgres |
| crm-tigre_redis_data | 58.30 MB | crm-tigre-redis |
| crm-tigre_backend_uploads | 0 B | crm-tigre-backend |
| crm-tigre_backend_logs | 0 B | crm-tigre-backend |
| ollama-executor_postgres_data | 47.81 MB | jarvis_postgres |
| ea03bd... (hash) | 88 B | publish-worker-1 |

---

## Volumes órfãos — Classificados

### GRUPO A: publisher-os (sistema parado, NÃO remover)

O docker-compose do Publisher OS está parado. Seus volumes são órfãos porque os containers foram stopped. Um `docker compose up` reativaria tudo.

| Volume | Tamanho | Risco de remover |
|---|---|---|
| publisher-os_ollama_data | 4.96 GB | ALTO — modelos Ollama do publisher |
| publisher-os_qdrant_data | 1.57 GB | ALTO — Qdrant com dados de memória |
| publisher-os_supabase_db_data | 58.07 MB | ALTO — banco Supabase do publisher |
| publisher-os_langfuse_db_data | 47.45 MB | MÉDIO — tracing Langfuse |
| publisher-os_redis_data | 0.54 MB | BAIXO — cache Redis |
| publisher-os_minio_data | 0.02 MB | BAIXO — storage Minio |
| publisher-os_n8n_data | 5.72 MB | MÉDIO — workflows n8n |

**Veredito: MANTER.** Sistema principal de produção. Parado, não abandonado.

### GRUPO B: SDR Aurora (projeto parado)

| Volume | Tamanho | Risco |
|---|---|---|
| sdr_aurora_postgres_data | 84.09 MB | MÉDIO — banco do SDR |
| sdr_aurora_n8n_data | 2.14 kB | BAIXO |
| sdr_aurora_evolution_instances | 0 B | BAIXO |

**Veredito: MANTER.** Projeto secundário, pode ter dados de leads.

### GRUPO C: SDR Premium (projeto parado)

| Volume | Tamanho | Risco |
|---|---|---|
| sdr_premium_postgres_data | 75.02 MB | MÉDIO |
| sdr_premium_redis_data | 264 B | BAIXO |
| sdr_premium_n8n_data | 123 B | BAIXO |
| sdr_premium_evolution_data | 0 B | BAIXO |

**Veredito: MANTER.**

### GRUPO D: casa-segura (projeto parado)

| Volume | Tamanho | Risco |
|---|---|---|
| casa-segura_postgres_data | 104.90 MB | MÉDIO |
| casa-segura_redis_data | 1.86 kB | BAIXO |

**Veredito: MANTER.**

### GRUPO E: verso-genius-app (projeto parado)

| Volume | Tamanho | Risco |
|---|---|---|
| verso-genius-app_postgres_data | 47.74 MB | MÉDIO |
| verso-genius-app_redis_data | 264 B | BAIXO |

**Veredito: MANTER.**

### GRUPO F: clinical_staging (projeto parado)

| Volume | Tamanho | Risco |
|---|---|---|
| clinical_staging_pgdata | 47.93 MB | MÉDIO |
| clinical_staging_grafana | 42.29 MB | BAIXO |
| clinical_staging_prometheus | 18.06 MB | BAIXO |
| clinical_staging_redis | 0 B | BAIXO |

**Veredito: MANTER.**

### GRUPO G: Hash volumes (origem desconhecida)

| Volume | Tamanho | Possível origem |
|---|---|---|
| 7c0f9322... | 2.24 GB | Imagem/container antigo, build cache |
| daa91984... | 72.08 MB | Build context ou DB antigo |
| f42f8cc2... | 47.77 MB | DB ou cache antigo |
| 66cfd703... | 167 B | Mínimo |
| 46a7f809... | 1.06 kB | Mínimo |
| 9184d860... | 0 B | Vazio |

**Veredito: INVESTIGAR.** O volume de 2.24 GB pode ser lixo ou dado útil. Auditar com `docker run --rm -v` antes de decidir.

### GRUPO H: n8n_data / prometheus_n8n_data / ollama-executor_n8n_data

| Volume | Tamanho |
|---|---|
| n8n_data | 0.59 MB |
| prometheus_n8n_data | 13.48 MB |
| ollama-executor_n8n_data | 0 B |
| ollama-executor_ollama_data | 0 B |
| ollama-executor_redis_data | 264 B |

**Veredito: BAIXO RISCO.** Volumes pequenos de projetos parados.

---

## Veredito Final

**NÃO executar `docker volume prune -f`.**

Motivos:
1. **33 volumes órfãos, mas NENHUM é claramente lixo.** Todos pertencem a projetos conhecidos que estão parados, não abandonados.
2. **Publisher OS** representa 6.6 GB dos 10.6 GB órfãos — é o sistema de produção principal, só está com containers parados.
3. Os volumes hash (2.24 GB + 72 MB) são os únicos candidatos a limpeza, mas precisam de inspeção antes.
4. **Ganho real de um prune seguro seria ~3-4 GB** (excluindo publisher-os e projetos conhecidos). Não resolve o problema crítico de disco.

### Recomendação

1. **Reativar Publisher OS** (`docker compose up -d` no `~/publisher-os`) — os volumes reconectam e deixam de ser órfãos.
2. **Inspecionar volume hash de 2.24 GB** (`7c0f9322...`) — se for lixo, remover manualmente.
3. **Para projetos abandonados** (clinical_staging, casa-segura, verso-genius): decidir se mantém ou faz backup + remoção.
4. **Disco segue crítico a 9.6%** — a solução real é expandir armazenamento ou mover assets (Desktop 58 GB) para HD externo.

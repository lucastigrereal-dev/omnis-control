# DISK-1 Audit Plan — Creative Production OS

## Contexto

DISK-0 (read-only) identificou ~70 GB reclaimável em Docker.
DISK-1 adiciona verificação de integridade do novo módulo Creative Production OS.

## 1. Docker — Whitelist de Reclaim Candidates

### Imagens para reter (uso ativo)

| Imagem | Container | Uso |
|--------|-----------|-----|
| publisher-os-publisher-core | publisher-core-1 | Core Publisher OS |
| ghcr.io/berriai/litellm:main-latest | litellm-1, litellm-2 | LLM Gateway |
| docker.n8n.io/n8nio/n8n | n8n-1 | Workflow automation |
| publisher-os-publish-worker | publish-worker-1 | Worker fila |
| ghcr.io/open-webui/open-webui | open-webui | Chat UI |
| redis:latest | redis-1 | Publisher OS cache |
| qdrant/qdrant | qdrant-1 | Vector DB |
| supabase/postgres:15.1.0.14 | supabase-db-1 | Publisher DB |
| minio/minio | minio-1 | Object storage |
| pgvector/pgvector:pg16 | akasha-postgres | Akasha DB |
| crm-tigre-backend | crm-tigre-backend | CRM (unhealthy) |
| crm-tigre-frontend | crm-tigre-frontend | CRM frontend |
| redis:7-alpine | crm-tigre-redis, aurora_redis, jarvis_postgres | Redis aux |
| postgres:15-alpine | crm-tigre-postgres, jarvis_postgres | DBs aux |
| ollama-executor-executor-api | jarvis_executor_api | Executor |
| ollama-executor-frontend | jarvis_frontend | Jarvis UI (unhealthy) |

### Imagens reclaimáveis (sem container ativo)

| Imagem | Tamanho | Risco | Ação |
|--------|---------|-------|------|
| `supabase/postgres:15.1.0.14` | 9.57 GB | **ALTO** — 1 container ativo (supabase-db-1) | **RETER** — está em uso |
| `ollama/ollama:latest` | 6.14 GB | BAIXO — sem container ativo | **Limpar** `docker rmi` |
| `ghcr.io/openclaw/openclaw:latest` | 6.21 GB | BAIXO — sem container ativo | **Limpar** `docker rmi` |
| `openclaw:local` | 3.94 GB | BAIXO — sem container ativo | **Limpar** `docker rmi` |
| `<none>:<none>` (dangling) | 1.4 GB | BAIXO | **Limpar** `docker image prune` |
| `n8nio/n8n:latest` | 1.64 GB | BAIXO — sem container (n8n usa docker.n8n.io) | **Limpar** `docker rmi` |
| `langfuse/langfuse:latest` | 1.36 GB | BAIXO — sem container | **Limpar** `docker rmi` |
| `postgres:15` | 633 MB | BAIXO — sem container (postgres:15-alpine em uso) | **Limpar** `docker rmi` |
| `atendai/evolution-api:latest` | 1.37 GB | BAIXO — sem container | **Limpar** `docker rmi` |
| `prom/prometheus:latest` | 518 MB | BAIXO — sem container | **Limpar** `docker rmi` |
| `grafana/grafana:latest` | 993 MB | BAIXO — sem container | **Limpar** `docker rmi` |
| `grafana/k6:latest` | 111 MB | BAIXO — sem container | **Limpar** `docker rmi` |
| `staging-backend-staging:latest` | 1.41 GB | BAIXO — sem container | **Limpar** `docker rmi` |
| `nvidia/cuda:12.0.0-base-ubuntu22.04` | 338 MB | BAIXO — sem container | **Limpar** `docker rmi` |
| `hello-world:latest` | 20 KB | BAIXO | **Limpar** `docker rmi` |

**Total reclaimável (imagens, exceto supabase):** ~25.5 GB

### Volumes reclaimáveis

| Volume | Tamanho | Risco | Ação |
|--------|---------|-------|------|
| `verso-genius-app_postgres_data` | 47.8 MB | BAIXO — sem container | **Limpar** |
| `clinical_staging_redis` | 0 B | BAIXO | **Limpar** |
| `sdr_aurora_evolution_instances` | 0 B | BAIXO | **Limpar** |
| `sdr_premium_evolution_data` | 0 B | BAIXO | **Limpar** |
| `sdr_premium_redis_data` | 264 B | BAIXO | **Limpar** |
| `verso-genius-app_redis_data` | 264 B | BAIXO | **Limpar** |
| `n8n_data` | 585.9 KB | BAIXO — sem container (projeto removido) | **Limpar** |
| `ollama-executor_postgres_data` | 47.8 MB | BAIXO — sem container (projeto removido) | **Limpar** |
| `7c0f932...` (anônimo) | 2.24 GB | BAIXO — volume órfão | **Limpar** |

**Total reclaimável (volumes):** ~2.3 GB

### Ordem de execução segura

1. `docker image prune` — limpa dangling (1.4 GB)
2. `docker rmi ollama/ollama` — 6.14 GB
3. `docker rmi ghcr.io/openclaw/openclaw` — 6.21 GB
4. `docker rmi openclaw:local` — 3.94 GB
5. `docker rmi n8nio/n8n` — 1.64 GB
6. `docker rmi langfuse/langfuse` — 1.36 GB
7. `docker rmi postgres:15` — 633 MB
8. `docker rmi atendai/evolution-api` — 1.37 GB
9. `docker rmi prom/prometheus grafana/grafana grafana/k6` — 1.62 GB
10. `docker rmi staging-backend-staging` — 1.41 GB
11. `docker rmi nvidia/cuda:12.0.0-base-ubuntu22.04` — 338 MB
12. `docker volume rm $(docker volume ls -qf dangling=true)` — ~2.3 GB

**Total estimado:** ~28.5 GB

### ⚠️ Riscos

- **supabase/postgres:15.1.0.14 (9.57 GB)** parece inativo mas TEM 1 container — NÃO limpar
- **crm-tigre-backend (2.36 GB)** está unhealthy desde Março — reter até decisão do operador
- **jarvis_frontend (81 MB)** unhealthy — reter (será consertado)
- NÃO executar `docker system prune -a` — muito agressivo, pode quebrar o ecossistema
- Cada `docker rmi` deve ser confirmado individualmente

## 2. Creative Production OS — Integridade

### Artefatos verificados

| Módulo | Arquivos | Status |
|--------|----------|--------|
| models.py | CreativeBrief, ProductionItem, CreativeReview dataclasses | ✅ |
| briefs.py | CRUD + JSONL + validação queue/caption | ✅ |
| production_queue.py | CRUD + JSONL + attach_asset | ✅ |
| review.py | approve, reject, is_ready_for_argos | ✅ |
| exporter.py | generate_export_package (13 artefatos) + backward compat | ✅ |
| html_renderer.py | render_preview_html (inline CSS, sem CDN) | ✅ |
| mock_image_generator.py | generate_mock_image (1080x1080 Pillow) | ✅ |

### CLI Commands

| Comando | Função | Status |
|---------|--------|--------|
| `creative status` | Status do módulo | ✅ |
| `creative list` | Lista briefs | ✅ |
| `creative show <id>` | Detalhes do brief | ✅ |
| `creative export-package --brief-id <id>` | Gera pacote | ✅ |

### Testes

- `tests/test_creative_production.py` — 20 testes (existente) ✅
- `tests/test_creative_production_export.py` — 8 testes (novos) ✅
- **Total: 28 testes, 319/319 suite completa** ✅

### Documentação

| Documento | Conteúdo |
|-----------|----------|
| `docs/creative/CREATIVE_PRODUCTION_AUDIT.md` | Auditoria completa (7 seções) |
| `docs/creative/CREATIVE_PRODUCTION_OS.md` | O que é, onde se encaixa |
| `docs/creative/CREATIVE_PRODUCTION_PIPELINE.md` | Pipeline 7 estágios |
| `docs/creative/CREATIVE_EXPORT_PACKAGE_CONTRACT.md` | Contrato dos 13 artefatos |

## 3. Ações Pós-DISK-1

### Commit pendente

- 14 arquivos alterados/criados (exporter.py, html_renderer.py, mock_image_generator.py, cli.py, creative_cmd.py, briefs.py, conftest.py, 2 test files, .gitignore, 4 docs)
- Mensagem: `feat(creative): Fase 2D — Export Package (13 artefatos) + CLI + 8 testes + DISK-1 audit`
- NO PUSH

### Próximas fases (não bloqueantes)

- Fase 7: Relatório final `docs/creative/RELATORIO_CREATIVE_PRODUCTION_OS_OFICIAL.md`
- Fase 8: Git commit

### Dívida técnica identificada

1. CLI `doctor` inclui 6 checks manuais + content_queue + caption_approval + argos_bridge — mas NÃO inclui creative_production. Adicionar creative_production ao doctor é melhoria futura.
2. `list_briefs()` não aceita filtro por status — adicionar quando necessário.
3. `generate_export_package()` com `include_html=False, include_mock_image=False` gera 10 arquivos apenas — contrato diz "mínimo 10", OK.

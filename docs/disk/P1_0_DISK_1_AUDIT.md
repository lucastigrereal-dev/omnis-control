# P1.0 DISK-1 — Auditoria de Disco (Read-Only)

**Data:** 2026-05-07 16:10 UTC-3
**Branch:** master
**Commit:** 74c88a8

---

## 1. Resumo do Disco

| Métrica | Valor |
|---|---|
| Disco | C:\ |
| Capacidade total | 924.3 GB |
| Usado | 844.9 GB |
| Livre | 79.4 GB |
| **% Livre** | **8.6%** (CRÍTICO) |

---

## 2. Top Diretórios — C:\Users\lucas

| Diretório | Tamanho | % do usado |
|---|---|---|
| Desktop | 58.19 GB | 6.9% |
| .ollama (modelos LLM) | 28.61 GB | 3.4% |
| _ORGANIZADO_POR_TIPO | 21.77 GB | 2.6% |
| .cache | 9.86 GB | 1.2% |
| Downloads | 8.26 GB | 1.0% |
| OneDrive | 4.80 GB | 0.6% |
| arquivos zip | 4.59 GB | 0.5% |
| .claude | 2.13 GB | 0.3% |
| .local (pipx, share) | 1.58 GB | 0.2% |
| clinical_companion_full4 | 1.32 GB | 0.2% |
| demais dirs | ~13 GB | 1.5% |

---

## 3. Docker

### Images (58.28 GB)

| Imagem | Tamanho | Em uso? |
|---|---|---|
| supabase/postgres:15.1.0.14 | 9.57 GB | 1 container (exited) |
| ghcr.io/open-webui/open-webui:main | 6.62 GB | 1 container |
| ghcr.io/openclaw/openclaw:latest | 6.21 GB | 0 containers |
| ollama/ollama:latest | 6.14 GB | 0 containers |
| publisher-os-publisher-core:latest | 5.92 GB | 1 container |
| ghcr.io/berriai/litellm:main-latest | 5.59 GB | 2 containers |
| openclaw:local | 3.94 GB | 0 containers |
| crm-tigre-backend:latest | 2.36 GB | 1 container |
| docker.n8n.io/n8nio/n8n:latest | 1.99 GB | 1 container |
| n8nio/n8n:latest (duplicada) | 1.64 GB | 0 containers |
| staging-backend-staging | 1.41 GB | 0 containers |
| \<none\> (dangling) | 1.40 GB | 0 containers |
| atendai/evolution-api | 1.37 GB | 0 containers |
| langfuse/langfuse | 1.36 GB | 0 containers |
| grafana/grafana | 0.99 GB | 0 containers |
| Outras 16 imagens | 3.85 GB | - |

**Reclaimable images: 32.32 GB (55%)**

### Containers

- 18 total, 11 running, 7 exited
- Exited: publisher-os-publisher-core-1, publisher-os-litellm-1, publisher-os-n8n-1, publisher-os-redis-1, publisher-os-qdrant-1, publisher-os-supabase-db-1, publisher-os-minio-1

### Volumes (23.14 GB)

| Volume | Tamanho | Em uso? |
|---|---|---|
| publisher-os_qdrant_data | 1.57 GB | 1 link |
| publisher-os_open_webui_data | 1.12 GB | 1 link |
| publisher-os_minio_data | 21 KB | 1 link |
| Volumes órfãos (sem links) | 7.80 GB | 0 links |

**Reclaimable volumes: 7.80 GB (33%)**

---

## 4. Caches de Desenvolvimento

| Cache | Tamanho | Detalhe |
|---|---|---|
| **pip cache** | **9.80 GB** | 3190 HTTP files em `AppData\Local\pip\cache` |
| .cache/whisper | 5.00 GB | Modelos Whisper (STT) |
| .cache/huggingface | 4.84 GB | Modelos HF |
| .bun cache | 0.45 GB | Bun package cache |
| .cache/chroma | 0.17 GB | ChromaDB embeddings |
| scoop cache | 0.06 GB | Scoop package cache |
| node_modules (daily-prophet) | 0.36 GB | npm dependencies |
| node_modules (publisher-cockpit) | 0.12 GB | npm dependencies |
| .pytest_cache (5 dirs) | 0.05 MB | Mínimo |
| __pycache__ (8816 dirs) | N/A | Distribuído, tipicamente < 10 MB total |
| npm cache (em `AppData\Local\npm-cache`) | N/A | Tamanho não medido |

---

## 5. Windows TEMP (C:\Users\lucas\AppData\Local\Temp)

Total: **~1.97 GB**

| Diretório/Padrão | Tamanho | Descrição |
|---|---|---|
| 118D18B7... (Squirrel) | 404.95 MB | Instalador residual |
| CapCut .rar.f73 | 374.76 MB | Download parcial |
| CapCut .rar.831 | 374.76 MB | Download parcial |
| DiagOutputDir | 224.51 MB | Diagnostic logs |
| ia-rimas-brasil | 99.37 MB | Projeto temp |
| verso-genius-final | 80.42 MB | Projeto temp |
| claude | 69.46 MB | Sessões Claude |
| docker-tar-extract1472426920 | 33.37 MB | Docker extract |
| CometInstaller | 31.74 MB | Instalador |
| openclaw_aurora_deploy | 25.08 MB | Deploy temp |
| Outros | ~250 MB | Diversos |

---

## 6. Recycle Bin

0.99 GB — seguro esvaziar.

---

## 7. Desktop (58.19 GB)

| Subdiretório | Tamanho |
|---|---|
| ARQUIVOS_MANUS_CLAUDE | 51.70 GB |
| ARQUIVO | 2.71 GB |
| TEMPLATES | 2.55 GB |
| MIDIAS | 1.72 GB |
| SÃO_PEDRO | 0.36 GB |
| Demais | ~0.50 GB |

---

## 8. Ollama Models (28.61 GB)

| Modelo | Blob | Tamanho |
|---|---|---|
| **deepseek-v4-pro:cloud (?) | sha256-065b... | **17.95 GB** |
| llama3.1:8b | sha256-667b... | 4.69 GB |
| qwen-coder-longctx-balanced | sha256-60e0... | 4.47 GB |
| qwen-coder-q5-recommended | (compartilha blob) | ~0 |
| qwen-coder-64k | (compartilha blob) | ~0 |
| qwen2.5-coder:7b | (compartilha blob) | ~0 |
| llama3.2:3b | sha256-dde5... | 1.93 GB |
| nomic-embed-text | sha256-970a... | 0.26 GB |

Nota: qwen-coder (4 variantes), qwen2.5-coder — todos compartilham o mesmo blob de 4.47 GB via hardlinks. Remover 1 remove as referências, mas o blob fica até o último.

---

## 9. Total Reclaimável (Estimativa Conservadora)

| Fonte | Reclaimable |
|---|---|
| Docker imagens não usadas | 32.32 GB |
| Docker volumes órfãos | 7.80 GB |
| Docker containers parados | 0.08 GB |
| pip cache | 9.80 GB |
| Windows TEMP (não-Claude) | ~1.50 GB |
| Recycle Bin | 0.99 GB |
| **TOTAL estimado** | **~52.5 GB** |

Potencial de recuperar disco de 8.6% → **~14% livre** (79 GB → ~131 GB).

# P1.0 DISK-1 — Relatório Final

**Data:** 2026-05-07 17:55 UTC-3
**Branch:** master
**Commit base:** 74c88a8

---

## Executado

| Fase | Ação | Resultado |
|---|---|---|
| Gate 0 | Verificação de estado | 3 snapshots descartados, working tree limpo |
| Phase 1 | Auditoria read-only | `docs/disk/P1_0_DISK_1_AUDIT.md` |
| Phase 2 | Classificação | `docs/disk/P1_0_DISK_CLEANUP_CANDIDATES.md` |
| Phase 3 | Comandos sugeridos | `docs/disk/P1_0_DISK_CLEANUP_COMMANDS_SUGGESTED_ONLY.md` |
| Phase 4 | Cleanup TIER 1 | 0.8 GB liberados |
| Phase 5 | Cleanup TIER 2 parcial | pip cache + docker image prune |
| Phase 6 | Volume audit | `docs/disk/P1_0_DOCKER_VOLUME_AUDIT_BEFORE_PRUNE.md` |
| Phase 7 | Testes finais | 604 passed, 2 skipped, 1 failed (pré-existente) |

---

## Disco — Progressão completa

| Momento | Livre | % | Delta |
|---|---|---|---|
| Antes de tudo | 79.4 GB | 8.6% | — |
| Após TIER 1 (safe) | 80.2 GB | 8.7% | +0.8 GB |
| Após pip cache purge | 80.2 GB | 8.7% | +0 GB (já estava limpo) |
| Após docker image prune -a | **88.8 GB** | **9.6%** | **+8.6 GB** |

---

## GB liberados por fonte

| Fonte | Liberado |
|---|---|
| TIER 1 combinado (.pytest_cache, __pycache__, containers, temp, scoop, recycle bin) | 0.8 GB |
| pip cache purge | 0 GB (cache já estava zerado ou foi limpo antes) |
| docker image prune -a (17 imagens removidas) | **14.09 GB** |
| Overlap com containers já removidos em TIER 1 | ~5.3 GB |
| **TOTAL líquido** | **~9.4 GB** |

Imagens removidas: openclaw (2), ollama/ollama, supabase/postgres antigo, redis extra, postgres extra, nginx, n8n duplicado, litellm, open-webui (parado), qdrant, prometheus, grafana, grafana/k6, langfuse, evolution-api, nvidia/cuda, staging-backend, python-core extra, mcp/playwright dangling, minio, hello-world.

---

## Docker volumes — Decisão

**`docker volume prune -f` NÃO executado.**

Auditoria completa em `docs/disk/P1_0_DOCKER_VOLUME_AUDIT_BEFORE_PRUNE.md`:

- 42 volumes totais, 33 órfãos (10.6 GB)
- **Nenhum volume é claramente lixo.** Todos pertencem a projetos conhecidos (parados, não abandonados)
- Publisher OS = 6.6 GB dos órfãos (sistema principal de produção, containers parados)
- Volumes hash (2.24 GB + 72 MB) são os únicos suspeitos — precisam de inspeção antes
- **Recomendação: NÃO fazer prune cego.**

---

## O que NÃO foi tocado

- `docker volume prune` — NÃO executado (auditoria recomenda contra)
- `docker system prune` — NÃO executado
- Desktop, Downloads, OneDrive, _ORGANIZADO_POR_TIPO
- Obsidian vault (ARQUIVOS_MANUS_CLAUDE, 51.7 GB)
- .ollama modelos ativos (28.6 GB)
- .cache/whisper + huggingface (9.8 GB)
- Akasha, Qdrant, Publisher OS, CRM, bancos Docker
- Projetos parados com volumes (sdr_aurora, sdr_premium, casa-segura, verso-genius, clinical_staging)

---

## Recomendação final

Disco saiu de 8.6% → 9.6%. Ainda crítico, mas respirando.

**Próximos passos para resolver o disco de vez:**

1. **Reativar Publisher OS** — `docker compose up -d` em `~/publisher-os` reconecta os volumes e traz serviços de volta
2. **Mover Desktop/ARQUIVOS_MANUS_CLAUDE (51.7 GB) para HD externo** — maior ganho possível
3. **Limpar .cache/whisper (5 GB)** — se não estiver usando transcrição ativamente
4. **Remover tags qwen-coder redundantes do Ollama** — não libera espaço (blob compartilhado), mas limpa
5. **Expandir armazenamento** — 924 GB é pouco para o ecossistema atual (Docker + Ollama + Obsidian + projetos)

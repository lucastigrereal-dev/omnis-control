# DISK-0 — Read-Only Audit Report

**Data:** 2026-05-06 15:10 BRT
**Branch:** master
**Script:** `scripts/disk_audit_readonly.py`
**Comandos:** `disk_audit_readonly.py` + `docker system df` + `docker ps --size`

---

## Espaço Livre

| Medida | Valor |
|--------|-------|
| Total | 992.5 GB |
| Usado | ~912 GB |
| **Livre** | **80.5 GB (8.1%)** |
| Status | **CRÍTICO** |

---

## Top Diretórios por Tamanho (projetos)

| Diretório | Tamanho |
|-----------|---------|
| daily-prophet-hotels | 970.0 MB |
| Downloads/instagram-publisher | 812.6 MB |
| publisher-os | 412.8 MB |
| omnis-control | 118.4 MB |
| biblioteca_sabedoria | 49.8 MB |
| JARVIS_OS | 1.8 MB |
| llm-router | 50.3 KB |

**Total projetos:** ~2.5 GB (insignificante vs. total do disco)

---

## Arquivos Grandes (>100 MB)

**Nenhum encontrado** nos 8 diretórios-alvo.

---

## node_modules

**Nenhum encontrado** — sem bloat de JS nos diretórios do ecossistema.

---

## Archives (.zip, .tar.gz, .rar)

**Nenhum encontrado** — sem rot de compactados.

---

## Docker — Uso de Disco

| Tipo | Total | Recuperável | % |
|------|-------|-------------|---|
| Images | 80.0 GB | **54.0 GB** | 67% |
| Containers | 131.2 MB | 0 B | 0% |
| Local Volumes | 23.1 GB | **7.8 GB** | 33% |
| Build Cache | 31.2 GB | **16.4 GB** | 52% |
| **Total recuperável** | | **~78.2 GB** | |

> 78 GB recuperáveis dobrariam o espaço livre de 80 → ~158 GB.

---

## Top 5 Containers por Tamanho Virtual

| Container | Tamanho Real | Tamanho Virtual |
|-----------|-------------|-----------------|
| publisher-os-supabase-db-1 | 36.9 kB | 6.12 GB |
| open-webui | 53.6 MB | 4.97 GB |
| publisher-os-publisher-core-1 | 4.25 MB | 4.33 GB |
| publisher-os-litellm-1 | 19.2 MB | 2.07 GB |
| crm-tigre-backend | 28.7 kB | 1.83 GB |

---

## Riscos

1. **80 GB livre pode zerar em semanas** com logs, cache Docker, volumes de banco crescendo
2. **Docker build cache** (31 GB) é o maior desperdício — 52% reclaimable
3. **54 GB em imagens não utilizadas** — imagens antigas de builds anteriores
4. **Nenhum risco imediato** de corrupção — disco não está 100%
5. **Windows Update pode falhar** se disco ficar abaixo de 20 GB

---

## Recomendações

1. **Prioridade máxima:** `docker image prune` — ~54 GB seguros
2. **Build cache:** `docker builder prune` — ~16 GB seguros
3. **Volumes órfãos:** revisar antes de limpar — ~7.8 GB
4. **Monitorar** semanalmente o espaço em disco
5. **Não apagar** código-fonte, DBs ou assets de produção

---

*Relatório gerado por Claude Code — 100% read-only, nada foi modificado*

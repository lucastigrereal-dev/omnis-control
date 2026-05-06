# DISK-0 — Cleanup Candidates

**Data:** 2026-05-06
**Regra:** Nada foi apagado. Esta é uma lista de candidatos para autorização humana.

---

## Docker Images (não utilizadas)

| # | Candidato | Tamanho | Risco | Motivo |
|---|-----------|---------|-------|--------|
| 1 | Imagens Docker não utilizadas | ~54 GB | ✅ Seguro | Apenas imagens sem container ativo |
| 2 | Build cache obsoleto | ~16.4 GB | ✅ Seguro | Cache de compilações anteriores |

**Total seguro:** ~70.4 GB

---

## Docker Volumes

| # | Candidato | Tamanho | Risco | Motivo |
|---|-----------|---------|-------|--------|
| 3 | Volumes órfãos | ~7.8 GB | ⚠️ Revisar | Pode conter dados de DB antigos |

**Total revisar:** ~7.8 GB

---

## Projetos

| # | Candidato | Tamanho | Risco | Motivo |
|---|-----------|---------|-------|--------|
| 4 | daily-prophet-hotels (node_modules + .next) | ~970 MB | ⚠️ Revisar | Código ativo, mas cache de build pode ser limpo |
| 5 | Downloads/instagram-publisher | ~812 MB | ⚠️ Revisar | Código ativo, verificar necessidade |

**Total revisar:** ~1.8 GB

---

## Resumo

| Prioridade | Candidato | Tamanho | Risco | Ação Sugerida |
|------------|-----------|---------|-------|---------------|
| P0 | docker image prune | ~54 GB | ✅ Seguro | `docker image prune -a` |
| P1 | docker builder prune | ~16.4 GB | ✅ Seguro | `docker builder prune` |
| P2 | Revisar volumes órfãos | ~7.8 GB | ⚠️ Revisar | `docker volume ls` + inspeção manual |
| P3 | .next cache hotel project | ~500 MB | ⚠️ Revisar | `npm run clean` no projeto |
| P4 | instagram-publisher | ~812 MB | ⚠️ Revisar | Decisão do operador |

**Potencial total de recuperação:** ~70-78 GB seguros + ~8 GB sob revisão

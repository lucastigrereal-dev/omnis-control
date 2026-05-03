# DISK CLEANUP PLAN — OMNIS

**Data:** 2026-05-03
**Status:** 🔴 CRÍTICO — 8.0% livre (74.4 GB / 924.3 GB)
**Risco:** Docker, logs e builds podem falhar a qualquer momento.

---

## Diagnóstico

```
C:\: 8.0% livre, 74.4 GB de 924.3 GB
```

Sem ação nos próximos dias, qualquer operação que gere arquivo grande (build, pull Docker, log) pode falhar.

---

## Ocupação por Categoria (estimativa)

| Categoria | Suspeita | Ação |
|-----------|----------|------|
| Docker images/volumes | Alta | `docker system df` para medir |
| Logs Python/JSONL | Média | Rotacionar logs antigos |
| Temp/Downloads | Alta | Limpar Downloads não usados |
| node_modules | Média | Onde houver, rodar `npm cache clean` |
| Windows Temp | Média | `cleanmgr` / `diskcleanup` |

---

## Plano de Ação (Manual, com confirmação)

### Passo 1 — Diagnóstico (seguro, read-only)
```bash
docker system df
docker image ls
docker volume ls
du -sh ~/omnis-control/logs/
du -sh ~/omnis-control/data/
```

### Passo 2 — Limpeza de logs OMNIS
```bash
# Com confirmação: compactar logs com mais de 7 dias
gzip ~/omnis-control/logs/*.log.old
# Ou: deletar logs com mais de 30 dias (pergunta primeiro)
find ~/omnis-control/logs/ -name "*.jsonl" -mtime +30
```

### Passo 3 — Docker prune (com confirmação)
```bash
# Preview do que seria limpo
docker system prune --all --volumes --dry-run

# Executar (SÓ COM CONFIRMAÇÃO EXPLÍCITA)
docker system prune --all --volumes -f
```

### Passo 4 — Windows cleanup
```bash
# Limpeza de cache e temp do Windows
cleanmgr /sageset:1  # Configurar opções
cleanmgr /sagerun:1   # Executar
```

---

## O que NÃO fazer

- Não apagar pastas de projeto sem confirmação.
- Não apagar `.env` ou credenciais.
- Não apagar dados do Publisher OS ou Akasha.
- Não rodar `docker system prune` sem dry-run primeiro.
- Não apagar arquivos modificados nos últimos 7 dias sem revisão.

---

## Monitoramento

```bash
# Comando OMNIS
python omnis.py doctor | grep -i disco
python omnis.py status

# Manual
wmic logicaldisk get size,freespace,caption
```

---

## Gatilho para Ação Imediata

Se disco chegar a **5% livre**, qualquer operação com Docker ou build deve parar até limpeza ser feita.

Se disco chegar a **2% livre**, o sistema pode travar. Prioridade absoluta.

# DISK-0 — Comandos Sugeridos (NÃO EXECUTADOS)

> **⚠️ ATENÇÃO:** NENHUM comando abaixo foi executado.
> Esta lista é apenas uma sugestão para autorização humana.
> Leia cada comando, entenda o risco, e só execute se confirmar.

---

## NÃO EXECUTADO — SUGERIDO APENAS — EXIGE AUTORIZAÇÃO HUMANA

---

### Comando 1: Limpar imagens Docker não utilizadas

```bash
docker image prune -a --filter "until=72h"
```

| Campo | Detalhe |
|-------|---------|
| **O que faz** | Remove imagens sem container ativo há mais de 72h |
| **Quanto libera** | ~54 GB |
| **Risco** | ✅ Baixo — imagens podem ser baixadas novamente |
| **Rollback** | Possível — rebuild via docker-compose |
| **Confirmação** | Required |

---

### Comando 2: Limpar build cache Docker

```bash
docker builder prune --all --filter "until=72h"
```

| Campo | Detalhe |
|-------|---------|
| **O que faz** | Remove cache de build anterior |
| **Quanto libera** | ~16.4 GB |
| **Risco** | ✅ Baixo — cache regenerado no próximo build |
| **Rollback** | Não necessário — recriado automaticamente |
| **Confirmação** | Required |

---

### Comando 3: Listar volumes órfãos (inspeção)

```bash
docker volume ls --filter "dangling=true"
docker volume inspect <volume-id>  # para cada volume suspeito
```

| Campo | Detalhe |
|-------|---------|
| **O que faz** | Lista volumes sem container vinculado |
| **Quanto libera** | ~7.8 GB (após identificar quais remover) |
| **Risco** | ⚠️ Médio — requer inspeção manual antes de remover |
| **Rollback** | Depende — se tiver backup, sim |
| **Confirmação** | Required |

---

### Comando 4: Limpar cache .next do daily-prophet-hotels

```bash
cd ~/daily-prophet-hotels && rm -rf .next/cache
```

| Campo | Detalhe |
|-------|---------|
| **O que faz** | Remove cache de build do Next.js |
| **Quanto libera** | ~100-300 MB |
| **Risco** | ✅ Baixo — regenerado no próximo build |
| **Rollback** | Não necessário |
| **Confirmação** | Required |

---

### Comando 5: Limpeza total segura (combinada)

```bash
docker image prune -a --filter "until=72h" && docker builder prune --all --filter "until=72h"
```

| Campo | Detalhe |
|-------|---------|
| **O que faz** | Remove imagens antigas + build cache |
| **Quanto libera** | ~70 GB |
| **Risco** | ✅ Baixo |
| **Rollback** | Possível (rebuild) |
| **Confirmação** | Required |

---

### Comando NÃO recomendado agora

```bash
docker system prune --volumes  # Remove volumes com dados potencialmente importantes
```

| Campo | Detalhe |
|-------|---------|
| **Risco** | 🔴 Alto — pode perder dados de banco |
| **Motivo** | Remove volumes Docker inclusive com dados |
| **Recomendação** | Só executar após inspeção manual |

---

**NENHUM COMANDO FOI EXECUTADO — TODOS REQUEREM AUTORIZAÇÃO HUMANA**

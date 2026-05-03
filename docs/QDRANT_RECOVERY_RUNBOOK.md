# QDRANT RECOVERY RUNBOOK — OMNIS

**Data:** 2026-05-03
**Status:** ⚠️ Diagnosticar (container pode estar saudável, porta pode estar fechada)

---

## Diagnóstico

### Passo 1 — Container existe?
```bash
docker ps --filter name=qdrant --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Passo 2 — Porta responde?
```bash
curl -s http://localhost:6333/health 2>&1 || echo "PORTA_FECHADA"
curl -s http://localhost:6333/collections 2>&1 || echo "SEM_RESPOSTA"
```

### Passo 3 — Docker interno vs host
Qdrant pode estar rodando em rede Docker interna, não mapeada para o host.
```bash
docker port publisher-os-qdrant-1
docker inspect publisher-os-qdrant-1 --format '{{range $p, $conf := .NetworkSettings.Ports}}{{$p}} -> {{(index $conf 0).HostPort}}{{"\n"}}{{end}}'
```

### Passo 4 — Teste dentro da rede Docker
```bash
docker exec publisher-os-qdrant-1 curl -s http://localhost:6333/health
```

---

## Resolução

### Cenário A — Container parado
```bash
docker start publisher-os-qdrant-1
```
*Aguardar 10s e testar novamente.*

### Cenário B — Porta não mapeada para host
Criar mapeamento no `docker-compose.yml` do Publisher OS:
```yaml
ports:
  - "6333:6333"
```
*Requer reinício do container e confirmação do operador.*

### Cenário C — Container saudável, mas OMNIS aponta URL errada
Verificar `config/paths.yaml`:
```yaml
qdrant:
  url: "http://localhost:6333"
```
Testar com:
```bash
python -c "import requests; r=requests.get('http://localhost:6333/health'); print(r.status_code)"
```

---

## Verificação pós-recovery

```bash
# Acessível?
curl -s http://localhost:6333/health

# Coleções existem?
curl -s http://localhost:6333/collections | python -m json.tool
```

---

## Se nada funcionar

1. Verificar logs do container: `docker logs publisher-os-qdrant-1 --tail 50`
2. Verificar disco: Qdrant pode estar falhando por falta de espaço.
3. Recriar container: `docker-compose up -d qdrant` (no diretório do Publisher OS).

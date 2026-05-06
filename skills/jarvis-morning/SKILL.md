---
name: jarvis-morning
description: |
  Briefing operacional matinal com diagnóstico de sistema. Roda 8h via cron OU
  manualmente. Output: top 3 prioridades + alertas + status sistema. READ-ONLY.
trigger:
  - cron 8h
  - usuário pede "bom dia jarvis" / "briefing"
  - "bom dia"
  - "missão do dia"
  - "o que fazer hoje"
sector: operacoes_organizacao
risk: low
model: haiku
approval_required: []
status: active
version: 1.0
absorbs:
  - morning-briefing  # depreciada
  - organizer         # depreciada
config:
  disk_alert_threshold_percent: 92
  cron_schedule: "0 8 * * *"
cost_estimate: "$0.002/run"
verification_criteria:
  - Sistemas com status explícito (verde/amarelo/vermelho)
  - Top 3 prioridades são concretas e executáveis hoje
  - Output < 300 palavras
  - Termina com "Qual das 3 missões você quer atacar primeiro?"
---

# Skill: jarvis-morning

Merge de `morning-briefing` (briefing completo) + `organizer` (diagnóstico sistema). READ-ONLY.

## Quando usar

"bom dia" / "briefing" / "missão do dia" / "o que fazer hoje" / primeira mensagem do dia

## Processo (executar em ordem)

### 1. Diagnóstico do sistema (Organizer)

```bash
bash ~/diagnostico_rapido.sh 2>/dev/null | grep -E "(RODANDO|MORTOS|Akasha|Publisher|DISCO)"
```

Verificar disco — alerta se > 92%:

```bash
df -h / 2>/dev/null | awk 'NR==2 {gsub("%",""); if($5>92) print "⚠️ DISCO CRÍTICO: "$5"%"; else print "✅ Disco: "$5"%"}'
```

Docker health:

```bash
docker ps --format "{{.Names}}\t{{.Status}}" 2>/dev/null | head -15
# Conta unhealthy
docker ps --filter "health=unhealthy" --format "{{.Names}}" 2>/dev/null | wc -l
```

Akasha estado:

```bash
docker exec akasha-postgres psql -U akasha -d gringotts \
  -c "SELECT cofre, total FROM v_gringotts_status;" 2>/dev/null
```

### 2. CEO Assistant Briefing (Publisher OS)

```bash
curl -s http://localhost:8000/api/assistant/briefing 2>/dev/null | python3 -m json.tool 2>/dev/null | head -30
```

Fallback se Publisher OS offline:

```bash
curl -s http://localhost:8000/api/v1/triggers/morning-briefing 2>/dev/null | head -20
```

### 3. Missão do dia (Obsidian)

```bash
cat ~/Desktop/OBSIDIAN/ComandoCentral/MISSAO_DO_DIA.md 2>/dev/null | head -20
cat ~/Desktop/OBSIDIAN/ComandoCentral/STATUS.md 2>/dev/null | head -10
```

### 4. Pipeline comercial

```bash
cat ~/Desktop/OBSIDIAN/ComandoCentral/PIPELINE.csv 2>/dev/null | head -8
```

### 5. Projetos ativos (últimos commits)

```bash
for proj in publisher-os publisher-os-cockpit daily-prophet-hotels; do
  echo "--- $proj ---"
  git -C ~/$proj log --oneline -2 2>/dev/null || echo "  sem repo"
done
```

### 6. Insight do Obsidian (contexto do dia)

```bash
grep -ri "$(date +%B)" ~/Desktop/OBSIDIAN/ComandoCentral/00_Contexto/ACOES_IMEDIATAS.md 2>/dev/null | head -5
```

## Output format

```
☀️ Bom dia, Tigrão. [DIA DA SEMANA], [DATA]

📊 Sistema: [verde/amarelo/vermelho]
   ├─ Docker: [N containers, M unhealthy]
   ├─ Disco: [X% usado] [⚠️ ALERTA se > 92%]
   ├─ Publisher OS: [UP/DOWN] :8000
   ├─ Cockpit: [UP/DOWN] :3200
   └─ Akasha/Gringotts: [totais por cofre em 1 linha]

🔥 Missão do dia:
[Conteúdo de MISSAO_DO_DIA.md — máx 3 linhas]

## Pipeline comercial
- [N] hotéis no pipeline
- [Status dos mais quentes — máx 3 nomes]

## Top 3 ações para hoje
  1. [Ação concreta + resultado esperado]
  2. [Ação concreta + resultado esperado]
  3. [Ação concreta + resultado esperado]

## Conteúdo a publicar hoje
[Do CEO briefing — máx 2 linhas]

💡 Insight: [1 trecho relevante do Obsidian]
⚠️ Alertas: [bloqueios ativos ou containers UNHEALTHY — omitir se nenhum]
```

## Regras

- Output total < 300 palavras
- Sempre terminar com "Qual das 3 missões você quer atacar primeiro?"
- Usar Haiku — não Sonnet/Opus (custo)
- Se sistema offline: nota o problema e continua — não trava o briefing
- Disco > 92%: inclui alerta vermelho no topo
- Containers UNHEALTHY: lista os nomes no bloco de alertas
- Se /api/assistant/briefing retornar 5xx: fallback para MCP `get_briefing`

## Fix conhecida — slowapi (herdada de organizer)

Após rebuild do `publisher-core`, `slowapi` pode não estar instalado:

```bash
docker exec publisher-os-publisher-core-1 pip install slowapi
docker compose -f ~/publisher-os/docker-compose.yml restart publisher-core
curl -s http://localhost:8000/health
```

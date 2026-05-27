# HANDOFF — BLOCO 2: WAVES 8, 9, 10 ✅

**Branch:** `feature/omnis-5waves-runtime-supreme`
**Data:** 2026-05-26
**Operador:** Lucas Tigre (Tigrão)

---

## WAVE 8 — Performance Report ✅

**Commit:** `113f5ee`
**Arquivo:** `src/agencia/performance_report.py`
**CLI:** `omnis content report [--days N] [--json]`

### O que faz
Agrega dados de múltiplas fontes e gera relatório de performance:
- `mission_runs.jsonl` → total de runs, command stats, avg duration
- `output/agencia/**/*.manifest.json` → carrosseis + clipes gerados
- `data/publish_ready/*/manifest.json` → exports feitos
- `caption_drafts.jsonl` → drafts aprovados vs pendentes
- `productivity_score` 0-100 (fórmula ponderada, custo R$0,00)

### Prova (anti-teatro)
```
omnis content report --days 7
```
Retorna productivity_score baseado em dados reais de `output/agencia/`.

### KRATOS pode exibir
- Rota: `GET /api/content/report?days=7`
- Resposta: `to_dict()` com `total_runs`, `clips_generated`, `carrosseis_generated`, `productivity_score`, `command_stats[]`

### Testes
15 testes verdes em `tests/agencia/test_performance_report.py`

---

## WAVE 9 — Publisher Prepare (Stub) ✅

**Commit:** `734eb2b`
**Arquivo:** `src/agencia/publisher_prepare.py`
**CLI:** `omnis content prepare-publish [--account @x] [--real] [--json]`

### O que faz
Prepara payload completo para publicação SEM publicar e SEM credencial:
- Distribui drafts aprovados em slots de horário de pico (configurável por dia da semana)
- `publer_bulk.csv` — formato Publer bulk upload com Account/Date/Time/Caption/Hashtags
- `manychat_stub.json` — automation stub com trigger `QUERO` no comentário
- `manifest.json` — sempre gerado (dry_run ou não)
- Output: `data/publish_ready/<date>-<id>/`

### Peak Hours
```python
Segunda:  07:00, 12:00, 19:00
Terça:    07:30, 12:00, 20:00
Quarta:   08:00, 13:00, 19:00
Quinta:   07:00, 12:30, 20:00
Sexta:    07:00, 12:00, 18:00
Sábado:   09:00, 14:00, 20:00
Domingo:  10:00, 15:00, 19:00
```

### Prova (anti-teatro)
```
omnis content prepare-publish --real
```
Gera `publer_bulk.csv` + `manychat_stub.json` em `data/publish_ready/`.

### KRATOS pode exibir
- Rota: `GET /api/content/publish-package`
- Resposta: `PublishPackage.to_dict()` com `slots[]`, `total_posts`, `publer_csv_path`

### Testes
15 testes verdes em `tests/agencia/test_publisher_prepare.py`

---

## WAVE 10 — Health Score ✅

**Commit:** `9d38d94`
**Arquivo:** `src/health/score.py`
**CLI:** `omnis health-score [--json] [--history N] [--no-persist]`

### O que faz
Score único 0-100 de saúde do sistema com 5 dimensões:

| Check           | Pts | O que verifica                              |
|-----------------|-----|---------------------------------------------|
| ollama          | 20  | Porta 11434 aberta (socket.connect_ex)      |
| akasha-postgres | 15  | Container Docker `akasha-postgres` running  |
| drafts-pending  | 15  | Fila de aprovação (0=ok, ≤5=warn, >5=fail)  |
| recent-content  | 20  | Manifests em output/agencia/ nos últimos 7d |
| mission-logger  | 10  | Último run em mission_runs.jsonl = success  |

**Thresholds:**
- `verde`:    score ≥ 70
- `amarelo`:  score ≥ 40
- `vermelho`: score < 40

**Persistência:** `logs/health_scores.jsonl` (append-only, formato `{"date", "score", "color"}`)

### Prova ao vivo (2026-05-26 05:05 UTC)
```
omnis health-score

HEALTH SCORE: 81/100  [VERDE]
  ollama          20/20  ok    port 11434 aberta
  akasha-postgres 15/15  ok    container running
  drafts-pending   0/15  fail  40 drafts pendentes (fila alta)
  recent-content  20/20  ok    100 arquivos recentes
  mission-logger  10/10  ok    último run: carrossel OK
```

### Histórico
```
omnis health-score --history 5
```

### KRATOS pode exibir
- Rota: `GET /api/health/score`
- Resposta:
```json
{
  "score": 81,
  "color": "green",
  "checks": [...],
  "generated_at": "2026-05-26T05:05:00+00:00",
  "warnings": ["40 drafts pendentes (fila alta)"]
}
```
- Widget sugerido: gauge/semicírculo 0-100 com cor dinâmica + lista de checks expandível

### Testes
33 testes verdes em `tests/health/test_health_score.py`

---

## Resumo BLOCO 2

| Wave | Status | Commit   | CLI                              | Testes |
|------|--------|----------|----------------------------------|--------|
| 8    | ✅     | 113f5ee  | `omnis content report`           | 15     |
| 9    | ✅     | 734eb2b  | `omnis content prepare-publish`  | 15     |
| 10   | ✅     | 9d38d94  | `omnis health-score`             | 33     |

**Total novo:** 63 testes adicionados no BLOCO 2

---

## ZONA VERMELHA — Aguardando Tokens

### WAVE 6 — Memória Notion
**Status:** PARADO — ZONA VERMELHA
**Motivo:** Precisa de `NOTION_TOKEN` via env (não inline, não commitar)
**Como fornecer:**
```powershell
$env:NOTION_TOKEN = "seu_token_aqui"
```
Depois retome: `omnis wave-6 start` (ou informe o token)

### WAVE 7 — Memória Akasha
**Status:** PARADO — ZONA VERMELHA
**Motivo:** Precisa de `AKASHA_DB_URL` via env para rotacionar credencial R01
**Como fornecer:**
```powershell
$env:AKASHA_DB_URL = "postgresql://akasha:SENHA@localhost:5432/akasha"
```
Depois retome.

---

## Próximas ações após aprovação

1. **Aprovar drafts pendentes** — 40 drafts na fila → `omnis content approve --batch --limit 40` para subir score de 81 → ~95
2. **Fornecer NOTION_TOKEN** para WAVE 6
3. **Confirmar rotação de credencial** para WAVE 7
4. **KRATOS** pode consumir `/api/health/score` para widget de gauge na dashboard

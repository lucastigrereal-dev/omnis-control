# SUPERPROMPT v2 — MISSÃO OMNIS (CORRIGIDA)
**Para:** Claude Code (Sonnet 4.6) em `~/omnis-control/`
**Data:** 2026-05-03
**Versão:** 2.0 — corrigido com base em 30 alertas de auditoria interna
**Sessão estimada:** 2-3h (3 fases, não 6)

---

## DECISÕES QUE VALEM COMO LEI NESTA MISSÃO

Antes de qualquer coisa, estas decisões são absolutas (de DECISOES.md):

- **D003:** Não mexer no Publisher OS
- **D006:** Não chamar APIs externas. Não ler `.env`. Tudo local e testável.
- **D007:** Aprovação manual é obrigatória antes de qualquer publicação
- **D008:** Não apagar nada automaticamente sem confirmação explícita

O v1 deste prompt violava D003 e D006 na Fase E (Publisher OS Connector via HTTP GET).
**A Fase E foi removida desta missão.**

---

## ESTADO REAL DO SISTEMA (verificado agora)

```
Disco C:          73GB livres de 924GB (8.0% livre — amarelo, não crítico)
caption_drafts:   40 com status "needs_review", 1 approved
content_queue:    40 needs_asset, 2 caption_ready
publisher_check:  já usa httpx — NÃO expandir (viola D006)
Testes:           213 passando
```

---

## INICIE ASSIM (obrigatório antes de qualquer coisa)

```bash
cd ~/omnis-control
python -m pytest tests/ -v --tb=short 2>&1 | tail -5
```

Confirme 213 testes verdes. Se algum falhar: **pare, corrija, só então avance.**

---

## MISSÃO — 3 FASES

### FASE 1 — Disk Analyze (somente análise, sem deletar)

**Objetivo:** Saber exatamente o que está ocupando espaço. Sem deletar nada.

**Por quê esta fase existe:** D008 proíbe apagar automaticamente. Mas ter visibilidade é seguro e necessário.

**Criar:** `scripts/disk_analyze.py`

```python
"""
OMNIS Disk Analyzer — análise read-only de uso de disco.
Nunca deleta nada. Só informa.

Uso: python scripts/disk_analyze.py
"""
```

O script deve usar **Python puro + pathlib** (sem PowerShell, sem subprocess desnecessário):

1. Disco C: — espaço total, usado, livre (via `shutil.disk_usage`)
2. Docker — rodar `docker system df` via `subprocess.run` e capturar output
3. Logs OMNIS — listar `logs/*.jsonl` com tamanho e data de modificação
4. Exports OMNIS — listar `data/exports/` com tamanho e data
5. Imprimir tabela simples no terminal (sem Rich, sem dependências extras)
6. Ao final: **apenas sugerir ações**, nunca executar

Output esperado:
```
═══════════════════════════════════════
  OMNIS DISK ANALYZER — 2026-05-03
═══════════════════════════════════════

DISCO C:
  Total:  924 GB
  Usado:  851 GB
  Livre:   73 GB (8.0%) ⚠️ Abaixo de 15%

DOCKER (via docker system df):
  [output bruto do comando]

LOGS OMNIS (logs/):
  missions.jsonl       0 KB  2026-05-03
  tool_runs.jsonl      0 KB  2026-05-03

EXPORTS (data/exports/):
  [lista arquivos]

AÇÕES SUGERIDAS:
  1. docker image prune -f         → estimativa: X GB
  2. docker builder prune -f       → estimativa: X GB
  [nunca executa — só sugere]
```

**Adicionar ao CLI em `omnis.py`:**
```
omnis disk analyze    → roda disk_analyze.py e exibe
```

**Adicionar ao .gitignore:**
```
data/exports/
logs/briefing_*.md
logs/disk_cleanup_*.log
```

**Criar:** `tests/test_disk_analyze.py`
- Testar que o script roda sem erro
- Testar que `shutil.disk_usage` retorna valores razoáveis (> 0)
- Testar que subprocess para docker não lança exceção quando falha (mock)
- **NÃO** testar valores absolutos de disco (variam por máquina)

---

### FASE 2 — Batch Review + Export Controlado

**Objetivo:** Aprovar drafts em lote com validação, não às cegas.

**Contexto real:** 40 drafts estão como `needs_review` (não `pending`). O batch precisa lidar com esse status.

**Expandir:** `src/caption_approval/approvals.py`

Adicionar função `batch_review_to_approved(limit: int = 5) -> dict`:

```python
def batch_review_to_approved(limit: int = 5) -> dict:
    """
    Move drafts de needs_review para approved.
    Valida cada draft antes de aprovar.
    Limit padrão: 5 por vez (seguro, controlado).
    Retorna: {"approved": N, "skipped": N, "skip_reasons": [...]}
    """
```

Regras de validação antes de aprovar:
- Draft tem `content` preenchido (não vazio, não None)
- Draft NÃO tem placeholders: `[`, `]`, `TODO`, `REVISAR`, `PLACEHOLDER`
- Draft tem `account_id` definido
- Se qualquer validação falhar: **skip com reason**, não erro

**Adicionar ao CLI:**
```
omnis approvals batch --limit 5    → aprova até 5 drafts válidos (padrão)
omnis approvals batch --limit 10   → aprova até 10
omnis approvals status             → mostra contagem por status
```

**Export pós-aprovação** (simples, não automático):
```
omnis approvals export             → gera data/exports/approved_latest.csv
```

Nota: sempre sobrescreve `approved_latest.csv` (não acumula). Resolve poluição de git.

**Criar:** `tests/test_batch_approve.py`
- Testar com 3 drafts válidos: aprovados
- Testar com draft com placeholder `[HOOK A REVISAR]`: skipped
- Testar com draft sem content: skipped
- Testar limit=2 com 5 válidos: só 2 aprovados
- Testar com 0 drafts disponíveis: retorna {"approved": 0, "skipped": 0}

---

### FASE 3 — Briefing Matinal

**Objetivo:** Um comando que dá visão do sistema em < 10 segundos. Máximo 3 ações.

**Criar:** `src/reports/briefing.py`

Health score simples (0-100), calculado localmente, sem chamadas externas:

```python
dimensions = {
    "pipeline":    # % drafts aprovados / total na fila (peso 40%)
    "disk":        # % livre de disco C: (peso 30%) — crítico < 10%, ok > 20%
    "containers":  # via docker ps --format, conta healthy/total (peso 20%)
    "queue":       # items caption_ready / total queue (peso 10%)
}
```

Critérios de cor:
- 80-100: verde ✅
- 60-79:  amarelo ⚠️
- 0-59:   vermelho ❌

TOP 3 AÇÕES — lógica de priorização:
```python
# Ordem de prioridade (não inventar — regras fixas):
actions = []
if disk_pct < 10:
    actions.append("URGENTE: omnis disk analyze → identificar o que limpar")
if approved_pct < 5:
    actions.append("omnis approvals batch --limit 10 → aprovar drafts")
if oauth_connected == 0:
    actions.append("Configurar META_APP_SECRET no publisher-os/.env")
if containers_unhealthy > 0:
    actions.append(f"{containers_unhealthy} containers unhealthy → ver docs/LEGACY_CONTAINERS.md")
# Retornar só os 3 primeiros
return actions[:3]
```

Output do briefing (terminal):
```
════════════════════════════════════════
  OMNIS — BRIEFING 2026-05-03
════════════════════════════════════════

SAÚDE: 68/100 ⚠️

📊 PIPELINE
  Fila:       42 itens
  Aprovados:  1 (2.4%)
  Argos:      1 draft pronto

💾 DISCO
  Livre: 73 GB (8.0%) ⚠️

🐳 CONTAINERS
  Rodando:   18
  Unhealthy: 2 (crm-tigre-backend, jarvis_frontend)

🎯 PRÓXIMAS 3 AÇÕES
  1. omnis approvals batch --limit 10
  2. Configurar META_APP_SECRET no publisher-os/.env
  3. Investigar crm-tigre-backend (UNHEALTHY 9d)

════════════════════════════════════════
```

Salvar em `logs/briefing_YYYY-MM-DD.md` apenas com flag `--save`.
Adicionar `logs/briefing_*.md` ao `.gitignore` (já listado na Fase 1).

Health scores históricos: gravar em `logs/health_scores.jsonl` a cada execução:
```json
{"date": "2026-05-03", "score": 68, "dimensions": {"pipeline": 2, "disk": 8, "containers": 89, "queue": 5}}
```

**Adicionar ao CLI:**
```
omnis briefing          → exibe briefing no terminal
omnis briefing --save   → exibe + salva em logs/
```

**Criar:** `tests/test_briefing.py`
- Mock de todos os checkers externos (docker ps, disk_usage)
- Testar que score fica entre 0 e 100
- Testar lógica das 3 ações com cenários: disco baixo, disco ok, sem aprovados
- Testar que `--save` cria o arquivo
- Testar que briefing NÃO falha se docker ps falhar (deve retornar "N/A")

---

## FASE FINAL — Commit

Após as 3 fases, se todos os testes passarem:

```bash
python -m pytest tests/ -v --tb=short 2>&1 | tail -10
```

Esperado: 220+ testes (eram 213 + ~7-10 novos por fase).

Atualizar `docs/ESTADO_ATUAL_RESUMIDO.md`:
- Data: 2026-05-03
- Novos comandos: `omnis disk analyze`, `omnis approvals batch`, `omnis approvals status`, `omnis approvals export`, `omnis briefing`
- Testes: N/N passando

Commit:
```bash
git add -A
git commit -m "feat: disk analyzer, batch approve com validação, briefing matinal

- scripts/disk_analyze.py: análise read-only, sem deletar (D008 respeitada)
- batch_review_to_approved(limit=N): valida placeholders antes de aprovar
- src/reports/briefing.py: health score + top 3 ações
- CLI: omnis disk analyze, approvals batch/status/export, briefing
- .gitignore: data/exports/, logs/briefing_*.md
- Testes: N/N passando

D003, D006, D007, D008 respeitadas.
Next: META OAuth (sessão separada)"
```

---

## REGRAS DESTA MISSÃO

1. **D006 é lei:** Nenhuma chamada HTTP externa. `publisher_check.py` não é expandido.
2. **D008 é lei:** `disk_analyze.py` NUNCA executa limpeza. Só analisa e sugere.
3. **Batch approve com limit:** padrão 5, máximo que o operador definir. Nunca `--all`.
4. **Python puro:** pathlib, shutil, subprocess. Sem dependências novas.
5. **Um teste por comportamento:** não teste os internos do Python, teste o comportamento do seu código.
6. **Se travar > 15 min numa fase:** documente o bloqueio em 1 linha no commit e avance.
7. **Não criar pastas vazias** (D006 também proíbe isso).

---

## CRITÉRIO DE SUCESSO

```
python omnis.py disk analyze     → roda, mostra disco + docker + sugestões
python omnis.py approvals batch  → aprova até 5 drafts válidos, skipa inválidos
python omnis.py approvals status → mostra contagem por status
python omnis.py briefing         → health score + 3 ações em < 3 segundos
python -m pytest tests/ -v       → 220+ testes, zero falhas
git log --oneline -1             → commit correto
```

Bora.

# SUPERPROMPT — MISSÃO COMPLETA OMNIS
**Para:** Claude Code (Sonnet 4.6) rodando em `~/omnis-control/`
**Data:** 2026-05-03
**Modelo recomendado:** Sonnet 4.6 — NÃO use Opus para isso
**Modo:** Execução sequencial imparável

---

## CONTEXTO (leia uma vez, não repita)

Você está dentro do projeto OMNIS (`~/omnis-control/`), o sistema operacional agentic do Lucas Tigre.

**O que já existe e está funcionando (NÃO tocar):**
- 213 testes passando ✅
- Pipeline: accounts → queue (42) → drafts (41) → approved (1) → argos_bridge → CSV/JSON export
- `config/sectors.yaml` (9 setores), `config/connectors.yaml` (16 conectores)
- Módulos: `src/argos_bridge/`, `src/caption_approval/`, `src/content_queue/`, `src/video_assets/`
- CLI: `omnis.py` com comandos funcionais
- `docs/DECISOES.md` (D001-D014 — lei interna do projeto)

**O que OMNIS NÃO faz ainda (gaps a preencher nesta missão):**
1. Não tem integração real com Publisher OS (MCP/API)
2. Não tem OAuth Meta configurado (bloqueio de publicação)
3. Não tem limpeza de disco automatizada (disco a 7% livre — CRÍTICO)
4. Não tem recovery do Qdrant
5. Não tem mission logging estruturado em `logs/missions.jsonl`
6. Não tem briefing matinal CLI (`omnis briefing`)
7. Não tem health score calculado
8. Não tem aprovação em lote (batch approve)
9. Não tem export agendado automático

**Regras absolutas (da D001-D014):**
- NÃO modificar `~/publisher-os/`, `~/.claude/`, `~/JARVIS_OS/`
- NÃO ler `.env` nunca
- NÃO chamar Instagram/Meta API sem OAuth completo
- NÃO publicar conteúdo automaticamente (approval gate obrigatório)
- NÃO criar squads dinâmicos ainda
- SEMPRE rodar `python -m pytest tests/ -v` antes de commitar

---

## MISSÃO — 6 FASES SEQUENCIAIS

Execute uma fase por vez. Ao concluir cada fase, rode os testes. Só avance se 100% verde.

---

### FASE A — Saneamento de Disco (P0 — URGENTE)

**Por quê primeiro:** Disco a 7% livre bloqueia qualquer build, Docker pull ou operação pesada.

**Criar:** `scripts/disk_cleanup.py`

```python
"""
OMNIS Disk Cleanup — remove Docker dangling, build cache, logs antigos.
Modo seguro: analisa antes, só executa com --execute flag.
"""
```

O script deve:

1. Analisar (sem deletar):
   - `docker system df` — mostrar imagens/volumes/cache removíveis
   - `Get-ChildItem ~/omnis-control/logs -Filter "*.log"` — logs > 7 dias
   - `Get-ChildItem ~/.claude/cache` — cache Claude Code
   - Total de espaço recuperável estimado

2. Com flag `--execute`:
   - Rodar `docker image prune -f` (só dangling, não todas)
   - Rodar `docker builder prune -f`
   - Deletar logs OMNIS > 30 dias
   - NUNCA deletar dados, volumes com dados, ou arquivos fora de escopo

3. Registrar resultado em `logs/disk_cleanup_YYYY-MM-DD.log`

**Adicionar ao CLI:**
```
omnis disk analyze    → mostra análise sem deletar
omnis disk clean      → executa limpeza (pede confirmação)
```

**Teste mínimo:** `test_disk_cleanup.py` com mock de subprocess.

---

### FASE B — Mission Logger

**Por quê:** Sem log de missões, o sistema não aprende. `logs/missions.jsonl` existe mas está vazio.

**Criar:** `src/utils/mission_logger.py`

Schema de cada entrada:
```json
{
  "mission_id": "uuid4",
  "timestamp": "ISO8601",
  "trigger": "cli|api|scheduled",
  "command": "string",
  "input_summary": "string (max 200 chars)",
  "output_summary": "string (max 200 chars)",
  "status": "success|failed|partial",
  "duration_ms": 0,
  "files_created": [],
  "errors": []
}
```

O logger deve:
- Ser chamado automaticamente por qualquer comando CLI via decorator
- Gravar em `logs/missions.jsonl` (append)
- Nunca quebrar o fluxo principal se falhar (try/except silencioso)
- Expor `get_last_n(n=10)` para o briefing

**Integrar nos comandos existentes:**
- `omnis doctor`
- `omnis report`
- `omnis queue stats`
- `omnis argos export`

**Teste:** `test_mission_logger.py` com 5 cenários incluindo falha silenciosa.

---

### FASE C — Batch Approve + Export Automático

**Por quê:** Hoje só dá para aprovar 1 draft por vez. Com 41 na fila, é inviável.

**Expandir:** `src/caption_approval/approvals.py`

Adicionar função `batch_approve(ids: list[str] = None, all_pending: bool = False)`:
- Se `all_pending=True`, aprova todos com status `pending`
- Se `ids` fornecido, aprova apenas os IDs especificados
- Registra cada aprovação em `data/approval_log.jsonl`
- Retorna summary: `{approved: N, skipped: N, errors: []}`

**Adicionar ao CLI:**
```
omnis approvals batch --all          → aprova todos pendentes
omnis approvals batch --ids id1,id2  → aprova selecionados
omnis approvals export --format csv  → exporta aprovados para CSV
```

**Export automático:** Após batch approve, gerar automaticamente:
- `data/exports/approved_YYYY-MM-DD_HH-MM.csv`
- `data/exports/approved_YYYY-MM-DD_HH-MM.json`

**Teste:** `test_batch_approve.py` com 3 cenários: all, by IDs, vazio.

---

### FASE D — Health Score + Briefing Matinal

**Por quê:** O manifesto exige que o sistema reduza carga cognitiva do Lucas. Briefing = 1 leitura, 3 ações.

**Criar:** `src/reports/health_score.py`

Calcular um score 0-100 com 5 dimensões:
```python
dimensions = {
    "pipeline":    calcular % de drafts aprovados / total na fila,
    "disk":        calcular % espaço livre (crítico < 15%),
    "containers":  calcular % containers healthy / total,
    "queue":       calcular itens em fila / capacidade estimada,
    "memory":      verificar se Akasha responde (porta 5432),
}
```

Score final = média ponderada (pipeline 40%, disk 25%, containers 20%, queue 10%, memory 5%)

**Criar:** `src/reports/briefing.py`

Output do briefing (formato terminal + gravado em `logs/briefing_YYYY-MM-DD.md`):

```
════════════════════════════════════════
  OMNIS — BRIEFING 2026-05-03 08:00
════════════════════════════════════════

SAÚDE DO SISTEMA: 72/100 ⚠️

📊 PIPELINE
  Fila:      42 items
  Aprovados: 1 (2.4%)
  Argos:     1 draft pronto

💾 DISCO
  Livre: 7% ⚠️ CRÍTICO
  Ação: rodar `omnis disk clean`

🐳 CONTAINERS (18 rodando)
  Unhealthy: crm-tigre-backend, jarvis_frontend
  Healthy:   16/18

🎯 TOP 3 AÇÕES HOJE
  1. [URGENTE] omnis disk clean — liberar espaço
  2. omnis approvals batch --all — aprovar 41 drafts
  3. Configurar META_APP_SECRET no publisher-os/.env

════════════════════════════════════════
```

**Adicionar ao CLI:**
```
omnis briefing          → gera e exibe briefing
omnis briefing --save   → salva em logs/briefing_YYYY-MM-DD.md
```

**Teste:** `test_briefing.py` com mock de todos os checks.

---

### FASE E — Publisher OS Connector (read-only primeiro)

**Por quê:** OMNIS precisa saber o status do Publisher OS sem modificá-lo. D003 diz: não alterar. Mas ler é seguro.

**Expandir:** `src/checkers/publisher_check.py` (já existe — melhorar)

Adicionar:
```python
def get_publisher_queue_stats() -> dict:
    """GET http://localhost:8000/api/v1/queue — retorna stats da fila Argos"""

def get_publisher_accounts() -> list:
    """GET http://localhost:8000/api/v1/accounts — lista contas OAuth"""

def get_publisher_health() -> dict:
    """GET http://localhost:8000/health — healthcheck"""
```

Cada função deve:
- Ter timeout de 3s
- Retornar `{"status": "unreachable"}` se falhar (nunca lançar exceção)
- Ser usada pelo briefing e pelo doctor

**Adicionar ao CLI:**
```
omnis publisher status    → mostra status do Publisher OS
omnis publisher accounts  → lista contas (com OAuth status)
```

**NÃO:** não chamar endpoints que modificam estado. Apenas GET.

**Teste:** `test_publisher_connector.py` com mock httpx.

---

### FASE F — Commit + Documentação Final

**Por quê:** Push sem documentação é desperdício. Documentação sem commit é fantasma.

**Executar:**
```bash
cd ~/omnis-control
python -m pytest tests/ -v --tb=short
```

Se 100% verde:

**Atualizar:** `docs/ESTADO_ATUAL_RESUMIDO.md`
- Adicionar as 5 fases concluídas desta missão
- Atualizar contagem de testes
- Atualizar data

**Atualizar:** `README.md`
- Adicionar novos comandos CLI
- Atualizar "o que funciona"

**Criar:** `docs/MISSAO_2026-05-03.md`
- Resumo do que foi feito hoje
- Testes antes/depois
- Próximos passos

**Commit:**
```bash
git add -A
git commit -m "feat: disk cleanup, mission logger, batch approve, briefing, publisher connector

- FASE A: scripts/disk_cleanup.py + omnis disk analyze/clean
- FASE B: src/utils/mission_logger.py + decorator CLI
- FASE C: batch_approve() + omnis approvals batch + auto-export
- FASE D: health_score.py + briefing.py + omnis briefing
- FASE E: publisher_check.py expandido + omnis publisher status
- Testes: XXX/XXX passando

Closes: pipeline content → approval → export
Next: META OAuth (Fase 3)"
```

---

## REGRAS DE EXECUÇÃO

1. **Uma fase por vez.** Não pule. Não parallelize.
2. **Testes antes de avançar.** Se quebrar teste existente: pare, corrija, só então avance.
3. **Nunca ler .env.** Se precisar de variável, leia de `config/paths.yaml` ou pergunte.
4. **Nunca tocar em** `~/publisher-os/`, `~/.claude/`, `~/JARVIS_OS/`.
5. **Código Python simples.** Sem abstrações desnecessárias. Feynman rule: se não consegue explicar em 2 linhas, está complexo demais.
6. **Imports sempre do topo do módulo.** Sem imports circulares.
7. **Toda função nova tem docstring de 1 linha.**
8. **Se travar em algo > 15 min:** documente o bloqueio em `docs/BLOQUEIOS.md` e avance para a próxima fase.

---

## ENTREGÁVEL ESPERADO

Ao final desta missão, o OMNIS deve ter:

```
omnis disk analyze      → funciona
omnis disk clean        → funciona (com confirmação)
omnis briefing          → funciona (saúde + 3 ações)
omnis approvals batch   → funciona (41 drafts aprovados)
omnis publisher status  → funciona (leitura do Publisher OS)
python -m pytest        → 230+ testes passando (eram 213)
git log --oneline -1    → commit com mensagem correta
```

Se conseguir tudo isso, o OMNIS passa de **fábrica com fila** para **fábrica com painel de controle**.

A publicação real (OAuth Meta) fica para a próxima sessão — depois que o disco estiver limpo.

---

## INICIANDO

Comece com:

```bash
cd ~/omnis-control
python omnis.py doctor
python -m pytest tests/ -v --tb=short 2>&1 | tail -5
```

Confirme os 213 testes verdes.
Depois inicie a FASE A.

Bora.

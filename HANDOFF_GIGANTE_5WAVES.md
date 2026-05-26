# HANDOFF — GIGANTE 5 WAVES

**Data:** 2026-05-26
**Branch:** feature/omnis-5waves-runtime-supreme
**Commits desta sessão:** `272b5cb` `7aed68b` `6b39199` `141388e` (+ skills install)

---

## INSTALAÇÃO (pré-waves)

Skills instaladas em `.claude/skills/`:
- `omnis-content-cycle` — squad de conteúdo (Camada 3, carrossel, export)
- `akasha-memory-operator` — operador de memória Akasha
- `notion-connector` — conector Notion
- `aurora-context-builder` — construtor de contexto Aurora

`SQUADS_E_SKILLS_MASTER.md` copiado para `C:\Users\lucas\`

---

## WAVE 1 — Agência Camada 3: Carrossel + Thumbnail

**Commit:** `272b5cb`
**Módulo:** `src/agencia/carrossel.py`
**Testes:** `tests/agencia/test_carrossel.py` — 27/27

**O que faz:**
- `CarrosselGenerator(dry_run=True/False)`
- Gera capa + N slides de conteúdo + slide CTA + thumbnail
- Slides 1080×1080 PNG, thumbnail 1280×720 PNG
- Paleta de cores por perfil (6 perfis configurados)
- dry_run=True: manifesto JSON sem PNG
- dry_run=False: PNG reais em `output/agencia/<perfil>/<data>/`

**Uso:**
```python
from src.agencia.carrossel import CarrosselGenerator
gen = CarrosselGenerator(dry_run=False)
result = gen.generate(title="Hotel Vista Mar", slides=["item1","item2"], perfil="oinatalrn", output_dir=Path("output/agencia/oinatalrn/2026-05-26"))
```

**KRATOS pode exibir:** slides do carrossel via manifesto JSON

---

## WAVE 2 — Aurora Context Engine

**Commit:** `0ab4498` (sessão anterior)
**Módulo:** `src/aurora/context_engine.py`
**Testes:** 34/34

**Já funcionando:** unifica state.json + leads + Notion REST + Akasha pgvector.
Ver HANDOFF_AURORA_NOTION.md e HANDOFF_AURORA_AKASHA.md.

---

## WAVE 3 — Ciclo de Aprovação

**Commit:** `7aed68b`
**Módulos:** `src/cli_commands/content_cmd.py` + `src/cli.py`
**Testes:** `tests/test_content_cmd.py` — 13/13

**Comandos novos:**
```
omnis content list [--status draft|needs_review|approved|rejected] [--account @perfil]
omnis content approve <ID>
omnis content approve --batch [--limit N]
omnis content reject <ID> --reason "motivo"
omnis content status
```

**Prova:** 3 drafts válidos criados → `content approve --batch` → todos `approved` no storage

**KRATOS pode exibir:** contagem de drafts por status via GET /agent/status (já existe)

---

## WAVE 4 — Export para Publer/CSV

**Commit:** `6b39199`
**Módulos:** `src/agencia/export.py` + `content export` CLI
**Testes:** `tests/agencia/test_export.py` — 11/11

**O que faz:**
- `ContentExporter(dry_run=True/False)`
- Lê drafts APPROVED do DraftsManager
- Gera `data/exports/<date>-<id>/posts.csv` + `manifest.json`
- dry_run=False: copia PNGs de `output/agencia/` para `assets/`

**Formato CSV (Publer bulk import):**
```
account, caption, hashtags, cta, media_files, thumbnail, draft_id, notes
```

**Uso:**
```
omnis content export [--account @oinatalrn] [--real] [--output pasta/]
```

**Prova:** CSV gerado em `data/exports/2026-05-26-*/posts.csv` com dados reais

---

## WAVE 5 — Mission Logging

**Commit:** `141388e`
**Módulos:** `src/mission_logger/` + `src/cli_commands/mission_cmd.py`
**Testes:** `tests/test_mission_logger.py` — 20/20

**O que faz:**
- `MissionLogger` com context manager — registra inputs, outputs, warnings, erros, duração
- Append-only JSONL em `logs/mission_runs.jsonl`
- Falha silenciosa (não quebra execução se log indisponível)

**Uso:**
```python
from src.mission_logger import MissionLogger
with MissionLogger("carrossel", module="agencia.carrossel") as run:
    run.add_input("perfil", "oinatalrn")
    result = gen.generate(...)
    run.add_output("slides_count", result.slides_count)
```

**CLI:**
```
omnis runs list [--limit N] [--command carrossel] [--status success]
omnis runs show <run_id>
omnis runs log <command> [--status error] [--note "texto"]
```

**Prova:**
```
run_id=2703416fbc12 | command=carrossel | status=success | dur=14ms
outputs: session_id=e5457b7a, slides_count=5
```

---

## Suite final

```
169 passed em 10.63s
Módulos: agencia/ aurora/ test_content_cmd test_mission_logger test_export
```

---

## KRATOS pode exibir (próximas rotas a criar)

| Wave | Dado | Rota sugerida |
|---|---|---|
| 1 | Carrossel gerado | GET /content/carrossel/latest |
| 3 | Drafts pendentes | GET /content/approvals/pending |
| 4 | Último export | GET /content/export/latest |
| 5 | Mission runs | GET /runs/list |

---

## Zona vermelha não tocada (aguarda Lucas)

- OAuth Meta (publicação real no Instagram)
- Obsidian/Qdrant (Qdrant DOWN + 38.664 notas — onda pesada separada)
- Conectar MissionLogger ao CarrosselGenerator e ContentExporter (opcional — Lucas decide se quer logging automático ou manual)

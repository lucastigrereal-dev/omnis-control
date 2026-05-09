# Mission Builder — P3.0

Módulo determinístico: pedido em linguagem natural → plano estruturado → pacote offline.

**Nunca publica. Nunca chama Meta. Nunca aciona OAuth.**

## Arquitetura

```
src/mission_builder/
  __init__.py          — exports: build_plan, run, detect_intent
  errors.py            — IntentUnknownError, MissionPackageError
  models.py            — MissionPlan, MissionPackageManifest
  intent.py            — detect_intent() via config/intents.yaml
  planner.py           — build_plan()
  package_exporter.py  — export_package()
  executor.py          — run()

config/intents.yaml    — padrões de keyword por intent
```

### Isolation Lock

`src/mission_builder/` **não toca** `src/missions/`. As duas árvores são completamente separadas:

| Área | Responsabilidade |
|---|---|
| `src/missions/` | Runtime de execução — MissionContract, TaskState, checkpoints |
| `src/mission_builder/` | Planeamento offline — pedido → plano → pacote |

## Intents suportados

| Intent | Exemplo de pedido | Entregável |
|---|---|---|
| `carousel` | "cria um carrossel sobre turismo" | `carousel_package` |
| `reels` | "faz um reel de 30s" | `reels_package` |
| `campaign` | "campanha de 10 posts para hotel" | `campaign_package` |
| `post` | "post simples para o feed" | `single_post_package` |
| `story` | "stories para o Instagram" | `story_package` |
| `unknown` | (sem match) | `unknown` (erro por padrão) |

## Detecção de intent

`config/intents.yaml` define padrões de keyword por intent. A detecção:
- Converte para minúsculas e remove acentos (NFKD)
- Verifica cada padrão por substring (`pattern in normalized_text`)
- Primeiro match vence
- Fallback: `unknown`

## CLI

```powershell
# Ver plano (sem criar arquivos)
python jarvis.py mission-builder plan "cria um carrossel sobre praias de Natal"
python jarvis.py mission-builder plan "cria um carrossel" --account oinatalrn --json

# Criar pacote offline (dry-run por padrão)
python jarvis.py mission-builder run "cria uma campanha de 10 posts" --dry-run
python jarvis.py mission-builder run "cria um reel" --account lucastigrereal --json

# Aceitar intent desconhecido
python jarvis.py mission-builder plan "algo genérico" --allow-unknown
```

## Saída do pacote

```
exports/mission_packages/<mission_id>/
  01_mission_brief.md        — resumo da missão
  02_context_used.md         — contexto usado / a preencher
  03_execution_plan.md       — etapas com checkboxes
  04_outputs/                — (vazio) outputs gerados aqui
  05_exports/                — (vazio) exports finais aqui
  06_next_action.md          — comando exato para executar
  mission_manifest.json      — metadados da missão
```

O diretório `exports/mission_packages/` está no `.gitignore`.

## Fluxo

```
pedido (str)
  → detect_intent()      ← config/intents.yaml
  → build_plan()         → MissionPlan
  → export_package()     → MissionPackageManifest + 7 arquivos em disco
```

## Testes

```powershell
python -m pytest tests/mission_builder/ -v
# 48 passed
```

Cobertura: intent detection (5 intents + fallback), planner (account extract, slot count, unknown error), package exporter (arquivos obrigatórios, sem rede), executor (dry-run flag), CLI (plan + run + JSON).

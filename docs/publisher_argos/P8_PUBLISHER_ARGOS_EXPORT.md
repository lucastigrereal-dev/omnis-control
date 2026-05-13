# P8 PUBLISHER / ARGOS EXPORT SKELETON

## Visão Geral

Módulo `src/publisher_argos/` — skeleton determinístico, dry-run e stdlib-only para planejar exportação de conteúdo para o ARGOS publishing pipeline.

**NÃO publica. NÃO chama Meta/Instagram. NÃO chama ARGOS real.**

## Estrutura

```
src/publisher_argos/
├── __init__.py          # exports públicos
├── models.py            # dataclasses + enums (stdlib-only)
└── planner.py           # PublisherArgosPlanner — engine determinístico
```

## Modelos

| Modelo | Descrição |
|---|---|
| `PublishTarget` | Página alvo (handle, seguidores, canal) |
| `ArgosExportItem` | Item de conteúdo preparado para export ARGOS |
| `PublishReadinessCheck` | Resultado de validação de um item |
| `PublishQueuePlan` | Fila de itens para exportação |
| `ArgosExportPackage` | Pacote completo de exportação |
| `PublisherHandoff` | Registro de handoff do Publisher → ARGOS |

## Enums

| Enum | Valores |
|---|---|
| `PublishChannel` | `instagram_feed`, `instagram_story`, `instagram_reel` |
| `ExportStatus` | `draft`, `ready`, `queued`, `exported`, `blocked` |
| `ReadinessVerdict` | `pass`, `fail`, `pending_approval` |

## Serviço — PublisherArgosPlanner

Métodos:

| Método | Descrição |
|---|---|
| `build_export_item()` | Cria um ArgosExportItem a partir de caption + metadata |
| `validate_publish_readiness()` | Executa 5 checks determinísticos em um item |
| `build_queue_plan()` | Cria um PublishQueuePlan a partir de uma lista de itens |
| `build_argos_export_package()` | Cria pacote com readiness checks para todos os itens |
| `build_publisher_handoff()` | Cria registro de handoff (sempre approval_required) |
| `export_argos_json()` | Exporta handoff como string JSON |

### 5 Checks de Readiness

1. **has_caption** — caption não vazio
2. **has_target** — target com handle definido
3. **has_media_url** — media_url preenchido (bloqueia sem, mas não falha)
4. **caption_min_length** — mínimo 10 caracteres
5. **handle_is_known** — handle na lista de páginas conhecidas

### Páginas Conhecidas (hardcoded)

| Handle | Seguidores |
|---|---|
| `lucastigrereal` | 690K |
| `oinatalrn` | 630K |
| `agenteviajabrasil` | 452K |
| `afamiliatigrereal` | 320K |
| `oquecomernatalrn` | 249K |
| `natalaivoueu` | 240K |

## Regras de Segurança

1. **dry_run = True** — sempre, em todos os modelos e operações
2. **approval_required = True** — sempre, para qualquer publish futuro
3. **approved_by = None** — nunca auto-aprova
4. **export_argos_json()** retorna string — nunca escreve em disco automaticamente
5. Nenhuma chamada de rede, Meta API, ou ARGOS real
6. Stdlib-only: sem dependências externas

## Testes

```bash
python -m pytest tests/publisher_argos/ -q
```

Cobertura:
- `test_models.py` — 24 testes: todos os modelos, defaults, transições de estado, to_dict
- `test_planner.py` — 30+ testes: build, validate, queue, package, handoff, export JSON, temp path

## Uso

```python
from src.publisher_argos import PublisherArgosPlanner, PublishChannel

planner = PublisherArgosPlanner()

# 1. Criar item
item = planner.build_export_item(
    caption="Meu post de viagem em família! ✈️",
    handle="afamiliatigrereal",
    channel=PublishChannel.INSTAGRAM_FEED,
    media_url="https://cdn.example.com/foto.jpg",
    tags=["viagem", "família"],
)

# 2. Validar
check = planner.validate_publish_readiness(item)
print(check.verdict)  # 'pass'

# 3. Criar fila
qp = planner.build_queue_plan(items=[item], label="Lote Manhã")

# 4. Criar pacote
pkg = planner.build_argos_export_package(qp, label="Export 2026-05-13")

# 5. Criar handoff
handoff = planner.build_publisher_handoff(pkg)

# 6. Exportar JSON
json_str = planner.export_argos_json(handoff)
print(json_str)
```

## Status

- **Phase:** P8 Publisher / ARGOS Export Skeleton
- **Status:** ✅ Complete
- **Tests:** Pass
- **Dependencies:** stdlib only (dataclasses, enum, json, uuid, datetime)
- **Network:** None
- **LLM:** None
- **Database:** None

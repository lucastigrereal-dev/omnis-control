# P12 Automation/n8n Skeleton — Relatório Final

## Visão Geral
Frente P12 AUTOMATION/N8N SKELETON do OMNIS.
Skeleton seguro para modelagem de automações e workflows.
**Modo dry-run** — sem chamadas reais ao n8n, sem Docker, sem rede.

## Arquitetura

```
src/automation/
|-- __init__.py     # Public API surface
|-- models.py       # Dataclass models (4 entidades)
|-- errors.py       # Exception hierarchy (6 erros)
|-- service.py      # Planner + Exporter + Validator
```

## Entidades

### AutomationTrigger
Gatilho de workflow. Tipos: `webhook`, `schedule`, `manual`, `mission_completed`.

| Campo | Tipo | Descrição |
|---|---|---|
| trigger_id | str | ID único (trig_XXXXXXXX) |
| trigger_type | str | Tipo do gatilho |
| config | dict | Configuração do gatilho |
| enabled | bool | Ativo/inativo |

### AutomationStep
Passo individual do workflow. Tipos: `http_request`, `transform`, `filter`, `merge`, `delay`, `notify`.

| Campo | Tipo | Descrição |
|---|---|---|
| step_id | str | ID único (step_XXXXXXXX) |
| name | str | Nome legível |
| step_type | str | Tipo do passo |
| config | dict | Configuração |
| position | int | Ordem visual |
| depends_on | list[str] | Dependências (step_ids) |

### AutomationWorkflow
Workflow completo: trigger + steps.

| Campo | Tipo | Descrição |
|---|---|---|
| workflow_id | str | ID único (wf_XXXXXXXX) |
| name | str | Nome do workflow |
| description | str | Descrição |
| trigger | AutomationTrigger | Gatilho |
| steps | list[AutomationStep] | Passos |
| active | bool | Ativo |
| created_at | str | ISO UTC |
| updated_at | str | ISO UTC |

### AutomationRunPlan
Plano de execução determinístico.

| Campo | Tipo | Descrição |
|---|---|---|
| run_id | str | ID único (run_XXXXXXXX) |
| workflow_id | str | Workflow pai |
| status | str | planned/running/completed/failed |
| steps_to_execute | list[str] | Step IDs em ordem topológica |
| dry_run | bool | Sempre True neste skeleton |

## Serviços

### WorkflowPlanner
Planejador determinístico:
1. Recebe `AutomationWorkflow`
2. Resolve dependências (Kahn's algorithm)
3. Detecta ciclos
4. Produz `AutomationRunPlan` com ordem topológica

Complexidade: O(V + E)

### export_n8n_spec()
Exporta workflow como JSON compatível conceitualmente com n8n:
- Mapeia trigger types → n8n-nodes-base.*
- Mapeia step types → n8n-nodes-base.*
- Gera nodes + connections no formato n8n
- Metadata: dry_run=True, exporter=P12-automation-skeleton

### validate_workflow()
Validador estrutural:
- Verifica: nome vazio, sem steps, dependências não resolvidas, ciclos
- Warnings: posições duplicadas, trigger desabilitado
- Retorna `ValidationResult(valid, errors, warnings)`

## Constantes de Domínio

### Trigger Types
| Constante | Valor |
|---|---|
| TRIGGER_WEBHOOK | "webhook" |
| TRIGGER_SCHEDULE | "schedule" |
| TRIGGER_MANUAL | "manual" |
| TRIGGER_MISSION_COMPLETED | "mission_completed" |

### Step Types
| Constante | Valor |
|---|---|
| STEP_HTTP_REQUEST | "http_request" |
| STEP_TRANSFORM | "transform" |
| STEP_FILTER | "filter" |
| STEP_MERGE | "merge" |
| STEP_DELAY | "delay" |
| STEP_NOTIFY | "notify" |

### Run Statuses
| Constante | Valor |
|---|---|
| RUN_PLANNED | "planned" |
| RUN_RUNNING | "running" |
| RUN_COMPLETED | "completed" |
| RUN_FAILED | "failed" |

## Mapeamento n8n (Conceitual)
| Internal Type | n8n Node Type |
|---|---|
| http_request | n8n-nodes-base.httpRequest |
| transform | n8n-nodes-base.function |
| filter | n8n-nodes-base.if |
| merge | n8n-nodes-base.merge |
| delay | n8n-nodes-base.wait |
| notify | n8n-nodes-base.emailSend |
| webhook | n8n-nodes-base.webhook |
| schedule | n8n-nodes-base.scheduleTrigger |

## Testes
- `tests/automation/test_models.py` — 21 testes (triggers, steps, workflows, run plans, constants)
- `tests/automation/test_service.py` — 24 testes (topological sort, planner, spec export, validation)

Total: **45 testes**. Zero LLM, zero network, zero Docker.

## Execução
```bash
python -m pytest tests/ -q
```

## Design Decisions
1. **Dataclasses, não Pydantic** — performance, zero dependências extras
2. **Kahn's Algorithm** — determinístico, O(V+E), detecção de ciclos built-in
3. **n8n spec é JSON puro** — compatível conceitualmente, sem chamar API
4. **ValidationResult como dataclass** — sem exceções para validação (retorna resultado composto)
5. **Erros tipados** — hierarquia de exceções para debug granular

## Limitações (by design)
- Não chama n8n real
- Não usa Docker
- Não usa rede
- Não integra CLI
- Não persiste em JSONL (futuro: AutomationStore)

## Próximo Passo
Quando n8n real estiver disponível: trocar `export_n8n_spec()` para POST real na API do n8n, mantendo o dry-run como fallback.

---

Gerado em: 2026-05-12 | Frente P12 | Modo dry-run | 0 LLM | 0 network | 0 Docker

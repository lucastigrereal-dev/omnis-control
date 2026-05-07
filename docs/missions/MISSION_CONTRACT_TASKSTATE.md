# MISSION CONTRACT + TASKSTATE — P0.5

**Event-Sourced Foundation do OMNIS Control**

## Conceito

Mission Contract é o "cartório" do OMNIS. TaskState é o "diário de bordo".
Juntos implementam **Event Sourcing**: o estado é projeção determinística de
um contrato imutável + eventos append-only ordenados.

## Componentes

### 1. MissionContract (`src/missions/models.py`)
Contrato imutável (Pydantic v2 `frozen=True, extra="forbid"`):
- `title`, `objective`, `sector` — obrigatórios
- `budget` (BudgetCaps) — max_tokens, max_cost_usd, max_duration_seconds, max_steps
- `acceptance_criteria` — lista de AcceptanceCriterion
- `content_hash()` — SHA-256 do JSON canônico (excluindo `created_at`)

### 2. EventEnvelope (`src/missions/events.py`)
25 tipos de evento append-only, sequenciados por missão:
- **Lifecycle**: mission_created, mission_started, mission_completed, mission_failed, mission_cancelled
- **Steps**: step_started, step_completed
- **Tools**: tool_invoked, tool_returned
- **Skills**: skill_invoked, skill_returned
- **Approvals**: approval_requested, approval_granted, approval_rejected
- **Artifacts**: artifact_produced, artifact_linked
- **Errors**: error_logged, retry_attempted
- **Budget**: budget_exceeded, token_used, cost_incurred
- **Control**: mission_paused, mission_resumed
- **Planning**: plan_drafted, plan_approved

### 3. TaskState (`src/missions/state.py`)
Projeção calculada via `project_from_events(contract, events)`:
- Determinístico — mesma entrada = mesma saída
- Cumulative tokens/cost mantém o máximo entre eventos

### 4. State Machine (`src/missions/state_machine.py`)
7 estados com transições validadas:
```
draft → running → waiting_approval → running → completed
                 ↘ paused → running
                 ↘ failed → running
                 ↘ cancelled
```
- `completed` e `cancelled` são terminais
- `failed` pode retornar a `running`
- `budget_exceeded` sempre vai para `waiting_approval` (trava dura)

### 5. JsonlRepository (`src/missions/repository.py`)
Storage file-based MVP:
- Contracts: `data/missions/contracts/{hash}.json` + `{hash}.hash`
- Events: `data/missions/events/{hash}.jsonl`
- Index: `data/missions/index.jsonl`
- Hash verification no load (ContractTamperedError)
- Sequence validation no append (SequenceGapError)
- Cálculo automático de cumulative tokens/cost

### 6. CLI (`src/cli_commands/missions_cmd.py`)
```bash
python jarvis.py mission create --title "..." --objective "..." --sector research
python jarvis.py mission list [--status running] [--json]
python jarvis.py mission show <mission_id>
python jarvis.py mission state <mission_id> [--json]
```

## Decisões de Arquitetura

| Decisão | Escolha | Motivo |
|---|---|---|
| Modelo | Pydantic v2 frozen | Validação forte + serialização confiável |
| Storage | JSONL file-based | Simples, auditável, sem dependência de banco |
| Hash | SHA-256 de JSON canônico | Determinístico cross-platform |
| Setores | 11 setores OMNIS | Domínio genérico, não só JARVIS mídia |
| Budget | Trava dura em waiting_approval | Segurança contratual |
| Repository | Instância normal (não singleton) | Isolamento em testes |
| Sequence | Por missão, sem gaps | Integridade do log |

## Roadmap P0.6+

- Snapshot caching para projeção rápida com muitos eventos
- File lock cross-platform (msvcrt/fcntl)
- Mission tree (parent_mission_id com navegação)
- `mission validate` — verificar acceptance criteria
- Integração com pipeline real de execução
- Migração para Postgres/Akasha quando modelo provado

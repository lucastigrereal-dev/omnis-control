# AGENT_FLOW

Gerado: 2026-05-23  
Base: codigo real em `src/cli_agent.py`, `src/agentic/`, `src/memory/caption_memory.py` e `src/api/`.

## 1. QueueItem -> legenda aprovada

O fluxo operacional atual e executado por `src.agentic.caption_draft_agent.CaptionDraftAgent`.

Entrada:

- `queue_id` vindo do CLI `omnis agent run <queue_id>` ou de `BatchRunner`.
- Item carregado por `src.content_queue.queue.Queue`.
- Contexto de memoria vindo de `src.memory.interface.MemoryInterface`.
- LLM via `MockLLMAdapter` quando `dry_run=True`; via `LiteLLMAdapter` quando `dry_run=False`.

Steps registrados no `AgentRun`:

| ordem | step | modulo | efeito real |
|---:|---|---|---|
| 1 | `fetch_queue_item` | `CaptionDraftAgent._fetch_queue_item` | Busca o `QueueItem`; se nao existe, marca `AgentRun` como failed. |
| 2 | `query_memory` | `CaptionDraftAgent._query_memory` | Consulta `MemoryInterface.query()` usando conta e objetivo. |
| 3 | `generate_caption` | `CaptionDraftAgent._generate_caption` | Monta `CaptionPromptInput` e chama o adapter LLM configurado. |
| 4 | `create_draft` | `CaptionDraftAgent._persist_draft` | Em dry-run cria `draft_id` fake; em real cria draft via `DraftsManager.create()`. |
| 5 | `approval_gate` | `CaptionDraftAgent._run_approval_gate` | Em dry-run simula aprovado; em real submete, valida e aprova via `ApprovalGate`. |
| 6 | `memory_writeback` | `CaptionDraftAgent._write_memory` | Grava memoria de legenda aprovada via `CaptionMemoryWriter` apenas quando aprovado. |

Quando o gate aprova no modo real:

1. `DraftsManager.submit(draft_id)` coloca o draft em revisao.
2. `ApprovalGate.validate(...)` valida texto, hashtags e CTA.
3. `ApprovalGate.approve(...)` aprova o draft.
4. O callback `_queue_updater` chama `Queue.update(queue_id, status=QueueStatus.CAPTION_READY)`.
5. `CaptionMemoryWriter.write(...)` persiste a legenda aprovada em `data/caption_memory.jsonl`.

Resultado do `AgentRun.complete()`:

- `draft_id`
- `caption_len`
- `hashtags`
- `model_used`
- `tokens_used`
- `memory_patterns`
- `gate_verdict`
- `gate_blocks`
- `queue_status`
- `memory_written`
- `dry_run`

Persistencia de runs:

- `AgentRunRepository` grava em `data/agent_runs.jsonl`.

## 2. BatchRunner

Modulo: `src.agentic.batch_runner.BatchRunner`.

O `BatchRunner` processa varios `QueueItem` em sequencia.

Selecao:

- Fonte: `Queue.list_all()`.
- Status padrao: `planned` e `needs_caption` (`PROCESSABLE_STATUSES`).
- Filtro opcional por conta: `account_filter`.
- Filtro opcional por status: `status_filter`.
- Limite: `limit`.

Execucao:

1. `_select_candidates(...)` escolhe os itens.
2. `_process_item(...)` chama `CaptionDraftAgent.run(item.queue_id)` para cada candidato.
3. Cada resultado vira `BatchItemResult`.
4. O lote final vira `BatchReport`.

Veredictos conhecidos:

- `approved`
- `approved_dry`
- `needs_review`
- `failed`
- `skipped`

O `BatchRunner` nao cria daemon e nao agenda por conta propria. Ele apenas processa um lote no momento da chamada.

## 3. SchedulerService

Modulo: `src.agentic.scheduler.SchedulerService`.

O scheduler nao roda como daemon. Ele persiste configuracoes e executa schedules vencidos quando alguem chama `run_due()`.

Arquivos:

- Schedules: `data/agent_schedules.jsonl`.
- Historico: `data/agent_schedule_runs.jsonl`.

Modelo:

- `BatchSchedule`: configuracao recorrente com `interval_hours`, `next_run_at`, `run_count`, filtros e modo dry/real.
- `ScheduleRun`: registro historico de cada execucao.

Fluxo de `run_due()`:

1. Lista schedules com `ScheduleRepository.list_all()`.
2. Filtra apenas `s.is_due`.
3. Para cada schedule vencido:
   - cria `BatchRunner` via factory;
   - executa `runner.run(limit=schedule.limit, account_filter=schedule.account_filter)`;
   - registra `ScheduleRun`;
   - chama `schedule.advance()`;
   - salva schedule atualizado;
   - salva historico.

## 4. CLI commands

Arquivo: `src/cli_agent.py`.

| comando | funcao | modulo acionado | comportamento |
|---|---|---|---|
| `omnis agent run <queue_id>` | `agent_run` | `CaptionDraftAgent` | Executa um item da fila. Em `--real`, exige LiteLLM disponivel. |
| `omnis agent runs` | `agent_runs` | `AgentRunRepository` | Lista historico de runs, com filtros por conta e limite. |
| `omnis agent batch` | `agent_batch` | `BatchRunner` | Processa N itens `planned`/`needs_caption`. |
| `omnis agent schedule-add` | `schedule_add` | `SchedulerService.add` | Cria schedule recorrente. |
| `omnis agent schedule-list` | `schedule_list` | `SchedulerService.list_schedules` | Lista schedules persistidos. |
| `omnis agent schedule-run` | `schedule_run` | `SchedulerService.run_due` | Executa schedules vencidos. |
| `omnis agent schedule-remove` | `schedule_remove` | `SchedulerService.remove` | Remove schedule por ID. |
| `omnis agent schedule-history` | `schedule_history` | `SchedulerService.history` | Lista historico de schedules. |
| `omnis agent memory` | `agent_memory` | `CaptionMemoryReader` | Mostra contagem ou legendas aprovadas similares. |
| `omnis agent status` | `agent_status` | Queue, AgentRunRepository, SchedulerService, CaptionMemoryReader, LiteLLMAdapter | Painel read-only da camada agentic. |

## 5. API endpoints para KRATOS

Arquivo raiz: `src/api/main.py`.

A API e read-only e registra os routers abaixo:

| prefixo | router | dados expostos |
|---|---|---|
| `/health` | `src.api.routers.health` | Health operacional. |
| `/queue` | `src.api.routers.queue` | Itens da fila e item por ID. |
| `/accounts` | `src.api.routers.accounts` | Contas e contas ativas. |
| `/drafts` | `src.api.routers.drafts` | Drafts e draft por ID. |
| `/assets` | `src.api.routers.assets` | Assets e asset por ID. |
| `/missions` | `src.api.routers.missions` | Missoes e missao por ID. |
| `/skills` | `src.api.routers.skills` | Skills/catalogo exposto. |
| `/reports` | `src.api.routers.reports` | Status report e briefing. |
| `/agent` | `src.api.routers.agent` | Runs, schedules, historico e memoria agentic. |

Endpoints agentic especificos:

| endpoint | fonte real |
|---|---|
| `GET /agent/runs` | `AgentRunRepository.list_all()` |
| `GET /agent/runs/{run_id}` | `AgentRunRepository.list_all()` filtrado por ID |
| `GET /agent/schedules` | `ScheduleRepository.list_all()` |
| `GET /agent/schedules/{schedule_id}/history` | `ScheduleRunRepository.for_schedule(schedule_id)` |
| `GET /agent/memory` | `CaptionMemoryReader.count(account)` |

## 6. Limites atuais

- API HTTP e read-only.
- `SchedulerService` nao e daemon: precisa ser chamado por CLI, cron, Task Scheduler ou outro orquestrador.
- Modo real depende de `LiteLLMAdapter.health_check()` apontando para o gateway configurado.
- `CaptionMemory` e JSONL local, sem transacao multi-processo.
- `BatchRunner` processa itens sequencialmente.


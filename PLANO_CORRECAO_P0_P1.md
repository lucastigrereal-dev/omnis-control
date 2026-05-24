# PLANO_CORRECAO_P0_P1

Data: 2026-05-24  
Modo: **PLANO APENAS** (sem execução)  
Base: itens 🔴 mapeados em `AVALIACAO_ESTRUTURAL.md` + validação de linhas no código atual

---

## Escopo e regra desta entrega

- Este documento **não executa nenhuma correção**.
- Objetivo: priorizar P0/P1 com evidência objetiva (arquivo:linha), impacto e dono da correção.
- Classificação de execução:
  - **Mecânica (Codex)**: mudança reversível que não altera semântica de negócio.
  - **Muda comportamento (Claude Code / Opus decide)**: exige decisão de comportamento/arquitetura.

---

## P0 — Segurança / risco que não pode esperar

### P0.1 Credenciais dev hardcoded em memória/config

| Item | Arquivo:linha | Problema | Risco | Tipo de correção | Executor |
|---|---|---|---|---|---|
| DSN default com usuário/senha inline | `src/memory/akasha_reader.py:9` | Fallback de `AKASHA_DSN` contém credencial explícita (`postgresql://akasha:akasha123@...`) | Vazamento acidental em ambientes indevidos + portabilidade fraca | **Muda comportamento** (troca fallback por fail-fast/env obrigatório) | Claude Code |
| DSN explícito em texto de módulo | `src/memory/akasha_reader.py:4` | String de conexão sensível aparece no bloco de documentação/cabeçalho | Normaliza cultura de credencial em código | **Mecânica** (higienização de texto) | Codex |
| Conexão psycopg2 com `password=postgres` hardcoded | `src/memory_unification/memory_router.py:230` | Credencial fixa no código | Risco de segurança + quebra fora do localhost | **Muda comportamento** (depende de contrato de env/config) | Claude Code |
| Conexão psycopg2 com `password=postgres` hardcoded | `src/memory_unification/memory_router.py:261` | Credencial fixa no código | Mesmo risco do item anterior | **Muda comportamento** | Claude Code |

### Ordem sugerida (P0)
1. Definir contrato único de variáveis de ambiente para DSN (decisão de construção).  
2. Trocar os hardcoded por leitura de env + erro explícito quando ausente.  
3. Rodar regressão focada de memória e depois suíte completa.  
4. Só depois higienizar textos/comentários remanescentes.

---

## P1 — Fragilidade de runtime (workflows com sink/construtor frágil)

### P1.1 Instanciação de classe abstrata `AkashaSinkAdapter()`

| Workflow | Arquivo:linha | Fragilidade | Tipo de correção | Executor |
|---|---|---|---|---|
| `capability_forge` | `src/workflows/capability_forge_workflow.py:74` | Instancia classe abstrata por default | **Muda comportamento** (definir sink default real) | Claude Code |
| `content_quality` | `src/workflows/content_quality_workflow.py:79` | Instancia classe abstrata por default | **Muda comportamento** | Claude Code |
| `deliverable_mapping` | `src/workflows/deliverable_mapping_workflow.py:85` | Instancia classe abstrata por default | **Muda comportamento** | Claude Code |
| `task_dispatch` | `src/workflows/task_dispatch_workflow.py:63` | Instancia classe abstrata por default | **Muda comportamento** | Claude Code |
| `squad_assignment` | `src/workflows/squad_assignment_workflow.py:58` | Instancia classe abstrata por default | **Muda comportamento** | Claude Code |
| `metrics_snapshot` | `src/workflows/metrics_snapshot_workflow.py:64` | Instancia classe abstrata por default | **Muda comportamento** | Claude Code |

### P1.2 `FileAkashaSink()` sem `target_dir` obrigatório

| Workflow | Arquivo:linha | Fragilidade | Tipo de correção | Executor |
|---|---|---|---|---|
| `caption_generator` | `src/workflows/caption_generator_workflow.py:99` | `FileAkashaSink()` chamado sem `target_dir` (assinatura exige) | **Muda comportamento** (definir caminho canônico + política dry_run) | Claude Code |
| `content_brief` | `src/workflows/content_brief_workflow.py:186` | Mesmo problema de construtor | **Muda comportamento** | Claude Code |
| `hotel_pitch` | `src/workflows/hotel_pitch_workflow.py:173` | Mesmo problema de construtor | **Muda comportamento** | Claude Code |

### Observação de escopo
- O item acima é de **runtime**, não de estilo.  
- Qualquer “default sink” aqui mexe em persistência/log de execução, então fica com a frente de construção.

---

## P1 — Dívida de arquitetura (dois trilhos de orquestração)

> Pedido explícito atendido: descrever conflito **sem propor fusão agora**.

### Conflito observado

| Trilho | Evidência | O que faz | Risco |
|---|---|---|---|
| Trilho A (agentic + workflow registry) | `src/agentic/mission_orchestrator.py` (refs `WorkflowRegistry`, `orchestrate`) | Orquestra `brief → agency → workflow registry → sink` | Pode ficar paralelo/duplicado sem ser o caminho principal da CLI |
| Trilho B (mission_orchestrator service/executor + graph bridge) | `src/mission_orchestrator/service.py`, `src/mission_orchestrator/executor.py`, `src/execution_graph/mission_bridge.py`, `src/cli_commands/mission_orchestrator_cmd.py` | Fluxo operacional usado pela CLI (`plan/run/run_full`) com gating e graph | Divergência de responsabilidade e pontos de verdade |

### Classificação para ação
- **Tipo:** Muda comportamento / decisão de arquitetura.  
- **Executor:** Opus decide direção; Claude Code implementa depois da decisão.  
- **Codex nesta fase:** apenas manter auditoria e testes de regressão entre os dois caminhos.

---

## Plano priorizado (resumo executivo)

1. **P0 imediato:** remover hardcoded de credenciais em memória/config com contrato de env definido.  
2. **P1 runtime:** corrigir defaults de sink/construtores frágeis nos workflows listados.  
3. **P1 arquitetura:** registrar decisão formal sobre trilho oficial de orquestração (sem executar fusão nesta etapa).

---

## Gate de validação (quando a execução começar)

- Gate P0:
  - testes de memória/memory_unification verdes;
  - ausência de credencial hardcoded nos pontos listados.
- Gate P1 runtime:
  - workflows com construtor corrigido executam sem `TypeError/abstract instantiation`.
- Gate regressão:
  - suíte completa sem queda de baseline.


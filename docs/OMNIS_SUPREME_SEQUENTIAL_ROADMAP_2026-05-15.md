# OMNIS SUPREME — Roadmap Sequencial Oficial para Runtime Real

**Date:** 2026-05-15
**Status:** Oficial
**Branch baseline:** `feature/omnis-5waves-runtime-supreme` @ `8c32ecf`

---

## Principios

1. **Local-first** — Tudo roda local antes de qualquer integracao externa
2. **Dry-run por padrao** — `dry_run=True` como default universal
3. **Approval antes de efeitos externos** — Nada real sem aprovacao humana
4. **Contrato antes de runtime real** — Interface definida antes do adapter real
5. **Mock fallback antes de adapter real** — File-backed/mock sempre disponivel como fallback
6. **Observabilidade antes de autonomia real** — Metricas e logs antes de acoes sem supervisao
7. **Akasha antes de controle remoto** — Memoria solida antes de canais externos
8. **Sem credencial real sem boundary** — Credenciais cercadas por feature flag + fallback
9. **Uma fase por vez** — Sequential, nunca paralelo em fases com side effects
10. **Teste antes de merge** — Full suite verde entre cada fase
11. **Relatorio antes da proxima fase** — Handoff documentado antes de avancar
12. **Lucas decide, OMNIS executa dentro do cercado** — Humano no controle, maquina no cercado de seguranca

---

## Estado atual

| Metric | Value |
|---|---|
| Features entregues (P1-P45) | 45 funcionalidades |
| Waves completas (W8-W12) | 5 waves, 50 blocos |
| Source files Python | 593 |
| Test files | 465 |
| Full suite | 5,902 passed, 3 skipped, 0 failures |
| Tempo full suite | ~17 min |
| dry_run coverage | 100% |
| Branch atual | `feature/omnis-5waves-runtime-supreme` |
| Commits ahead of master | 37 |
| Merge status | PENDING — P46 em execucao |
| Wave 13 | Planejada — ver `OMNIS_W12B9_WAVE_13_NEXT_PLAN.md` |

### O que ja foi feito

```
P1-P20:  Fundacao + Supreme Activation
P21-P24: Memory Intelligence, Capability Forge Real, Autonomous Execution, Live Cockpit
P25-P29: Multi-Model Orchestration, App Factory, Real World Actions, Self-Improvement, OS Layer
P30-P36: Control Tower / Wave 7A
P37-P45: Runtime Bridge / Wave 7B
W8:      Skill Execution Prep (9 blocks)
W9:      Akasha Runtime Prep (9 blocks)
W10:     Remote Control Architecture (9 blocks)
W11:     MCP/Plugin Architecture (7 blocks)
W12:     Governance & QA (10 documents)
```

### Arquitetura atual

```
                    ┌──────────────────────┐
                    │   RemoteCommandRouter │  W10
                    │   (Telegram/WhatsApp) │
                    └──────────┬───────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ SkillExecution  │  │ AkashaRuntime   │  │ PluginRuntime   │
│ Service (W8)    │  │ Service (W9)    │  │ (W11)           │
│                 │  │                 │  │                 │
│ PermissionGate  │  │ WritePolicy     │  │ PermissionGate  │
│ BoundaryChecker │  │ EventMapper     │  │ ManifestReader  │
│ DryRunExecutor  │  │ DedupRegistry   │  │ MCPDescriptor   │
│ EventBus        │  │ FileAdapter     │  │ Plugin Registry │
│ ArtifactReg     │  │ HealthChecker   │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

---

## Fluxo de fases — Wave 13 rumo ao Supreme RC

```
P46 ──► P47 ──► P48 ──► P49 ──► P50 ──► P51 ──► P52 ──► P53 ──► P54 ──► P55 ──► P56
 │       │       │       │       │       │       │       │       │       │       │
Merge   Akasha  Obser-  MCP    Tele-  Whats-  Prod   KRATOS  First   Real   Supreme
Readi-  Real    vabi-   Real   gram   App     Hard-  Con-    E2E     Action   RC
ness    Sink    lity           Real   Plan    ening  tract   DryRun+ Pilot
```

---

## P46 — Merge Readiness Final

| Field | Detail |
|---|---|
| **Objetivo** | Validar se `feature/omnis-5waves-runtime-supreme` esta pronta para merge em `master` |
| **Por que vem nessa ordem** | Pre-condicao para qualquer proximo passo. Sem merge, tudo fica na branch. |
| **Dependencias** | P1-P45 + W8-W12 concluidos |
| **Arquivos permitidos** | `docs/OMNIS_P46_*.md`, `docs/OMNIS_BRANCH_*.md`, `docs/OMNIS_TEST_*.md`, `docs/OMNIS_SUPREME_SEQUENTIAL_ROADMAP_*.md` |
| **Arquivos proibidos** | `src/`, `tests/`, `config/` (exceto leitura) |
| **Comandos seguros** | `git status`, `git log`, `git branch`, `git worktree list`, `git rev-list`, `python -m pytest` |
| **Comandos proibidos** | `git push`, `git merge`, `git rebase`, `git reset --hard`, `git clean`, `rm`, `docker` |
| **Entregaveis** | `OMNIS_P46_MERGE_READINESS_FINAL.md`, `OMNIS_BRANCH_AND_WORKTREE_AUDIT.md`, `OMNIS_TEST_READINESS_SUMMARY.md`, `OMNIS_SUPREME_SEQUENTIAL_ROADMAP_2026-05-15.md` |
| **Criterios de aceite** | Full suite passa, working tree explicado, branch correta, sem secrets tocados, decisao final clara |
| **Testes obrigatorios** | Full suite: `python -m pytest tests/ --import-mode=importlib -p no:warnings -q` |
| **Seguranca** | dry_run preservado, secrets nao acessados, APIs mockadas, approval gates intactos |
| **Rollback** | N/A — fase somente leitura + documentacao |
| **Sinais de bloqueio** | Full suite falha, working tree com arquivos criticos modificados, secrets detectados |
| **Prompt executor** | "Executar P46 — Merge Readiness Final no OMNIS Control" |
| **Condicao para proxima fase** | Verdict MERGE_READY ou MERGE_READY_WITH_NOTES + merge executado com sucesso em master |

---

## P47 — Real Akasha Sink

| Field | Detail |
|---|---|
| **Objetivo** | Sair de file-backed/mock Akasha para conector real controlado ao Akasha pgvector/Postgres |
| **Por que vem nessa ordem** | Akasha e a fundacao de memoria. Sem ele, nenhum writeback real funciona. E o primeiro passo logico apos merge porque nao envolve canais externos (Telegram/WhatsApp) — e uma integracao interna controlada. |
| **Dependencias** | P46 concluido (merge em master), Akasha pgvector disponivel |
| **Arquivos permitidos** | `src/akasha_runtime/`, `tests/akasha_runtime/`, `docs/OMNIS_P47_*.md`, `docs/OMNIS_AKASHA_*.md` |
| **Arquivos proibidos** | `.env`, `src/remote_control/`, `src/plugin_runtime/` (real parts) |
| **Comandos seguros** | `python -m pytest tests/akasha_runtime/`, `git status`, `git diff` |
| **Comandos proibidos** | `docker compose down`, `psql` com credenciais reais sem autorizacao, `rm -rf` |
| **Entregaveis** | Real Akasha adapter, health check real, write policy com boundary, dedup keys reais, benchmark minimo, `OMNIS_P47_REAL_AKASHA_SINK_REPORT.md`, `OMNIS_AKASHA_RUNTIME_BOUNDARY.md` |
| **Criterios de aceite** | Mock continua passando como fallback, real adapter pode ser desligado via flag, health check nao vaza secret, writeback so em namespace permitido, testes mock + integration passam |
| **Testes obrigatorios** | `tests/akasha_runtime/` completo + novos integration tests com real adapter |
| **Seguranca** | Real adapter atras de feature flag (`AKASHA_REAL_ENABLED=false` default), connection string nunca hardcoded, sem log de credenciais, sem acesso a namespaces fora do permitido |
| **Rollback** | Desligar feature flag → volta para file-backed adapter |
| **Sinais de bloqueio** | pgvector indisponivel, credenciais ausentes, schema migration pendente |
| **Prompt executor** | "Executar P47 — Real Akasha Sink. Conectar ao Akasha pgvector atras de feature flag. Manter file-backed como fallback." |
| **Condicao para proxima fase** | Mock passa + real adapter funcional + testes verdes + relatorio aprovado |

---

## P48 — Observability Baseline Real

| Field | Detail |
|---|---|
| **Objetivo** | Antes de canais externos reais, criar camada de observabilidade operacional |
| **Por que vem nessa ordem** | Telegram e WhatsApp sao canais externos. Antes de abri-los, precisamos ver o que esta acontecendo no runtime. Observabilidade vem antes de qualquer canal que possa gerar eventos externos. |
| **Dependencias** | P47 concluido (Akasha real operando) |
| **Arquivos permitidos** | `src/health/`, novos `src/observability/`, `tests/observability/`, `docs/OMNIS_P48_*.md` |
| **Arquivos proibidos** | `src/remote_control/` (real adapters), secrets, .env |
| **Comandos seguros** | `python -m pytest tests/observability/`, `python -m pytest tests/health/` |
| **Comandos proibidos** | Exportar metricas para externo, abrir portas de metrics, docker sem autorizacao |
| **Entregaveis** | Structured logging (structlog), metricas locais, health aggregation, traces de execucao com trace_id/correlation_id, eventos por stage, latency/error counters, alertas locais, `OMNIS_P48_OBSERVABILITY_BASELINE_REPORT.md`, `OMNIS_RUNTIME_HEALTH_MODEL.md` |
| **Criterios de aceite** | Cada execucao tem trace_id/correlation_id, cada stage loga start/success/fail, falhas ficam auditaveis, metricas acessiveis localmente |
| **Testes obrigatorios** | Testes de eventos/metricas, smoke test de health aggregation |
| **Seguranca** | Nenhuma metrica exportada para externo sem aprovacao, sem credenciais em logs, trace_id sem dados sensiveis |
| **Rollback** | Desligar structured logging → volta para print/logging basico |
| **Sinais de bloqueio** | Dependencia pesada nao aprovada, porta de metrics conflitante |
| **Prompt executor** | "Executar P48 — Observability Baseline. Adicionar structured logging, metricas locais, health aggregation. Nada externo." |
| **Condicao para proxima fase** | Observabilidade funcional + health checks agregados + relatorio aprovado |

---

## P49 — Real MCP Bridge

| Field | Detail |
|---|---|
| **Objetivo** | Sair do plugin runtime mock para MCP bridge real controlada |
| **Por que vem nessa ordem** | MCP bridge e a camada de ferramentas. Com Akasha real e observabilidade, temos onde persistir e como monitorar. MCP vem antes de Telegram porque as tools que o Telegram vai disparar precisam existir. |
| **Dependencias** | P47 (Akasha real), P48 (observability) |
| **Arquivos permitidos** | `src/plugin_runtime/`, `tests/plugin_runtime/`, `docs/OMNIS_P49_*.md`, `docs/OMNIS_MCP_*.md` |
| **Arquivos proibidos** | Tokens MCP hardcoded, .env |
| **Comandos seguros** | `python -m pytest tests/plugin_runtime/` |
| **Comandos proibidos** | Spawn de processos MCP sem sandbox, tool calls sem permission gate |
| **Entregaveis** | Interface de MCP process starter, stdio/SSE transport planejado, tool discovery seguro, permission gate antes de tool call, allowlist de tools, timeout/cancelamento, `OMNIS_P49_REAL_MCP_BRIDGE_REPORT.md`, `OMNIS_MCP_PERMISSION_MODEL.md` |
| **Criterios de aceite** | Tool discovery funciona em mock, real bridge desligavel, critical tools bloqueadas, audit trail completo, timeout funciona |
| **Testes obrigatorios** | `tests/plugin_runtime/` + novos integration tests com MCP descriptors |
| **Seguranca** | dry_run por padrao, critical tools (shell, file_delete, network) bloqueadas, allowlist obrigatoria, sem execucao sem permission gate, timeout em toda tool call |
| **Rollback** | Desabilitar MCP bridge → volta para plugin runtime mock |
| **Sinais de bloqueio** | MCP server processes sem sandbox, tools criticas sem bloqueio |
| **Prompt executor** | "Executar P49 — Real MCP Bridge. Criar MCP process starter com permission gate. Tools criticas bloqueadas. dry_run default." |
| **Condicao para proxima fase** | Tool discovery funcional + permission gates operantes + testes verdes |

---

## P50 — Real Telegram Bot

| Field | Detail |
|---|---|
| **Objetivo** | Criar bot Telegram real controlado para comandos remotos |
| **Por que vem nessa ordem** | Telegram e o primeiro canal externo real. Vem depois de Akasha (para persistir comandos), observabilidade (para monitorar), e MCP (para ter tools disponiveis). E o canal mais simples e controlado para comecar. |
| **Dependencias** | P47 (Akasha), P48 (observability), P49 (MCP bridge) |
| **Arquivos permitidos** | `src/remote_control/`, `tests/remote_control/`, `docs/OMNIS_P50_*.md`, `docs/OMNIS_TELEGRAM_*.md` |
| **Arquivos proibidos** | Token Telegram hardcoded, .env |
| **Comandos seguros** | `python -m pytest tests/remote_control/` |
| **Comandos proibidos** | Enviar mensagem para terceiros, comandos destrutivos via Telegram, polling sem rate limit |
| **Entregaveis** | Telegram adapter real (python-telegram-bot), decisao polling vs webhook documentada, whitelist de comandos, approval challenge, registro de evento de comando remoto, comandos iniciais: status/briefing/approve/reject, `OMNIS_P50_REAL_TELEGRAM_BOT_REPORT.md`, `OMNIS_TELEGRAM_COMMANDS_V1.md` |
| **Criterios de aceite** | Comando remoto vira Work Order seguro, approval challenge validado, sem credencial hardcoded, sem side effect real sem approval, mock continua passando |
| **Testes obrigatorios** | `tests/remote_control/` + mock integration com Telegram adapter |
| **Seguranca** | Comandos whitelist somente, approval challenge para qualquer comando MEDIUM+, sem comandos destrutivos mapeados, rate limit por usuario, token via config (nunca .env direto) |
| **Rollback** | Desligar bot → comandos Telegram param de ser processados. Mock adapter assume. |
| **Sinais de bloqueio** | Token Telegram indisponivel, webhook sem HTTPS local |
| **Prompt executor** | "Executar P50 — Real Telegram Bot. Bot controlado com whitelist. Enviar apenas para @lucastigrereal. Comandos: status, briefing, approve, reject." |
| **Condicao para proxima fase** | Bot responde a comandos + approval challenge funcional + nenhum comando destrutivo executavel |

---

## P51 — WhatsApp Business Adapter Planning + Mock

| Field | Detail |
|---|---|
| **Objetivo** | Preparar WhatsApp sem entrar em producao prematura |
| **Por que vem nessa ordem** | WhatsApp e mais complexo que Telegram (Business API, templates, media handling). Vem depois do Telegram para aproveitar o aprendizado do canal mais simples. Comeca com planejamento + mock para nao atrasar o Telegram com complexidade desnecessaria. |
| **Dependencias** | P50 (Telegram real operando) |
| **Arquivos permitidos** | `src/remote_control/whatsapp*.py`, `tests/remote_control/test_whatsapp*.py`, `docs/OMNIS_P51_*.md`, `docs/OMNIS_WHATSAPP_*.md` |
| **Arquivos proibidos** | WhatsApp Business API key, phone number ID, .env |
| **Comandos seguros** | `python -m pytest tests/remote_control/ -k whatsapp` |
| **Comandos proibidos** | Enviar mensagem WhatsApp real, configurar webhook real |
| **Entregaveis** | Planejamento WhatsApp Business API, modelagem de templates, modelagem de media handling, mock adapter atualizado, riscos e limites documentados, `OMNIS_P51_WHATSAPP_ADAPTER_PLAN.md`, `OMNIS_WHATSAPP_SECURITY_BOUNDARY.md` |
| **Criterios de aceite** | Arquitetura pronta e documentada, nenhum envio real possivel, aprovacao obrigatoria modelada para qualquer mensagem, mock adapter cobre todos os cenarios |
| **Testes obrigatorios** | Mock adapter tests, template validation tests |
| **Seguranca** | Nenhum envio real sem aprovacao, sem numero real hardcoded, sem template aprovado sem revisao |
| **Rollback** | N/A — fase de planejamento + mock |
| **Sinais de bloqueio** | WhatsApp Business API acesso negado, Meta Business verification pendente |
| **Prompt executor** | "Executar P51 — WhatsApp Business Adapter Planning + Mock. Planejar arquitetura. Criar mock adapter. Nao conectar numero real." |
| **Condicao para proxima fase** | Arquitetura documentada + mock tests passam |

---

## P52 — Production Hardening

| Field | Detail |
|---|---|
| **Objetivo** | Endurecer runtime antes de missoes E2E e acao real controlada |
| **Por que vem nessa ordem** | Depois que todos os adapters estao planejados/implementados, hardening garante que o sistema aguenta uso real sem quebrar. Vem antes de P54 (E2E mission) porque a missao precisa de retries/timeouts/rollbacks. |
| **Dependencias** | P47-P51 concluidos |
| **Arquivos permitidos** | `src/` (todas as camadas), `tests/`, `docs/OMNIS_P52_*.md` |
| **Arquivos proibidos** | .env, secrets |
| **Comandos seguros** | `python -m pytest tests/`, profiling tools |
| **Comandos proibidos** | Alterar politica de seguranca, remover dry_run defaults |
| **Entregaveis** | E2E tests reais controlados, profiling, retry policies, circuit breakers, timeout policies, rollback docs, failure matrix, dry-run guarantee audit atualizado, `OMNIS_P52_PRODUCTION_HARDENING_REPORT.md`, `OMNIS_FAILURE_MODE_MATRIX.md`, `OMNIS_ROLLBACK_RUNBOOK.md` |
| **Criterios de aceite** | Retries e timeouts documentados e testados, sem unbounded execution, sem silent failure, circuit breaker abre em 3 falhas consecutivas |
| **Testes obrigatorios** | E2E tests, retry/circuit breaker unit tests, timeout enforcement tests |
| **Seguranca** | Nenhum safety gate removido, hardening nao enfraquece dry_run, retries nao bypassam approval |
| **Rollback** | Reverter para politicas default (no retry, timeout longo) |
| **Sinais de bloqueio** | Testes de falha injetada quebram o sistema, circuit breaker muito sensivel |
| **Prompt executor** | "Executar P52 — Production Hardening. Adicionar retries, circuit breakers, timeouts. Auditar dry-run guarantees. Nao remover gates de seguranca." |
| **Condicao para proxima fase** | Hardening tests passam + failure matrix documentada + runbook pronto |

---

## P53 — KRATOS ↔ OMNIS Runtime Dashboard Contract

| Field | Detail |
|---|---|
| **Objetivo** | Definir contrato entre OMNIS e KRATOS para o cockpit visualizar runtime real |
| **Por que vem nessa ordem** | KRATOS e o cockpit visual do Lucas. Depois do hardening, o runtime esta estavel o suficiente para expor seu estado. O contrato define O QUE expor, sem acoplar KRATOS aos internals do OMNIS. |
| **Dependencias** | P52 (production hardening) |
| **Arquivos permitidos** | `docs/OMNIS_P53_*.md`, schema files, `tests/kratos_bridge/` |
| **Arquivos proibidos** | `src/` do KRATOS (outro projeto), .env |
| **Comandos seguros** | JSON schema validation, teste de payload |
| **Comandos proibidos** | Modificar codigo do KRATOS, abrir porta HTTP sem autorizacao |
| **Entregaveis** | API/arquivo status schema para KRATOS ler: mission status, approvals pending, runtime health, latest outputs, active work orders, risk state, blocked actions, next action, `OMNIS_P53_KRATOS_RUNTIME_CONTRACT.md` |
| **Criterios de aceite** | KRATOS consegue ler sem acoplar internals, payload sem secrets, fallback disponivel, schema validado |
| **Testes obrigatorios** | Payload validation tests |
| **Seguranca** | Nenhum secret no payload, status endpoint nao expoe comandos pending, somente leitura do lado KRATOS |
| **Rollback** | KRATOS volta para status mock |
| **Sinais de bloqueio** | KRATOS nao consegue consumir schema, payload muito pesado |
| **Prompt executor** | "Executar P53 — KRATOS Runtime Dashboard Contract. Definir schema JSON. KRATOS le status. Nenhum secret exposto." |
| **Condicao para proxima fase** | Contrato validado + KRATOS consegue ler payload de exemplo |

---

## P54 — First Real Mission End-to-End Dry-Run+

| Field | Detail |
|---|---|
| **Objetivo** | Rodar primeira missao completa com runtime quase-real, mas ainda sem efeito externo perigoso |
| **Por que vem nessa ordem** | A primeira missao E2E integra todos os sistemas em um fluxo real. E o teste definitivo de que as pecas funcionam juntas. "Dry-Run+" significa: dry-run para acoes externas, mas com writebacks reais em Akasha e artefatos locais. |
| **Dependencias** | P47-P53 concluidos |
| **Arquivos permitidos** | `missions/`, `output/` (safe dirs), `docs/OMNIS_P54_*.md` |
| **Arquivos proibidos** | Instagram API, publicacao real, envio externo |
| **Comandos seguros** | Pipeline dry-run completo |
| **Comandos proibidos** | Publicar, enviar, deploy, push |
| **Entregaveis** | Missao exemplo: "Crie 3 posts sobre turismo em Natal e gere pacote de entrega", artefatos gerados, pipeline completo: intake → validate → context → skill route → dry-run execution → artifact registry → approval → Akasha writeback real → report → KRATOS status payload, `OMNIS_P54_FIRST_E2E_MISSION_REPORT.md` |
| **Criterios de aceite** | Missao gera artefatos, logs completos com trace_id, aprovacao registrada, aprendizado gravado em Akasha, sem publicacao real, KRATOS mostra status da missao |
| **Testes obrigatorios** | Pipeline integration test, artifact validation test |
| **Seguranca** | Sem publicacao real, sem envio externo, sem acao destrutiva, aprovacao necessaria |
| **Rollback** | Artefatos ficam como output local. Nada publicado. |
| **Sinais de bloqueio** | Pipeline quebra em stage inesperado, Akasha writeback falha |
| **Prompt executor** | "Executar P54 — First E2E Mission. Pipeline completo dry-run. Missao: criar 3 posts turismo Natal. Artefatos locais. Sem publicacao." |
| **Condicao para proxima fase** | Missao completa E2E + artefatos gerados + relatorio aprovado |

---

## P55 — Controlled Real Action Pilot

| Field | Detail |
|---|---|
| **Objetivo** | Primeira acao real limitada, reversivel e inofensiva |
| **Por que vem nessa ordem** | Depois de provar que o pipeline E2E funciona em dry-run, damos um passo minimo para acao real. A menor acao possivel, controlada, com rollback facil. |
| **Dependencias** | P54 (E2E mission dry-run bem sucedida) |
| **Arquivos permitidos** | Akasha namespace de teste, canal Telegram proprio, output file local |
| **Arquivos proibidos** | Instagram post, WhatsApp para terceiros, delete, gastar dinheiro, API critica |
| **Comandos seguros** | Akasha write (namespace teste), Telegram send (self), file write local |
| **Comandos proibidos** | Instagram publish, WhatsApp send to others, destructive, paid API |
| **Entregaveis** | Uma acao real (ex: enviar "OMNIS P55 pilot completo" para @lucastigrereal no Telegram, ou escrever doc em Akasha namespace `omnis/pilot/`), `OMNIS_P55_CONTROLLED_REAL_ACTION_PILOT_REPORT.md` |
| **Criterios de aceite** | Acao real pequena e documentada, auditada, reversivel ou inofensiva, aprovada explicitamente por Lucas |
| **Testes obrigatorios** | Verification de que acao foi executada e logada |
| **Seguranca** | Acao unica, limitada em escopo, Lucas aprova explicitamente antes, audit trail completo |
| **Rollback** | Delete do registro em Akasha, delete da mensagem Telegram |
| **Sinais de bloqueio** | Credencial real ausente, Lucas nao aprova |
| **Prompt executor** | "Executar P55 — Controlled Real Action Pilot. Menor acao real possivel. Aprovacao explicita necessaria. Rollback facil." |
| **Condicao para proxima fase** | Acao real bem sucedida + auditada + Lucas confirma |

---

## P56 — Supreme Release Candidate

| Field | Detail |
|---|---|
| **Objetivo** | Preparar OMNIS Supreme Release Candidate |
| **Por que vem nessa ordem** | Ultima fase. Com tudo integrado, testado, e pilotado, o RC e o pacote final que diz: "OMNIS Supreme esta pronto para operacao controlada." |
| **Dependencias** | P46-P55 todos concluidos |
| **Arquivos permitidos** | `docs/OMNIS_SUPREME_RC_*.md`, checklists, `CHANGELOG.md` |
| **Arquivos proibidos** | Alteracoes de codigo (feature freeze) |
| **Comandos seguros** | `python -m pytest tests/`, `git log`, `git diff --stat master` |
| **Comandos proibidos** | Novas features, alteracoes de arquitetura, mudancas de seguranca |
| **Entregaveis** | `OMNIS_SUPREME_RELEASE_CANDIDATE_REPORT.md`, checklist seguranca, checklist runtime, checklist Akasha, checklist remote control, checklist KRATOS bridge, checklist tests, checklist docs |
| **Criterios de aceite** | Sistema operavel, riscos conhecidos e documentados, runbooks completos, nenhum mock critico fingindo producao, Supreme RC definido e selado |
| **Testes obrigatorios** | Full suite verde |
| **Seguranca** | Todos os gates confirmados, auditoria final de seguranca, dry_run defaults intactos |
| **Rollback** | N/A — ponto de chegada |
| **Sinais de bloqueio** | Qualquer criterio de seguranca violado, testes falhando |
| **Prompt executor** | "Executar P56 — Supreme Release Candidate. Gerar checklists finais. Feature freeze. Validar tudo." |
| **Condicao para proxima fase** | Supreme RC aprovado. Fim da Wave 13. |

---

## Resumo visual do roadmap

```
┌──────────────────────────────────────────────────────────────┐
│                    OMNIS SUPREME ROADMAP                      │
│                   Wave 13 — Runtime Real                     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  NOW:    P46  Merge Readiness          [EM EXECUCAO]         │
│           │                                                  │
│  WAVE13: P47  Real Akasha Sink         [PLANEJADO]           │
│           │                                                  │
│          P48  Observability Baseline    [PLANEJADO]           │
│           │                                                  │
│          P49  Real MCP Bridge           [PLANEJADO]           │
│           │                                                  │
│          P50  Real Telegram Bot         [PLANEJADO]           │
│           │                                                  │
│          P51  WhatsApp Plan + Mock      [PLANEJADO]           │
│           │                                                  │
│          P52  Production Hardening      [PLANEJADO]           │
│           │                                                  │
│          P53  KRATOS Runtime Contract   [PLANEJADO]           │
│           │                                                  │
│          P54  First E2E Mission         [PLANEJADO]           │
│           │                                                  │
│          P55  Controlled Real Action    [PLANEJADO]           │
│           │                                                  │
│  GOAL:   P56  Supreme Release Candidate [OBJETIVO FINAL]     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Decisoes pendentes do operador

1. **P46:** Autorizar merge apos limpeza do working tree? → Aguardando
2. **P47:** pgvector disponivel? Docker pronto? → Verificar antes de iniciar
3. **P48-P49:** Ordem confirmada (Observability → MCP)? → Proposta: sim
4. **P50:** Token Telegram disponivel? Webhook ou polling? → Verificar
5. **P51-P56:** Confirmar sequencia completa → Roadmap aberto para ajustes

---

## Regras de transicao entre fases

1. Cada fase gera relatorio proprio em `docs/OMNIS_P<N>_*.md`
2. Full suite (ou targeted tests) devem passar antes de considerar fase concluida
3. Relatorio deve ser revisado e aprovado antes de iniciar proxima fase
4. Nenhuma fase comeca com working tree sujo
5. Seguranca re-verificada a cada transicao (dry_run defaults, secrets boundary)
6. Se uma fase revelar problema na anterior, pausar e resolver antes de continuar

---

**Proximo passo:** Aprovacao de Lucas para merge P46 → iniciar P47.

# OMNIS WAVE 7B — RUNTIME BRIDGE & REAL EXECUTION CONTROL PLANNING

**Status:** PLANNING READ-ONLY  
**Date:** 2026-05-14  
**Author:** Aba 3 — OMNIS Planning Architect  
**Target branch:** `feature/omnis-wave-7b-runtime-bridge` (not created yet)

---

## 1. Sumario Executivo

A Wave 7B transforma o OMNIS de um engine puramente in-memory em um sistema conectado ao ecossistema real: War Room (work orders), Skill Router (ks), Akasha (pgvector), e uma camada de aprovacao explicita. Tudo permanece com dry-run obrigatorio e sem execucao automatica de acoes destrutivas.

A Wave 7B nao implementa adapters reais para APIs externas (Instagram, Gmail, GitHub) — isso fica para a Wave 7C+. A Wave 7B foca em CONEXOES INTERNAS ao proprio ecossistema do operador.

---

## 2. Estado Atual Apos Wave 7A

- **Master @ `d550ad3`** — up to date with origin/master
- **5428 tests passed, 2 skipped, 0 failures**
- **7 modulos novos:** Control Tower, Execution Contracts, Work Order Bridge, Skill Router Bridge, Safe Execution Queue, Decision Log, Integration Pipeline
- **Pipeline funcional:** WorkOrder → Contract → Decision → Skill → DryRun → Queue → EventLog
- **Todo mock:** Nenhum modulo toca sistema real. Skills sao 7 mocks. Queue e in-memory. Log e in-memory ou file-backed.

---

## 3. O Que Wave 7A Ja Permite

| Capacidade | Modulo |
|---|---|
| Classificar risco de acoes (LOW→CRITICAL) | `control_tower/risk.py` |
| Bloquear acoes por violacao de fronteira | `control_tower/boundaries.py` |
| Decidir se acao procede (BLOCK/OBSERVE/DRY_RUN/EXECUTE) | `control_tower/decision_engine.py` |
| Gerar contrato de execucao com paths permitidos/proibidos | `execution_contracts/` |
| Parsear Work Orders em Markdown com frontmatter YAML | `work_orders/parser.py` |
| Selecionar skill mock por ID, intent ou tags | `skills_bridge/selection.py` |
| Executar dry-run em skill mock | `skills_bridge/dryrun.py` |
| Enfileirar, validar e executar itens com 9-state machine | `execution_queue/` |
| Registrar 8 tipos de eventos de decisao | `decision_log/` |
| Pipeline end-to-end integrado | `omnis_control/pipeline.py` |

---

## 4. O Que Wave 7A Ainda NAO Permite

| Gap | Impacto |
|---|---|
| Nao le Work Orders reais do War Room | Pipeline so funciona com string inline |
| Nao escreve reports de volta no War Room | Execucao nao deixa rastro no sistema de controle |
| Nao consulta skill router real (`ks`) | Selecao de skill e mock, nao reflete skills reais |
| Nao tem camada de aprovacao explicita standalone | Aprovacao esta diluida entre work_orders e queue |
| Nao escreve eventos no Akasha (pgvector) | EventLog existe mas nao persiste em banco vetorial |
| Nao tem planejamento de controle remoto | Telegram/WhatsApp sao ideias, nao planos |
| Nao tem trilha de auditoria consolidada | Logs existem por modulo mas nao unificados |
| Nao tem rollback hints estruturados | Contratos tem hints mas nao ha mecanismo de rollback |

---

## 5. Objetivo da Wave 7B

Sair do pipeline puramente in-memory e conectar o OMNIS aos sistemas reais do proprio ecossistema, mantendo dry-run obrigatorio e aprovacao humana para toda acao com consequencia externa.

**Regra:** Conectar internamente primeiro (War Room, skills, Akasha, aprovacao). APIs externas ficam para Wave 7C+.

---

## 6. Principios de Seguranca

| Principio | Regra | Aplicacao |
|---|---|---|
| **Dry-run first** | Nenhuma acao real sem dry-run previo | Todo adapter real tem flag `dry_run=True` default |
| **Approval required** | MEDIUM/HIGH/CRITICAL requer aprovacao | Approval Runtime centraliza todos os gates |
| **No shell livre** | Nenhum `subprocess.run` sem path whitelist | Shell adapter com allowed_commands explicito |
| **No external write sem aprovacao** | Write em sistema externo → approval gate | BoundaryGuard ampliado para filesystem writes |
| **No KRATOS mutation** | OMNIS nunca escreve no repo KRATOS | Boundary rule: OMNIS → KRATOS = read only |
| **No secrets exposure** | Nenhum token/senha em log ou evento | Sanitizer em LogWriter para campos secret_* |
| **No destructive action** | DELETE, DROP, RM requerem confirmacao dupla | DecisionEngine: destructive → CRITICAL → BLOCK |
| **Mock-first testing** | Todo adapter real tem mock para testes | Padrao estabelecido na Wave 7A |

---

## 7. P37 — War Room Runtime Bridge

### Objetivo
Conectar o OMNIS ao War Room como fonte e destino de Work Orders, inicialmente read-only para leitura e write-only para reports.

### Modulos Provaveis
- `src/war_room_bridge/` — modulo novo

### Arquivos Provaveis
```
src/war_room_bridge/__init__.py       — exports
src/war_room_bridge/models.py         — WarRoomOrder, WarRoomReport, OrderStatus
src/war_room_bridge/reader.py         — WarRoomReader: le orders/ do War Room
src/war_room_bridge/writer.py         — WarRoomWriter: escreve reports/ no War Room
src/war_room_bridge/adapter.py        — WarRoomAdapter: interface unificada
src/war_room_bridge/errors.py         — WarRoomError
```

### Testes Provaveis
```
tests/war_room_bridge/test_reader.py   — leitura de orders/ com tmp_path
tests/war_room_bridge/test_writer.py   — escrita de reports/ com tmp_path
tests/war_room_bridge/test_adapter.py  — integracao reader+writer
tests/war_room_bridge/test_models.py   — round-trip to_dict/from_dict
```

### Interfaces principais
- `WarRoomReader.list_orders() → list[WarRoomOrder]` — scan `war-room/orders/`
- `WarRoomReader.read_order(order_id: str) → WarRoomOrder` — le e parseia order markdown
- `WarRoomWriter.write_report(order_id: str, report: WarRoomReport)` — escreve `war-room/reports/`
- `WarRoomAdapter.sync()` — le novas orders e atualiza status

### Riscos
- **Baixo.** Leitura de filesystem e segura. Escrita restrita ao diretorio `reports/`.
- Paths do War Room precisam ser configurable, nao hardcoded.

### Criterio de Aceite
1. Consegue ler `war-room/orders/aba-3-omnis.md` como WarRoomOrder
2. Consegue escrever report em `war-room/reports/` como markdown
3. Nao toca em `war-room/status/` (read-only para OMNIS)
4. Nao toca em `war-room/canon/` (read-only para OMNIS)
5. Todos os testes passam com tmp_path (zero dependencia do War Room real)

### O Que NAO Fazer
- NAO criar orders no War Room (so le)
- NAO modificar status files (aba-3-omnis.md)
- NAO mexer no Canon Vault
- NAO hardcodar paths absolutos

---

## 8. P38 — Skill Router Real Bridge

### Objetivo
Conectar o `skills_bridge` mock da Wave 7A ao catalogo/router real de skills (`ks` + 153 skills), inicialmente em dry-run.

### Modulos Provaveis
- `src/skills_bridge/` — extendido (nao substituido)

### Arquivos Provaveis
```
src/skills_bridge/real_router.py      — RealSkillRouter: consulta ks + skill-map.json
src/skills_bridge/real_adapter.py     — RealSkillAdapter: ABC para skills reais
src/skills_bridge/catalog.py          — SkillCatalog: carrega skill-map.json
```

### Testes Provaveis
```
tests/skills_bridge/test_real_router.py    — router com catalog mockado
tests/skills_bridge/test_catalog.py        — parse de skill-map.json
tests/skills_bridge/test_real_adapter.py   — adapter com mock de execucao
```

### Interfaces principais
- `RealSkillRouter.__init__(catalog_path: str, dry_run: bool = True)`
- `RealSkillRouter.resolve(skill_id: str) → SkillDefinition` — busca no catalog
- `RealSkillAdapter.call_skill(skill_id, payload) → dict` — dry-run por default
- `SkillCatalog.load() → list[SkillDefinition]` — carrega skill-map.json

### Fontes de dados reais
- `C:\Users\lucas\.kratos\skill-map.json` (93.5 KB, 153 skills)
- `C:\Users\lucas\.kratos\kratos-skill-router.ps1` (ks command)
- Skills directory com SKILL.md canonicos

### Riscos
- **Baixo.** Leitura de JSON e segura. Execucao e sempre dry-run.
- skill-map.json pode mudar estrutura — validar schema antes de parse.

### Criterio de Aceite
1. Consegue carregar skill-map.json e listar 153 skills
2. `resolve("seogram")` retorna a skill correta
3. `call_skill` sempre executa em dry-run (nao invoca ks real)
4. Fallback para `manual-review` se skill nao encontrada
5. Testes usam catalog mockado de 5-10 skills

### O Que NAO Fazer
- NAO executar `ks` PowerShell real (so consultar catalog)
- NAO modificar skill-map.json
- NAO substituir SkillSelector mock — extender com opcao real
- NAO depender do skill-map.json para testes (usar fixture)

---

## 9. P39 — Approval Runtime

### Objetivo
Criar camada de aprovacao explicita e standalone para acoes MEDIUM/HIGH/CRITICAL, separada do WorkOrder validator e do ExecutionQueue.

### Modulos Provaveis
- `src/approval_runtime/` — modulo novo

### Arquivos Provaveis
```
src/approval_runtime/__init__.py       — exports
src/approval_runtime/models.py         — ApprovalRequest, ApprovalDecision, ApprovalStatus(Enum)
src/approval_runtime/engine.py         — ApprovalEngine: avalia e decide
src/approval_runtime/store.py          — ApprovalStore: persiste aprovacoes pendentes
src/approval_runtime/errors.py         — ApprovalError
```

### Testes Provaveis
```
tests/approval_runtime/test_models.py     — round-trip
tests/approval_runtime/test_engine.py     — logicas de aprovacao
tests/approval_runtime/test_store.py      — persistencia com tmp_path
tests/approval_runtime/test_integration.py — integration com pipeline
```

### Interfaces principais
- `ApprovalEngine.__init__(dry_run: bool = True)`
- `ApprovalEngine.evaluate(item: ApprovalRequest) → ApprovalDecision`
- Regras:
  - LOW risk + non-destructive → AUTO_APPROVE
  - MEDIUM risk → NEEDS_APPROVAL (aguarda humano)
  - HIGH risk → NEEDS_APPROVAL + dry-run mandatory
  - CRITICAL risk → NEEDS_APPROVAL + dry-run + reason documentado
- `ApprovalStore.pending() → list[ApprovalRequest]`
- `ApprovalStore.approve(request_id)` / `ApprovalStore.reject(request_id, reason)`

### Riscos
- **Medio.** Aprovacao e o unico gate entre automacao e acao real. Logica precisa ser simples e sem ambiguidade.

### Criterio de Aceite
1. `evaluate(LOW, non-destructive) → AUTO_APPROVE`
2. `evaluate(MEDIUM, any) → NEEDS_APPROVAL`
3. `evaluate(HIGH, any) → NEEDS_APPROVAL + dry_run_required=True`
4. `evaluate(CRITICAL, any) → NEEDS_APPROVAL + requires_reason=True`
5. Store persiste aprovacoes pendentes em JSON
6. Integracao com pipeline: contract → decision → APPROVAL → skill → queue

### O Que NAO Fazer
- NAO implementar aprovacao via Telegram ainda (P41)
- NAO pular approval gate em testes (mockar, nao desabilitar)
- NAO usar banco de dados real — JSON file-backed

---

## 10. P40 — Akasha Event Sink

### Objetivo
Preparar escrita de eventos do Decision Log no Akasha (pgvector), comecando com adapter file-backed e mock para testes.

### Modulos Provaveis
- `src/akasha_sink/` — modulo novo
- `src/decision_log/` — extendido com sink interface

### Arquivos Provaveis
```
src/akasha_sink/__init__.py            — exports
src/akasha_sink/models.py              — SinkEvent, SinkStatus, SinkConfig
src/akasha_sink/adapter.py             — AkashaAdapter: ABC + FileAdapter + MockAdapter
src/akasha_sink/collector.py           — EventCollector: coleta do LogWriter → sink
src/akasha_sink/errors.py              — SinkError
```

### Testes Provaveis
```
tests/akasha_sink/test_file_adapter.py    — escrita/leitura em tmp_path
tests/akasha_sink/test_collector.py       — coleta eventos do LogWriter
tests/akasha_sink/test_models.py          — round-trip
```

### Interfaces principais
- `AkashaAdapter` (ABC) com `write_event(event: dict)`, `query_events(filter)`, `health_check()`
- `FileAkashaAdapter(AkashaAdapter)` — escreve JSON em diretorio (tmp_path em testes)
- `MockAkashaAdapter(AkashaAdapter)` — in-memory para testes
- `EventCollector.__init__(writer: LogWriter, sink: AkashaAdapter)`
- `EventCollector.flush()` — envia eventos pendentes para o sink

### Estrategia de conexao real (futura)
- `PgVectorAkashaAdapter` — conecta no pgvector (porta 5432)
- Nao implementado na Wave 7B — apenas planejado e stub

### Riscos
- **Baixo.** So file-backed por enquanto. Conexao pgvector real e para Wave 7C.
- Dependencia do psycopg2/asyncpg — nao instalar ainda.

### Criterio de Aceite
1. FileAkashaAdapter escreve eventos JSON em diretorio
2. MockAkashaAdapter armazena em memoria para testes
3. EventCollector.flush() transfere eventos do LogWriter para o sink
4. Nao requer conexao com pgvector real
5. Interface ABC permite swap futuro para pgvector sem quebrar codigo

### O Que NAO Fazer
- NAO conectar no pgvector real
- NAO instalar psycopg2/asyncpg
- NAO escrever embeddings — so JSON estruturado
- NAO modificar schema do Akasha

---

## 11. P41 — Telegram/WhatsApp Control Planning

### Objetivo
Planejar bridge de controle remoto, comecando por Telegram. Fase puramente de design — zero implementacao.

### Entregaveis
```
docs/OMNIS_TELEGRAM_BRIDGE_DESIGN.md   — design completo
docs/OMNIS_TELEGRAM_SECURITY_MODEL.md   — modelo de seguranca
```

### Conteudo dos docs
1. **Arquitetura:** Bot Telegram → webhook → OMNIS API → Approval Runtime → Execucao
2. **Comandos planejados:**
   - `/status` — health check de todos os sistemas
   - `/approve <id>` — aprovar acao pendente
   - `/reject <id> <reason>` — rejeitar acao
   - `/briefing` — briefing diario do Publisher OS
   - `/run <skill> <args>` — executar skill em dry-run
3. **Modelo de seguranca:**
   - Chat ID whitelist (so Lucas pode comand ar)
   - Token em variavel de ambiente, nunca em codigo
   - Confirmacao dupla para acoes destrutivas
   - Rate limiting (max 10 comandos/minuto)
4. **O que NAO permitir:**
   - NAO permitir shell commands via Telegram
   - NAO permitir acesso a .kratos/ ou War Room
   - NAO permitir modificacao de codigo
5. **Dependencias futuras:** python-telegram-bot (nao instalar ainda)

### Riscos
- **Alto se implementado sem seguranca.** Chat ID spoofing, token leak, command injection.
- Por isso e planning-only. Implementacao real requer auditoria de seguranca previa.

### Criterio de Aceite
1. Design doc completo com arquitetura e fluxos
2. Security model documentado
3. Lista de comandos permitidos/proibidos
4. NENHUM codigo implementado

### O Que NAO Fazer
- NAO implementar bot Telegram
- NAO criar tokens/keys
- NAO abrir webhooks
- NAO escrever uma linha de codigo de integracao

---

## 12. P42 — Observability, Rollback & Audit

### Objetivo
Consolidar logs, runs, audit trail, rollback hints e status de execucao em uma camada de observabilidade unificada.

### Modulos Provaveis
- `src/observability/` — extendido (ja existe `src/observability/` com estrutura basica)

### Arquivos Provaveis
```
src/observability/__init__.py          — exports
src/observability/audit.py             — AuditTrail: registro de toda acao
src/observability/rollback.py          — RollbackEngine: hints + planos
src/observability/status.py            — RunStatus: status de execucao unificado
src/observability/reporter.py          — RunReporter: sumario de execucao
```

### Testes Provaveis
```
tests/observability/test_audit.py      — trilha de auditoria
tests/observability/test_rollback.py   — planos de rollback
tests/observability/test_status.py     — status de execucao
tests/observability/test_reporter.py   — geracao de reports
```

### Interfaces principais
- `AuditTrail.record(action, result, timestamp)` — registra acao
- `AuditTrail.query(since, until, system) → list[AuditEntry]` — consulta historico
- `RollbackEngine.plan(contract) → RollbackPlan` — gera plano a partir de rollback_hint
- `RollbackEngine.can_rollback(contract) → bool` — verifica se rollback e possivel
- `RunStatus.update(phase, status, detail)` — atualiza status de execucao
- `RunReporter.generate(run_id) → RunReport` — sumario completo

### Riscos
- **Baixo.** Consolidacao de dados que ja existem em modulos separados.
- Cuidado com duplicacao — audit trail deve referenciar eventos do decision_log, nao duplica-los.

### Criterio de Aceite
1. AuditTrail consolida eventos de execution_queue + decision_log
2. RollbackEngine le rollback_hint dos contratos e gera plano
3. RunStatus integra com pipeline para tracking de fase
4. RunReporter gera markdown report (compativel com War Room)
5. Testes cobrem fluxo end-to-end de auditoria

### O Que NAO Fazer
- NAO executar rollback real (so gerar planos)
- NAO substituir logs existentes — complementar
- NAO depender de banco de dados externo

---

## 13. Arquitetura Final Esperada

```
                              ┌──────────────────────┐
                              │   WAR ROOM ORDERS/   │
                              │   (filesystem read)  │
                              └──────────┬───────────┘
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │  P32 WORK ORDER      │
                              │  PARSER (frontmatter)│
                              └──────────┬───────────┘
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │  P31 EXECUTION       │
                              │  CONTRACT (validate) │
                              └──────────┬───────────┘
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │  P30 CONTROL TOWER   │
                              │  DECISION ENGINE     │
                              └──────────┬───────────┘
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │  P39 APPROVAL        │
                              │  RUNTIME (gate)      │
                              └──────────┬───────────┘
                                         │
                          ┌──────────────┼──────────────┐
                          │              │              │
                          ▼              ▼              ▼
                   ┌────────────┐ ┌────────────┐ ┌────────────┐
                   │ AUTO_      │ │ NEEDS_     │ │ BLOCKED    │
                   │ APPROVE    │ │ APPROVAL   │ │            │
                   └─────┬──────┘ └─────┬──────┘ └─────┬──────┘
                         │              │              │
                         ▼              ▼              ▼
                   ┌────────────┐ ┌────────────┐ ┌────────────┐
                   │ CONTINUE   │ │ WAIT FOR   │ │ LOG +      │
                   │            │ │ HUMAN      │ │ TERMINATE  │
                   └─────┬──────┘ └────────────┘ └────────────┘
                         │
                         ▼
                  ┌──────────────────────┐
                  │  P38 SKILL ROUTER    │
                  │  REAL BRIDGE (dryrun)│
                  │  ← catalog           │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  P34 SAFE EXECUTION  │
                  │  QUEUE (9-state)     │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  P35 DECISION LOG    │
                  │  (eventos)           │
                  └──────────┬───────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
                    ▼                 ▼
          ┌──────────────────┐  ┌──────────────────┐
          │  P40 AKASHA      │  │  P37 WAR ROOM    │
          │  EVENT SINK      │  │  REPORT WRITER   │
          │  (file/mock)     │  │  → reports/      │
          └──────────────────┘  └──────────────────┘
                                        │
                                        ▼
                              ┌──────────────────────┐
                              │  P42 OBSERVABILITY   │
                              │  AUDIT + ROLLBACK    │
                              └──────────────────────┘
                                        │
                                        ▼
                              ┌──────────────────────┐
                              │  P41 TELEGRAM/WA     │
                              │  (planned, not built)│
                              └──────────────────────┘
```

---

## 14. Test Strategy

| Camada | Estrategia |
|---|---|
| **Unit tests** | Cada modulo testado isoladamente com fixtures mock |
| **Integration tests** | Pipeline tests entre 2-3 modulos reais |
| **E2E tests** | `test_omnis_wave_7b_pipeline.py` — fluxo completo com fixtures file-backed |
| **Mock-first** | Todo adapter real tem mock para testes. Nenhum teste depende de sistema externo. |
| **tmp_path** | Todos os testes de filesystem usam `tmp_path`, nunca paths reais |
| **Regression guard** | Suite completa (5428+) antes e depois de cada fase |

**Meta de cobertura:** Nao definida formalmente, mas cada modulo novo deve ter no minimo 3 arquivos de teste.

---

## 15. Branch Strategy

**Branch futura:** `feature/omnis-wave-7b-runtime-bridge`

Criar a partir de `master` @ `d550ad3`.

```
master
  │
  ├─ d550ad3 (Wave 7A final)
  │
  └─ feature/omnis-wave-7b-runtime-bridge
       ├─ feat(p37): add war room runtime bridge
       ├─ feat(p38): add skill router real bridge
       ├─ feat(p39): add approval runtime
       ├─ feat(p40): add akasha event sink
       ├─ docs(p41): add telegram control planning
       └─ feat(p42): add observability rollback audit
```

---

## 16. Commit Strategy

- **1 commit por fase** (P37 → P42), seguindo padrao `feat(pXX): ...`
- **Commit message format:** `feat(pXX): <descricao curta>` + Co-Authored-By
- **Nao commitar docs + codigo no mesmo commit** — docs separados
- **Nao commitar ate que TODOS os testes da fase passem**
- **Nao fazer amend em commits passados**
- **Nao commitar com working tree sujo**

---

## 17. Stop Conditions

Parar imediatamente se:

| Condicao | Acao |
|---|---|
| Teste falhar em qualquer fase | Parar, diagnosticar, corrigir ANTES de continuar |
| Conflito de merge | Parar, reportar, aguardar autorizacao |
| Remote divergir | Parar, reportar, aguardar autorizacao |
| Erro de importacao | Parar, verificar `__init__.py`, corrigir |
| Pre-commit hook falhar | Parar, corrigir o que o hook reportou |
| Working tree ficar sujo com arquivos nao relacionados | Parar, limpar antes de continuar |
| Duvida sobre seguranca de uma acao | Parar, nao executar, reportar |

---

## 18. Dependencies

| Fase | Depende de | Pode ser paralelizada com |
|---|---|---|
| P37 War Room Bridge | — (so filesystem) | P39, P40 |
| P38 Skill Router Real Bridge | — (so catalog JSON) | P37, P39 |
| P39 Approval Runtime | — (module standalone) | P37, P38 |
| P40 Akasha Event Sink | P35 Decision Log | P37 |
| P41 Telegram Planning | — (docs only) | Qualquer fase |
| P42 Observability | P35, P37, P34 | — (fase final) |

**Ordem sugerida:** P37 + P39 em paralelo → P38 → P40 → P41 + P42

---

## 19. Riscos Reais

| Risco | Probabilidade | Impacto | Mitigacao |
|---|---|---|---|
| skill-map.json mudar schema | Baixa | Medio | Validar schema no load, fallback para mock |
| War Room paths diferentes do esperado | Media | Baixo | Paths configuraveis via config/paths.yaml |
| Duplicacao de logica de aprovacao | Media | Medio | Approval Runtime como unico source of truth |
| Complexidade excessiva no pipeline | Media | Medio | Manter pipeline steps < 15; cada step e uma chamada simples |
| Vazamento de paths absolutos em testes | Baixa | Baixo | So usar tmp_path, nunca paths reais |
| Tentacao de implementar Telegram | Alta | Alto | P41 e docs-only por design; implementacao requer nova aprovacao |

---

## 20. Proxima Acao Recomendada

**NAO EXECUTAR AINDA.**

1. Revisar este plano com calma
2. Validar contra o KRATOS Master Context
3. Ajustar escopo se necessario
4. Criar branch `feature/omnis-wave-7b-runtime-bridge`
5. Executar com autorizacao explicita: "EXECUTAR ONDA 7B — P37"

---

*Fim do planejamento Wave 7B. Nenhuma implementacao iniciada.*

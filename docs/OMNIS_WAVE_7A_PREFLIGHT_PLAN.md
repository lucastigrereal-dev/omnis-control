# OMNIS WAVE 7A PREFLIGHT PLAN
## 2026-05-14

---

## 1. ESTADO ATUAL

| Indicador | Valor |
|---|---|
| Branch | `master` @ `0183528` |
| Origin | Up to date |
| Testes baseline | 5214+ (running) |
| Working tree | Dirty (ruído pré-existente, não relacionado a P25-P29) |
| P25-P29 | Mergeados e pushados — skeletons estruturais |
| Fase do roadmap | Phase 2 — OMNIS Operational Engine (10%) |

---

## 2. MÓDULOS P25-P29 ENCONTRADOS

| Módulo | Source Files | Status |
|---|---|---|
| P25 Multi-Model Orchestration | 10 | Skeleton ✅ |
| P26 App Factory Supreme | 8 | Skeleton ✅ |
| P27 Real World Actions | 14 | Skeleton ✅ |
| P28 Self-Improvement Loop | 9 | Skeleton ✅ |
| P29 OMNIS OS Layer | 11 | Skeleton ✅ |

**Todos são skeletons:** estrutura + contratos de interface + testes de contrato existem, mas ZERO implementação real.

---

## 3. GAPS PRINCIPAIS

| Gap | Severidade |
|---|---|
| Sem Control Tower para avaliar ações | CRITICAL |
| Sem contratos formais de execução | HIGH |
| Sem bridge para Work Orders do War Room | HIGH |
| Sem bridge para Skills OS | MEDIUM |
| Sem fila de execução segura | HIGH |
| Sem log de decisões/eventos | MEDIUM |
| Sem pipeline de integração | HIGH |

---

## 4. ARQUITETURA PROPOSTA DA ONDA 7A

```
WorkOrder (markdown)
    → P32 Work Order Bridge (parse/validate)
        → P31 Execution Contract (formal contract)
            → P30 Control Tower (risk assessment + decision)
                → P33 Skill Router Bridge (skill selection)
                    → P34 Safe Execution Queue (dry-run gate)
                        → P35 Decision Log (Akasha-ready events)
                            → P36 Integration Smoke Pipeline
```

### Alinhamento com o Canon:

```
KRATOS vê     → WorkOrder nasce no War Room
Aurora interpreta → WorkOrder é criada pela Aba 0
OMNIS age     → Control Tower + Execution Queue processam
Akasha lembra → Decision Log registra eventos
Lucas decide  → Risk HIGH/CRITICAL requer approval
```

---

## 5. MICROFASES PLANEJADAS

| Fase | Nome | Arquivos Source | Arquivos Teste |
|---|---|---|---|
| P30 | Control Tower Core | 6 | 4 |
| P31 | Execution Contracts | 5 | 4 |
| P32 | Work Order Bridge | 5 | 3 |
| P33 | Skill Router Bridge | 5 | 4 |
| P34 | Safe Execution Queue | 5 | 4 |
| P35 | Decision Log / Akasha Events | 5 | 3 |
| P36 | Integration Smoke Pipeline | 2 | 1 |

**Total estimado:** 33 source files, 23 test files

---

## 6. ARQUIVOS PROVÁVEIS

```
src/control_tower/       __init__.py, models.py, risk.py, decision_engine.py, boundaries.py, next_action.py
src/execution_contracts/ __init__.py, models.py, validators.py, permissions.py, outcomes.py
src/work_orders/         __init__.py, parser.py, mapper.py, validator.py, models.py
src/skills_bridge/       __init__.py, models.py, adapter.py, dryrun.py, selection.py
src/execution_queue/     __init__.py, models.py, queue.py, runner.py, state.py
src/decision_log/        __init__.py, models.py, writer.py, events.py, serializer.py
src/omnis_control/       orchestration.py / pipeline.py
```

---

## 7. TESTES PLANEJADOS

| Fase | Testes |
|---|---|
| P30 | test_models.py, test_risk.py, test_boundaries.py, test_decision_engine.py |
| P31 | test_contract_models.py, test_contract_validation.py, test_permissions.py, test_outcomes.py |
| P32 | test_parser.py, test_mapper.py, test_validator.py |
| P33 | test_models.py, test_selection.py, test_dryrun.py, test_adapter_mock.py |
| P34 | test_queue.py, test_runner_dryrun.py, test_runner_blocks_high_risk.py, test_state_transitions.py |
| P35 | test_event_models.py, test_writer.py, test_serializer.py |
| P36 | test_omnis_wave_7a_pipeline.py |

---

## 8. RISCOS

| Risco | Nível | Mitigação |
|---|---|---|
| Working tree sujo no master | BAIXO | Ruído pré-existente, branch novo isola |
| P25-P29 são skeletons | BAIXO | Wave 7A não depende de implementação real deles |
| Zero dependências externas | BAIXO | Tudo local, mock, testável |
| Conflito com worktrees existentes | BAIXO | Branch novo, sem merge até o final |

---

## 9. CRITÉRIOS DE PARADA

- Testes falham em qualquer fase → PARAR, reportar, não continuar
- Working tree fica sujo com arquivos inesperados → PARAR
- Conflito git → PARAR
- Erro de importação cruzada entre módulos → PARAR
- Qualquer ação externa real → PARAR

---

## 10. ESTRATÉGIA DE COMMITS

| Fase | Mensagem |
|---|---|
| P30 | `feat(p30): add omnis control tower core` |
| P31 | `feat(p31): add execution contract layer` |
| P32 | `feat(p32): add work order bridge` |
| P33 | `feat(p33): add skill router bridge` |
| P34 | `feat(p34): add safe execution queue` |
| P35 | `feat(p35): add decision log events` |
| P36 | `feat(p36): add wave 7a integration smoke pipeline` |
| Final | `docs(omnis): add wave 7a final report` |

**Regra:** `git add` específico por arquivo, nunca `git add .`

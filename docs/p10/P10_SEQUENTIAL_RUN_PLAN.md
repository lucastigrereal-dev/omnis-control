# P10 Sequential Run Plan — Blocos P10.2 a P10.11

**Data:** 2026-05-12 | **Base:** 61233cc (P10.1)
**Modo:** Trem blindado — 1 bloco por vez, gate, teste, commit

---

## Baseline

| Item | Valor |
|---|---|
| Branch | master |
| Commit base | 61233cc feat(p10.1): deterministic markdown output writer |
| Testes output_generator | 46/46 |
| Regressão work_order+execution_graph | 312/312 |
| Dirty files (fora escopo) | 5 (config/paths.yaml, docs/ESTADO_ATUAL_RESUMIDO.md, docs/disk_audit_report.json, docs/RELATORIO_COMPLETO_2026.md, exports/) |
| Escopo permitido | src/output_generator/**, src/cli_commands/output_generator_cmd.py, tests/output_generator/**, docs/output_generator/**, docs/p10/**, docs/night_shift/**, docs/state/**, .gitignore |

---

## Regras de execução

1. Um bloco por vez — nunca avançar sem commit verde
2. Teste obrigatório — suite do módulo + regressão
3. Commit atômico — mensagem padronizada
4. Stop imediato em falha — corrigir antes de avançar
5. Zero rede, zero LLM, zero mudança fora de escopo

---

## Blocos

### P10.2 — JSON / Spec Output Writers

**Objetivo:** Writer determinístico para JSON e spec documents.
**Escopo:** `src/output_generator/json_writer.py` + update writer_service + tests + CLI
**CLI novo:** `output-generator write-json <wo_id> [--json]`
**Testes mínimos:** 8
**Dependências:** Nenhuma nova (json é stdlib)

### P10.3 — CSV / Table Output Writers

**Objetivo:** Writer determinístico para CSV (calendários, listas, filas).
**Escopo:** `src/output_generator/csv_writer.py` + update writer_service + tests + CLI
**CLI novo:** `output-generator write-csv <wo_id> [--json]`
**Testes mínimos:** 7
**Dependências:** Nenhuma nova (csv é stdlib)

### P10.4 — Multi-File Output Package

**Objetivo:** Gerar pacote com múltiplos arquivos por work order (md + json + csv + manifest).
**Escopo:** `src/output_generator/package_builder.py` + update writer_service + tests + CLI
**CLI novo:** `output-generator package <wo_id> [--json]`
**Testes mínimos:** 8
**Dependências:** P10.2 + P10.3 writers

### P10.5 — Output Manifest Registry

**Objetivo:** Registry local JSONL de todos os outputs gerados (paths, fingerprints, timestamps).
**Escopo:** `src/output_generator/manifest_registry.py` + tests
**CLI novo:** `output-generator registry list|show <output_id>`
**Testes mínimos:** 7
**Dependências:** Nenhuma nova

### P10.6 — Output Validation Layer

**Objetivo:** Validar integridade do pacote: schema, arquivos obrigatórios, fingerprints.
**Escopo:** `src/output_generator/validator.py` + tests + CLI
**CLI novo:** `output-generator validate <wo_id> [--json]`
**Testes mínimos:** 8
**Dependências:** P10.5 registry

### P10.7 — Approval Submission Bridge

**Objetivo:** Preparar submissão para approval center (dry-run, sem publicar).
**Escopo:** `src/output_generator/approval_bridge.py` + tests + CLI
**CLI novo:** `output-generator submit-approval <wo_id> [--json]`
**Testes mínimos:** 7
**Dependências:** src/approval_center (já existe)

### P10.8 — Work Order → Output Package

**Objetivo:** Orquestrador completo: WO → writers → package → manifest → registry.
**Escopo:** Update `writer_service.py` com método `package()` + tests + CLI
**CLI:** `output-generator package <wo_id>` (evolui o de P10.4)
**Testes mínimos:** 8
**Dependências:** P10.4 + P10.5

### P10.9 — Batch Output Generator

**Objetivo:** Processar múltiplas OS em lote, dry-run por padrão.
**Escopo:** `src/output_generator/batch_runner.py` + tests + CLI
**CLI novo:** `output-generator batch --status approved --dry-run [--json]`
**Testes mínimos:** 8
**Dependências:** P10.8

### P10.10 — E2E Work Order to Final Package

**Objetivo:** Teste ponta a ponta completo e isolado.
**Escopo:** `tests/output_generator/test_e2e_package.py`
**CLI:** Nenhum novo (usa existentes)
**Testes mínimos:** 5 (E2E)
**Dependências:** P10.8 + P10.9

### P10.11 — P10 Final Seal Audit

**Objetivo:** Auditoria final, relatório, contagem de testes.
**Escopo:** Docs + selo final
**Testes:** Regressão completa
**Dependências:** Todos os blocos anteriores

---

## Estimativa de testes

| Bloco | Mínimo | Estimado |
|---|---|---|
| P10.2 JSON/Spec Writers | 8 | ~10 |
| P10.3 CSV Writer | 7 | ~8 |
| P10.4 Multi-File Package | 8 | ~9 |
| P10.5 Manifest Registry | 7 | ~8 |
| P10.6 Validation Layer | 8 | ~9 |
| P10.7 Approval Bridge | 7 | ~8 |
| P10.8 WO → Package | 8 | ~9 |
| P10.9 Batch Generator | 8 | ~9 |
| P10.10 E2E | 5 | ~6 |
| P10.11 Seal | — | — |
| **TOTAL** | **66** | **~76** |

---

## Progress Tracker

| Bloco | Status | Commit | Testes | Data |
|---|---|---|---|---|
| P10.2 | ⏳ pending | — | —/8 | — |
| P10.3 | ⏳ pending | — | —/7 | — |
| P10.4 | ⏳ pending | — | —/8 | — |
| P10.5 | ⏳ pending | — | —/7 | — |
| P10.6 | ⏳ pending | — | —/8 | — |
| P10.7 | ⏳ pending | — | —/7 | — |
| P10.8 | ⏳ pending | — | —/8 | — |
| P10.9 | ⏳ pending | — | —/8 | — |
| P10.10 | ⏳ pending | — | —/5 | — |
| P10.11 | ⏳ pending | — | — | — |

---

## Pontos de parada recomendados

Após P10.4 — pausa para review de fundação (md + json + csv + package base).
Após P10.7 — pausa para review de integração (registry + validation + approval bridge).
Após P10.10 — pausa antes do selo final.

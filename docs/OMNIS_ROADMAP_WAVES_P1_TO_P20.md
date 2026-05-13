# OMNIS ROADMAP — Waves P1 to P20

> **Operador:** Lucas Tigre (Tigrão) — 100% solo
> **Stack:** Claude Code + Python + Docker + PostgreSQL + CrewAI
> **Propósito:** Um homem, uma máquina, um império de mídia — 2.32M seguidores, 6 perfis
> **Gerado:** 2026-05-12 pós-Onda 3

---

## 1. Estado Atual — Pós-Onda 3

- **Branch:** `master` — up to date with `origin/master`
- **Último commit:** `becb3e2` — merge: p5 marketing supreme skeleton
- **Tag:** `onda3-complete-20260512`
- **Working tree:** clean
- **Full suite:** 3083 passed, 2 skipped, 0 failures
- **Commits acumulados:** 146+ desde o início
- **Módulos integrados:** 10

## 2. Módulos Já Integrados

| # | Módulo | Pasta `src/` | Pasta `tests/` | Onda | Commit Merge |
|---|---|---|---|---|---|
| 1 | Mission Adapter | `src/mission/` | `tests/mission/` | Onda 1 | `9825847` |
| 2 | App Factory | `src/app_factory/` | `tests/app_factory/` | Onda 1 | `a52c06b` |
| 3 | Automation | `src/automation/` | `tests/automation/` | Onda 1 | `6d8d365` |
| 4 | Governance & Audit | `src/governance/` | `tests/governance/` | Onda 2 | `18febbc` |
| 5 | Analytics | `src/analytics/` | `tests/analytics/` | Onda 2 | `afcf85d` |
| 6 | Computer Ops | `src/computer_ops/` | `tests/computer_ops/` | Onda 2 | `4b099d7` |
| 7 | Finance | `src/finance/` | `tests/finance/` | Onda 3 | `39053bb` |
| 8 | Commercial SDR | `src/commercial_sdr/` | `tests/commercial_sdr/` | Onda 3 | `811879c` |
| 9 | Sales CRM | `src/sales_crm/` | `tests/sales_crm/` | Onda 3 | `33578e7` |
| 10 | Marketing Supreme | `src/marketing/` | `tests/marketing/` | Onda 3 | `becb3e2` |

## 3. Tabela P1–P20

| P# | Nome Funcional | Status | Onda | Dependências | Pasta Principal | Risco | Pode Paralelizar? | Critério de Pronto |
|---|---|---|---|---|---|---|---|---|
| P1 | Content Queue & Scheduling | pending | Onda 4+ | — | `src/content_queue/` | Baixo | Sim | CRUD fila, agendamento, JSONL persistence, testes isolados |
| P2 | Creative Production OS | pending | Onda 4+ | P1 | `src/creative_production/` | Baixo | Sim | Brief, production items, review/exporter, testes isolados |
| P3 | Caption & Approval Pipeline | pending | Onda 4+ | P1, P2 | `src/caption_approval/` | Baixo | Sim | Draft → review → approve/reject gate, testes isolados |
| P4 | Memory Pack / Akasha Bridge | pending | Onda 4 | — | `src/memory/` | Médio | Sim | Conexão pgvector, busca híbrida, context injector, testes isolados |
| P5 | Marketing Supreme | **integrated** | Onda 3 | — | `src/marketing/` | — | ✅ Feito | 90 testes, modelos + service + exporters |
| P6 | Design Art Engine | pending | Onda 4 | — | `src/design/` | Médio | Sim | Geração de assets visuais, templates, validação, testes isolados |
| P7 | Video Studio | pending | Onda 4 | — | `src/video/` | Alto | Sim | Pipeline vídeo, edição, render, testes isolados |
| P8 | Publisher / ARGOS Export | pending | Onda 4+ | P3, P6, P7 | `src/publisher/` | Alto | Não (depende de P3+P6+P7) | Pacote de publicação completo, export argos-ready, testes isolados |
| P9 | Commercial SDR | **integrated** | Onda 3 | — | `src/commercial_sdr/` | — | ✅ Feito | 124 testes, lead models + service |
| P10 | Sales CRM | **integrated** | Onda 3 | P9 | `src/sales_crm/` | — | ✅ Feito | 114 testes, pipeline + deal models |
| P11 | App Factory | **integrated** | Onda 1 | mission | `src/app_factory/` | — | ✅ Feito | App scaffolding, templates, testes isolados |
| P12 | Automation | **integrated** | Onda 1 | — | `src/automation/` | — | ✅ Feito | n8n client, workflow registry, testes isolados |
| P13 | Analytics | **integrated** | Onda 2 | — | `src/analytics/` | — | ✅ Feito | Métricas, reports, aggregations, testes isolados |
| P14 | Finance | **integrated** | Onda 3 | — | `src/finance/` | — | ✅ Feito | 155 testes, revenue models + service |
| P15 | Computer Ops | **integrated** | Onda 2 | — | `src/computer_ops/` | — | ✅ Feito | Disk audit, docker health, system checks, testes isolados |
| P16 | Observability & Monitoring | pending | Onda 5+ | P13, P15 | `src/observability/` | Baixo | Sim | Logs, alerts, health dashboard, testes isolados |
| P17 | Delivery & Client Portal | pending | Onda 5+ | P8, P10 | `src/delivery/` | Médio | Não (depende de P8+P10) | Entrega de assets ao cliente, portal, feedback loop |
| P18 | Governance & Audit | **integrated** | Onda 2 | — | `src/governance/` | — | ✅ Feito | Audit trail, compliance checks, testes isolados |
| P19 | Campaign Manager | pending | Onda 5+ | P5, P8, P13 | `src/campaign/` | Médio | Não (depende de P5+P8+P13) | Campanhas ponta a ponta, métricas, ROI tracking |
| P20 | OMNIS Supreme | pending | Onda 6+ | P1–P19 | `src/omnis_supreme/` | Alto | Não (depende de tudo) | Orquestração total, cockpit, autonomia supervisionada |

### Resumo de Status

- **Integrados:** 10/20 (P5, P9, P10, P11, P12, P13, P14, P15, P18 + mission)
- **Pending:** 10/20
- **Onda 4 candidatos:** P1, P2, P3, P4, P6, P7 (baixa dependência entre si)

## 4. Histórico de Ondas

### Onda 1 — Fundação Operacional

| Commit Merge | Módulo | Commit Original |
|---|---|---|
| `9825847` | Mission Adapter | `49b5899` |
| `a52c06b` | P11 App Factory | `4b6b2e3` |
| `6d8d365` | P12 Automation | `a92b1fa` |

**Marcos:** Primeira onda com merge sequencial. Estabeleceu o padrão mission → app_factory → automation.

### Onda 2 — Infraestrutura & Controle

| Commit Merge | Módulo | Commit Original |
|---|---|---|
| `18febbc` | P18 Governance & Audit | `345f042` |
| `afcf85d` | P13 Analytics | `977108a` |
| `4b099d7` | P15 Computer Ops | `3c083d7` |

**Tags:** `onda2-complete-20260512` → `4b099d7`
**Marcos:** Primeira onda com parallel worktrees + merge sequencial. Protocolo de monitoramento estabelecido (`e7bd603`).

### Onda 3 — Negócio Core

| Commit Merge | Módulo | Commit Original | Linhas |
|---|---|---|---|
| `39053bb` | P14 Finance | `c6fe124` | +2856 |
| `811879c` | P9 Commercial SDR | `9b4e9cc` | +2108 |
| `33578e7` | P10 Sales CRM | `9476d02` | +2705 |
| `becb3e2` | P5 Marketing Supreme | `fa0a528` | +2246 |

**Tags:** `pre-onda3-merge-20260512` → `4b099d7`, `onda3-complete-20260512` → `becb3e2`
**Bundles:** `omnis-pre-onda3-merge-20260512.bundle`, `omnis-onda3-complete-20260512.bundle`
**Full suite final:** 3083 passed, 2 skipped, 0 failures
**Total linhas adicionadas:** +9915

## 5. Onda 4 — Recomendada

### Frentes Candidatas

| Ordem | P# | Módulo | Risco | Justificativa |
|---|---|---|---|---|
| 1 | P4 | Memory Pack / Akasha Bridge | Médio | Conecta conhecimento existente (20K docs, 606K chunks) ao pipeline |
| 2 | P6 | Design Art Engine | Médio | Geração de assets visuais para collabs |
| 3 | P7 | Video Studio | Alto | Pipeline de vídeo — core do negócio Instagram |
| 4 | P1 | Content Queue & Scheduling | Baixo | Fila de conteúdo — fundação para P2 e P3 |

### Por que não P8 ainda?

P8 (Publisher / ARGOS Export) depende de P3 (Caption), P6 (Design) e P7 (Video). Lançar P8 antes desses geraria retrabalho. P8 entra na Onda 5.

### Estrutura Esperada (por módulo)

```
src/memory/                  # P4 — Memory Pack
├── __init__.py
├── models.py                # Dataclasses: MemoryContext, SearchResult, ChunkRef
├── service.py               # Akasha client wrapper, busca híbrida
├── errors.py                # MemoryError, ConnectionError, EmbeddingError
tests/memory/
├── __init__.py
├── test_models.py
├── test_service.py
docs/memory/
└── P4_MEMORY_PACK_SKELETON.md
```

## 6. Regras de Paralelização

1. **Máximo 4 frentes por onda** — evita fragmentação e conflitos
2. **Escopo isolado** — cada branch toca apenas `src/<modulo>/`, `tests/<modulo>/`, `docs/<modulo>/`
3. **Commit por frente** — `feat: add p<N> <nome> skeleton` (1 commit squash por worktree)
4. **Targeted test por frente** — `python -m pytest tests/<modulo>/ -q` deve passar isolado
5. **Full suite após cada merge** — `python -m pytest tests/ -q` após cada `git merge --no-ff`
6. **Tag + bundle + push ao fim da onda** — checkpoint imutável antes de avançar

### Protocolo de Onda

```
1. Criar tag pre-onda<N>-merge-<date>
2. Criar bundle backup pré-merge na Desktop
3. Criar 4 worktrees (1 por frente)
4. Cada worktree: implementar skeleton → targeted test → commit
5. Merge sequencial (1 por vez): merge → targeted → full suite
6. Stashar exports/ e arquivos voláteis
7. Criar tag onda<N>-complete-<date>
8. Criar bundle backup pós-merge na Desktop
9. Remover worktrees e branches parallel
10. Push master + tags
```

## 7. Critérios para OMNIS Supreme (P20)

OMNIS Supreme é o meta-sistema que unifica todos os módulos P1–P19 sob orquestração autônoma.

| Componente | Descrição | Estado |
|---|---|---|
| **Mission Package Universal** | Toda tarefa é encapsulada como mission package com contract + state + outputs | Parcial (mission/ existe) |
| **Squads Dinâmicos** | Agentes montados sob demanda por competência (skill matcher + role registry) | Parcial (src/squad_composer/) |
| **Skill Matcher** | Match automático de tarefa → skill → agente | Parcial (src/skill_matcher/) |
| **Capability Forge** | Geração de novas capabilities a partir de gaps detectados | Parcial (src/capability_forge_lite/) |
| **Approval Gate** | Toda ação destrutiva passa por approval center | Parcial (src/approval_center/) |
| **Memory Loop** | Toda execução alimenta Akasha + Mem0 para contexto futuro | Parcial (src/knowledge_context/) |
| **Execution Graph** | DAG de passos com replay, resume, dry-run | Parcial (src/execution_graph/) |
| **Cockpit** | Dashboard unificado de todas as frentes, jobs, métricas e saúde | Pendente |
| **Autonomia Supervisionada** | Sistema opera sozinho com gates de segurança; humano só aprova/rejeita | Pendente |

### Gatilho para iniciar P20

- P1–P19 integrados e testados
- Full suite ≥ 5000 testes passando
- Publisher OS publicando com OAuth real
- 3 ondas consecutivas sem regressão

## 8. Mapa de Dependências

```
                    ┌──────────────────────────────────────┐
                    │           P20 OMNIS SUPREME           │
                    └──────────────────────────────────────┘
                           ↑ (depende de tudo abaixo)
    ┌───────┬───────┬───────┼───────┬───────┬───────┬───────┐
    │       │       │       │       │       │       │       │
    P17     P19     P8      P16     P3      P2      P1      P4
 (delivery)(campaign)(publisher)(obs) (caption)(creative)(queue)(memory)
      ↑       ↑       ↑               ↑       ↑
      └───┬───┘       ├───────────────┘       │
          │           │                       │
          P10         P6    P7               P1
        (sales)    (design)(video)         (queue)

  LEGENDA:
  ✅ Integrated (Onda 1-3): mission, P5, P9, P10, P11, P12, P13, P14, P15, P18
  🔲 Onda 4: P4, P6, P7, P1
  🔲 Onda 5: P2, P3, P8, P16
  🔲 Onda 6: P17, P19
  🔲 Onda 7+: P20
```

## 9. Riscos e Bloqueios Ativos

| Risco | Severidade | Status |
|---|---|---|
| OAuth Meta pendente (META_APP_ID/SECRET) | Alto | Bloqueia publicação real |
| 2 containers unhealthy (crm-tigre-backend, jarvis_frontend) | Baixo | Não crítico |
| NOTION_TOKEN não configurado | Baixo | Sync com Notion pendente |
| Oportunidade 150 influenciadores Interior SP | Médio | Aguardando pipeline commercial_sdr |
| Disco C:\ 15.3% livre (141.7 GB) | Médio | Monitorar; P15 computer_ops já trackeia |

---

*"O que gera dinheiro hoje?" — A pergunta guia.*
*OMNIS — Do latim "omnis" = "tudo", "cada", "todo".*

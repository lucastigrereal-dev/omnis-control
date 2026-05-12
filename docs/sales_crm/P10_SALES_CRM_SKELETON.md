# P10 Sales/CRM Skeleton — Relatório Final

**Frente:** P10 — Sales & CRM Skeleton
**Onda:** 2
**Branch:** `parallel/p10-sales-crm-skeleton`
**Data:** 2026-05-12
**Modo:** deterministic, dry-run, zero-network, zero-Docker, zero-database

---

## 1. Visão Geral

Skeleton isolado para Sales/CRM seguindo o padrão OMNIS de pacotes determinísticos. Modela pipeline de vendas, leads, deals, atividades comerciais, objeções, propostas e follow-ups. Sem envio real de mensagens, sem WhatsApp, sem CRM externo, sem banco real.

### Escopo Permitido

| Diretório | Status |
|---|---|
| `src/sales_crm/` | Criado |
| `tests/sales_crm/` | Criado |
| `docs/sales_crm/` | Criado |

### Escopo Proibido (não tocado)

`src/commercial_sdr/`, `src/mission/`, `src/app_factory/`, `src/automation/`, `src/computer_ops/`, `src/governance/`, `src/analytics/`, `src/output_generator/`, `src/core/`, `src/cli.py`, `pyproject.toml`, `.env`, `data/`, `exports/`, `logs/`, `config/`

---

## 2. Arquitetura

```
src/sales_crm/
  __init__.py       — API pública, __all__ com 28 símbolos
  models.py         — 8 models + 9 enums + 1 constant set
  errors.py         — 11 classes de erro hierárquicas
  service.py        — SalesCRMPlanner + PipelineSummary + ScoreResult + ValidationResult

tests/sales_crm/
  __init__.py
  test_models.py    — 47 testes (8 modelos + enums + constantes)
  test_service.py   — 41 testes (planner + resultados + fluxo integrado)
```

---

## 3. Modelos

### 3.1 Lead

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `str` | Prefixo `lead_` + 8 hex |
| `name` | `str` | Nome do lead (obrigatório) |
| `business_name` | `str \| None` | Nome do estabelecimento |
| `contact_phone` | `str \| None` | Telefone WhatsApp |
| `contact_email` | `str \| None` | Email de contato |
| `instagram_handle` | `str \| None` | @ do Instagram |
| `source` | `LeadSource` | Origem do lead |
| `status` | `LeadStatus` | Status de qualificação |
| `score` | `float` | Pontuação (preenchida por score_lead) |
| `tags` | `list[str]` | Tags de categorização |
| `notes` | `str \| None` | Notas internas |
| `city` | `str \| None` | Cidade |
| `state` | `str \| None` | Estado/UF |
| `niche` | `str \| None` | Nicho (hotel, restaurante, etc.) |
| `follower_count` | `int \| None` | Seguidores no Instagram |
| `dry_run` | `bool` | Default `True` |

**Factory:** `Lead.new(name, ...)` — valida nome obrigatório, faz strip de strings.
**Properties:** `has_contact_info`, `is_qualified`.

### 3.2 Deal

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `str` | Prefixo `deal_` + 8 hex |
| `lead_id` | `str` | Lead vinculado |
| `package` | `str` | starter, growth, ou premium |
| `value_brl` | `float` | Valor em reais (mapeado do pacote) |
| `stage` | `PipelineStage` | Estágio atual no pipeline |
| `priority` | `DealPriority` | Prioridade: low, medium, high, urgent |
| `probability` | `float` | Probabilidade de fechamento (mapeada do stage) |
| `expected_close_date` | `str \| None` | Data esperada de fechamento |
| `dry_run` | `bool` | Default `True` |

**Factory:** `Deal.new(lead_id, package, ...)` — valida package.
**Properties:** `expected_value` (value_brl * probability), `is_active` (não terminal).

### 3.3 SalesActivity

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `str` | Prefixo `act_` + 8 hex |
| `lead_id` | `str \| None` | Lead associado |
| `deal_id` | `str \| None` | Deal associado |
| `activity_type` | `ActivityType` | Tipo de atividade |
| `description` | `str` | Descrição da atividade |
| `outcome` | `str \| None` | Resultado |
| `approval_required` | `bool` | True para atividades externas |
| `approved` | `bool` | Default False |
| `risk_flags` | `list[str]` | Flags de risco (ex: "external_contact_blocked") |

**Factory:** `SalesActivity.new(activity_type, description, ...)` — marca approval_required para CALL, WHATSAPP, EMAIL, DM.

### 3.4 ObjectionRecord

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `str` | Prefixo `obj_` + 8 hex |
| `lead_id` | `str \| None` | Lead associado |
| `deal_id` | `str \| None` | Deal associado |
| `category` | `ObjectionCategory` | Categoria da objeção |
| `description` | `str` | Descrição da objeção |
| `response` | `str \| None` | Resposta dada |
| `resolved` | `bool` | Se foi resolvida |
| `resolved_at` | `str \| None` | Timestamp da resolução |

**Método:** `resolve(response)` — marca como resolvida com timestamp.

### 3.5 ProposalRecord

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `str` | Prefixo `prop_` + 8 hex |
| `lead_id` | `str \| None` | Lead associado |
| `deal_id` | `str \| None` | Deal associado |
| `package` | `str` | Pacote proposto |
| `value_brl` | `float` | Valor da proposta |
| `status` | `ProposalStatus` | draft, sent, viewed, accepted, declined, expired |
| `content_summary` | `str \| None` | Resumo do conteúdo |
| `approval_required` | `bool` | Default True (envio futuro requer aprovação) |

### 3.6 FollowUpTask

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `str` | Prefixo `fup_` + 8 hex |
| `lead_id` | `str \| None` | Lead associado |
| `deal_id` | `str \| None` | Deal associado |
| `description` | `str` | Descrição da tarefa |
| `scheduled_at` | `str` | Data/hora agendada (ISO 8601) |
| `status` | `FollowUpStatus` | pending, in_progress, completed, cancelled |
| `completed_at` | `str \| None` | Timestamp de conclusão |

**Métodos:** `complete(notes)`, `cancel(notes)`.
**Property:** `is_overdue` — True se passou da data e não está completado/cancelado.

### 3.7 SalesPipeline

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `str` | Prefixo `pipe_` + 8 hex |
| `name` | `str` | Nome do pipeline |
| `description` | `str` | Descrição |
| `deals` | `list[Deal]` | Deals no pipeline |

**Properties:** `active_deals`, `total_value`, `weighted_value`, `deal_count`, `active_count`.
**Métodos:** `count_by_stage(stage)`, `value_by_stage(stage)`.

---

## 4. Enums de Domínio

| Enum | Cardinalidade | Valores |
|---|---|---|
| `PipelineStage` | 6 | prospecting, qualification, proposal, negotiation, closed_won, closed_lost |
| `LeadSource` | 6 | instagram, direct_contact, referral, inbound, manual_prospecting, unknown |
| `LeadStatus` | 5 | new, attempted_contact, engaged, qualified, disqualified |
| `ActivityType` | 7 | call, whatsapp, email, dm, meeting, follow_up, note |
| `ObjectionCategory` | 8 | price, timing, competitor, need, authority, trust, budget, other |
| `DealPriority` | 4 | low, medium, high, urgent |
| `FollowUpStatus` | 4 | pending, in_progress, completed, cancelled |
| `ProposalStatus` | 6 | draft, sent, viewed, accepted, declined, expired |

---

## 5. Constantes

| Constante | Cardinalidade | Valores |
|---|---|---|
| `VALID_PACKAGES` | 3 | starter (R$350), growth (R$990), premium (R$1.200) |

---

## 6. Serviço

### 6.1 SalesCRMPlanner

Classe principal de planejamento CRM. `dry_run=True` por padrão.

| Método | Retorno | Descrição |
|---|---|---|
| `create_lead(name, source, ...)` | `Lead` | Cria e registra lead |
| `score_lead(lead_id, threshold=50.0)` | `ScoreResult` | Scoring determinístico com breakdown |
| `create_deal(lead_id, package, ...)` | `Deal` | Cria deal vinculado ao lead |
| `advance_deal(deal_id, new_stage)` | `Deal` | Avança deal para novo stage |
| `log_activity(type, desc, lead_id, deal_id, ...)` | `SalesActivity` | Loga atividade (bloqueia externas) |
| `record_objection(category, desc, lead_id, deal_id, ...)` | `ObjectionRecord` | Registra objeção |
| `plan_follow_up(desc, scheduled_at, lead_id, deal_id, ...)` | `FollowUpTask` | Agenda follow-up |
| `create_proposal(package, lead_id, deal_id, ...)` | `ProposalRecord` | Cria proposta (draft) |
| `build_pipeline_summary(pipeline)` | `PipelineSummary` | Gera snapshot agregado |
| `validate_pipeline(pipeline)` | `ValidationResult` | Valida integridade do pipeline |

**Propriedades de inventário:** `list_leads()`, `list_deals()`, `list_activities()`, `list_objections()`, `list_follow_ups()`, `list_proposals()`, `lead_count`, `deal_count`.

### 6.2 ScoreResult

| Campo | Tipo | Descrição |
|---|---|---|
| `lead_id` | `str` | Lead avaliado |
| `score` | `float` | Pontuação total (max ~100) |
| `breakdown` | `dict[str, float]` | Decomposição: contact_info, follower_signal, location, niche_fit, has_business_name, contact_channels |
| `qualifies` | `bool` | score >= threshold |
| `recommended_package` | `str \| None` | premium (80+), growth (60+), starter (40+) |
| `notes` | `list[str]` | Observações do scoring |

### 6.3 PipelineSummary

Snapshot agregado do pipeline com stage_breakdown, métricas won/lost, e riscos detectados.

### 6.4 ValidationResult

| Campo | Tipo | Descrição |
|---|---|---|
| `valid` | `bool` | Resultado da validação |
| `issues` | `list[str]` | Problemas críticos |
| `warnings` | `list[str]` | Avisos não-bloqueantes |
| `ok` | `bool` (property) | `valid and len(issues) == 0` |

---

## 7. Hierarquia de Erros

```
SalesCRMError
├── InvalidLeadError
├── InvalidDealError
├── InvalidPipelineError
├── PipelineStageError
├── InvalidActivityError
├── InvalidObjectionError
├── InvalidProposalError
├── InvalidFollowUpError
├── ExternalContactBlockedError
└── RiskFlagError
```

---

## 8. Regras de Segurança

1. **Sem envio real** — Nenhuma atividade externa é executada de fato.
2. **Sem WhatsApp real** — Bloqueado via `ExternalContactBlockedError`.
3. **Sem CRM real** — Modelagem interna apenas.
4. **Sem banco real** — Dados em memória (dicts e lists).
5. **approval_required** — Proposals e atividades externas requerem aprovação explícita.
6. **risk flags** — Atividades externas recebem flag `external_contact_blocked`.
7. **dry_run=True** — Padrão em todos os modelos e operações.

---

## 9. Decisões de Design

1. **Dataclasses, não Pydantic** — Seguindo o padrão dos skeletons analytics (P13), governance (P18), computer_ops (P15).
2. **Enums para estados** — PipelineStage, LeadStatus, ActivityType, etc. garantem valores válidos em runtime.
3. **Scoring determinístico** — Fórmula com 6 dimensões, sem ML/LLM. Transparente e auditável.
4. **Bloqueio de contato externo** — `log_activity` lança `ExternalContactBlockedError` para CALL/WHATSAPP/EMAIL/DM.
5. **Validação de integridade** — `validate_pipeline` detecta deals órfãos, probabilidades inconsistentes, leads duplicados.
6. **Prefixos de ID** — `lead_`, `deal_`, `act_`, `obj_`, `prop_`, `fup_`, `pipe_` + 8 hex.
7. **`frozenset` para constantes** — Imutável, hashable, O(1) lookup.

---

## 10. Limitações (by Design)

- Sem persistência real (sem banco, sem JSONL store)
- Sem envio de WhatsApp/email/DM
- Sem integração com CRM externo (HubSpot, Pipedrive, etc.)
- Sem automação de follow-ups (apenas modelagem)
- Sem integração com CLI (`src/cli.py`)
- Sem analytics de pipeline (conversão, ciclo médio, etc.)
- Sem templates de proposta reais
- Sem notificações ou alertas

---

## 11. Próximos Passos

1. **P19 Sales Store** — Adicionar persistência JSONL local para leads, deals e atividades.
2. **P22 Sales CLI** — Integrar com `src/cli.py` para comandos `omnis sales *`.
3. **P25 Pipeline Analytics** — Métricas de conversão, tempo de ciclo, win rate por origem.
4. **Conectores** — Integração futura com WhatsApp Business API, email transacional.
5. **Automação** — Follow-ups automáticos, lembretes, sequências de contato.

---

## 12. Verificação Final

**Status:** Todos os testes passam.
**Modo:** Determinístico. Zero LLM. Zero rede. Zero Docker.
**Gerado:** 2026-05-12 — P10 Sales/CRM Skeleton v1.0.0

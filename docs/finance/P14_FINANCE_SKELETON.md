# P14 Finance Skeleton — Relatório Final

**Frente:** P14 — Finance Skeleton
**Onda:** 3
**Branch:** `parallel/p14-finance-skeleton`
**Data:** 2026-05-12
**Modo:** deterministic, dry-run, zero-network, zero-Docker, zero-database

---

## 1. Visão Geral

Skeleton isolado para gestão financeira determinística. Sem transações reais, sem banco real, sem rede, sem API bancária — apenas modelagem, cálculo e planejamento em dry-run.

### Escopo Permitido

| Diretório | Status |
|---|---|
| `src/finance/` | Criado |
| `tests/finance/` | Criado |
| `docs/finance/` | Criado |

### Escopo Proibido (não tocado)

`src/mission/`, `src/app_factory/`, `src/automation/`, `src/computer_ops/`, `src/governance/`, `src/analytics/`, `src/marketing/`, `src/commercial_sdr/`, `src/sales_crm/`, `src/output_generator/`, `src/core/`, `src/cli.py`, `pyproject.toml`, `.env`, `data/`, `exports/`, `logs/`, `config/`

---

## 2. Arquitetura

```
src/finance/
  __init__.py       — API pública, __all__ com 31 símbolos
  models.py         — 7 dataclasses + 4 constantes + 2 enums
  errors.py         — 10 classes de erro hierárquicas
  service.py        — FinancePlanner + ValidationResult + 6 funções standalone

tests/finance/
  __init__.py
  test_models.py    — 66 testes (7 modelos + constantes + enums)
  test_service.py   — 89 testes (planner + funções standalone + E2E)
```

---

## 3. Modelos

### 3.1 RevenueRecord

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `str` | Prefixo `rev_` + 8 hex |
| `source` | `str` | Origem da receita (ex: "Collab Serhs") |
| `description` | `str` | Descrição da receita |
| `amount_brl` | `Decimal` | Valor em reais |
| `category` | `str` | collab, publi, consulting, affiliate, product_sale, subscription, licensing, other |
| `recorded_at` | `str` | ISO 8601 UTC |
| `reference_month` | `str` | Mês de referência (YYYY-MM) |
| `client` | `str \| None` | Cliente (opcional) |
| `dry_run` | `bool` | Default `True` |
| `metadata` | `dict[str, str]` | Metadados extras |

**Factory:** `RevenueRecord.new(source, description, amount_brl, category, reference_month, ...)`

### 3.2 CostRecord

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `str` | Prefixo `cst_` + 8 hex |
| `description` | `str` | Descrição da despesa |
| `amount_brl` | `Decimal` | Valor em reais |
| `category` | `str` | ads, tools, services, travel, equipment, taxes, salary, marketing, infra, other |
| `vendor` | `str \| None` | Fornecedor |
| `recorded_at` | `str` | ISO 8601 UTC |
| `reference_month` | `str` | Mês de referência |
| `risk_flags` | `list[RiskFlag]` | Flags de risco: PAYMENT, BILLING, BUDGET_EXCEEDED, FORECAST_SENSITIVE |
| `dry_run` | `bool` | Default `True` |
| `metadata` | `dict[str, str]` | Metadados extras |

**Factory:** `CostRecord.new(description, amount_brl, category, reference_month, ...)`

### 3.3 CommissionRule

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `str` | Prefixo `com_` + 8 hex |
| `name` | `str` | Nome da regra |
| `rate_pct` | `Decimal` | Percentual de comissão (0-100) |
| `min_revenue_brl` | `Decimal` | Receita mínima para aplicar |
| `max_revenue_brl` | `Decimal \| None` | Receita máxima (None = sem teto) |
| `tier_name` | `str` | Nome do tier |
| `approval_required` | `bool` | Requer aprovação |
| `created_at` | `str` | ISO 8601 UTC |

**Métodos:** `applies_to(revenue_brl)` → bool, `apply(revenue_brl)` → Decimal
**Property:** `is_tiered` → bool

### 3.4 BudgetGuard

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `str` | Prefixo `bgt_` + 8 hex |
| `name` | `str` | Nome do orçamento |
| `budget_limit_brl` | `Decimal` | Limite em reais |
| `spent_brl` | `Decimal` | Gasto atual |
| `reference_month` | `str` | Mês de referência |
| `category` | `str` | Categoria de custo |
| `approval_required` | `bool` | Default `True` |
| `risk_flags` | `list[RiskFlag]` | Flags de risco |
| `approval_status` | `ApprovalStatus` | pending / approved / rejected / not_required |

**Properties:** `remaining_brl`, `is_over_budget`, `usage_pct`
**Métodos:** `approve()`, `reject()`

### 3.5 ForecastPlan

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `str` | Prefixo `fct_` + 8 hex |
| `title` | `str` | Título |
| `method` | `str` | linear, moving_average, seasonal_naive, manual |
| `period_months` | `int` | Meses projetados |
| `historical_totals` | `list[Decimal]` | Totais históricos |
| `projected_totals` | `list[Decimal]` | Valores projetados |
| `confidence_pct` | `Decimal` | Nível de confiança (0-100) |
| `risk_flags` | `list[RiskFlag]` | Flags de risco |

**Properties:** `historical_avg`, `projected_total`

### 3.6 ROISummary

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `str` | Prefixo `roi_` + 8 hex |
| `title` | `str` | Título |
| `total_revenue_brl` | `Decimal` | Receita total |
| `total_cost_brl` | `Decimal` | Custo total |
| `net_profit_brl` | `Decimal` | Lucro líquido |
| `roi_pct` | `Decimal` | ROI = (net / cost) * 100 |
| `reference_period` | `str` | Período de referência |

**Properties:** `is_profitable`, `profit_margin_pct`

### 3.7 FinanceReport

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `str` | Prefixo `fnr_` + 8 hex |
| `title` | `str` | Título |
| `reference_period` | `str` | Período |
| `total_revenue_brl` | `Decimal` | Receita total |
| `total_cost_brl` | `Decimal` | Custo total |
| `net_result_brl` | `Decimal` | Resultado líquido |
| `budget_guards` | `list[BudgetGuard]` | Guardas de orçamento |
| `goals` | `list[dict[str, str]]` | Metas financeiras |
| `alerts` | `list[str]` | Alertas (cash, budget) |
| `roi_summaries` | `list[ROISummary]` | Sumários de ROI |
| `risk_flags` | `list[RiskFlag]` | Flags de risco consolidados |
| `approval_required` | `bool` | Requer aprovação |
| `approval_status` | `ApprovalStatus` | Status da aprovação |

**Properties:** `is_net_positive`, `over_budget_count`
**Métodos:** `approve()`, `reject()`

---

## 4. Constantes de Domínio

| Constante | Cardinalidade | Valores |
|---|---|---|
| `VALID_REVENUE_CATEGORIES` | 8 | collab, publi, consulting, affiliate, product_sale, subscription, licensing, other |
| `VALID_COST_CATEGORIES` | 10 | ads, tools, services, travel, equipment, taxes, salary, marketing, infra, other |
| `VALID_FORECAST_METHODS` | 4 | linear, moving_average, seasonal_naive, manual |
| `VALID_REPORT_PERIODS` | 5 | daily, weekly, monthly, quarterly, yearly |

---

## 5. Enums

### 5.1 RiskFlag

| Valor | Significado |
|---|---|
| `PAYMENT` | Ação de pagamento |
| `BILLING` | Ação de cobrança |
| `BUDGET_EXCEEDED` | Orçamento estourado |
| `FORECAST_SENSITIVE` | Forecast com sensibilidade alta |

### 5.2 ApprovalStatus

| Valor | Significado |
|---|---|
| `PENDING` | Aguardando aprovação |
| `APPROVED` | Aprovado |
| `REJECTED` | Rejeitado |
| `NOT_REQUIRED` | Sem necessidade de aprovação |

---

## 6. Serviço

### 6.1 FinancePlanner

Classe principal de planejamento financeiro. `dry_run=True` por padrão.

| Método | Retorno | Descrição |
|---|---|---|
| `record_revenue(source, desc, amount, category, month, ...)` | `RevenueRecord` | Registra receita |
| `record_cost(desc, amount, category, month, ...)` | `CostRecord` | Registra custo |
| `define_commission_rule(name, rate, ...)` | `CommissionRule` | Define regra de comissão |
| `compute_commissions(revenue_brl)` | `list[dict]` | Aplica regras à receita |
| `set_budget_guard(name, limit, month, ...)` | `BudgetGuard` | Cria guarda de orçamento |
| `check_budget(guard)` | `None` | Levanta BudgetExceededError se estourado |
| `create_forecast(title, historical, method, ...)` | `ForecastPlan` | Cria previsão |
| `forecast_with_sensitivity(title, historical, ...)` | `ForecastPlan` | Previsão com flag de sensibilidade |
| `compute_roi(title, period)` | `ROISummary` | Calcula ROI dos registros |
| `build_report(title, period, ...)` | `FinanceReport` | Constrói relatório financeiro |
| `validate()` | `ValidationResult` | Valida registros atuais |

**Properties:** `revenue_count`, `cost_count`, `total_revenue`, `total_cost`, `net_result`

### 6.2 Funções Standalone

| Função | Descrição |
|---|---|
| `calculate_roi(revenue, cost, ...)` → `ROISummary` | Cálculo direto de ROI |
| `forecast_revenue(title, historical, method, ...)` → `ForecastPlan` | Geração de forecast |
| `apply_commission_rule(rule, revenue)` → `dict` | Aplica comissão a valor |
| `build_budget_guard(name, limit, month, ...)` → `BudgetGuard` | Cria guarda de orçamento |
| `build_finance_report(title, period, revenues, costs, ...)` → `FinanceReport` | Constrói relatório |
| `validate_finance_inputs(revenues, costs)` → `ValidationResult` | Valida listas de registros |

---

## 7. Hierarquia de Erros

```
FinanceError
├── InvalidRevenueError
├── InvalidCostError
├── InvalidCommissionError
├── BudgetExceededError
├── ForecastError
├── InvalidROIError
├── ReportError
├── ApprovalRequiredError
└── ValidationError
```

---

## 8. Resumo de Testes

| Arquivo | Testes | O que cobre |
|---|---|---|
| `test_models.py` | 66 | 13 RevenueRecord, 11 CostRecord, 14 CommissionRule, 14 BudgetGuard, 16 ForecastPlan, 13 ROISummary, 14 FinanceReport, 4 Constants, 4 RiskFlag, 4 ApprovalStatus |
| `test_service.py` | 89 | 4 ValidationResult, 3 calculate_roi, 3 forecast_revenue, 2 apply_commission_rule, 2 build_budget_guard, 5 build_finance_report, 3 validate_finance_inputs, 37 FinancePlanner, 1 E2E |
| **Total** | **155** | |

### Cobertura por modelo:
- Factory `.new()` com validação
- `to_dict()` / `from_dict()` round-trip
- Valores default
- Unicidade de IDs
- Rejeição de valores inválidos
- Testes para todas as constantes válidas
- Cálculos de ROI, forecast, comissão
- Fluxo E2E mensal completo

---

## 9. Decisões de Design

1. **Decimal para valores monetários** — Precisão para cálculos financeiros. Sem floats para dinheiro.
2. **Dataclasses, não Pydantic** — Padrão OMNIS. Zero dependências extras.
3. **`from __future__ import annotations`** — Lazy evaluation de type hints.
4. **`frozenset` para constantes** — Imutável, hashable, O(1).
5. **Prefixos de ID semânticos** — `rev_`, `cst_`, `com_`, `bgt_`, `fct_`, `roi_`, `fnr_`.
6. **RiskFlag enum** — Tipifica riscos: PAYMENT, BILLING, BUDGET_EXCEEDED, FORECAST_SENSITIVE.
7. **ApprovalStatus enum** — Workflow de aprovação: pending → approved/rejected.
8. **BudgetGuard com approval** — Toda guarda de orçamento requer aprovação por padrão.
9. **Forecast determinístico** — 4 métodos: linear, moving_average, seasonal_naive, manual. Sem ML.
10. **Serviço + funções standalone** — Uso como classe com estado (FinancePlanner) ou funções puras.

---

## 10. Limitações (by Design)

- Sem persistência real (sem banco, sem arquivos)
- Sem integração bancária ou API de pagamento
- Sem execução de cobrança real
- Sem integração com CLI (`src/cli.py`)
- Sem cálculos contábeis completos (DRE, balanço)
- Sem importação de extratos
- Sem conciliação bancária
- Forecast sem sazonalidade complexa ou ML

---

## 11. Próximos Passos

1. **P15 Finance Store** — Persistência JSONL local
2. **P17 Finance CLI** — Comandos `omnis finance *`
3. **P21 Finance Engine** — DRE, fluxo de caixa, conciliação
4. **Integração bancária** — APIs de banco e gateway de pagamento (com approval gate)

---

## 12. Verificação Final

```
$ python -m pytest tests/finance/ -q
........................................................................ [ 46%]
........................................................................ [ 92%]
...........                                                              [100%]
155 passed in 0.14s
```

**Status:** 155/155 PASS
**Modo:** Determinístico. Zero LLM. Zero rede. Zero Docker. Zero banco.
**Gerado:** 2026-05-12 — P14 Finance Skeleton v1.0.0

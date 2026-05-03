# Reconciliação de Setores — 9 atuais vs 14 futuros

**Data:** 2026-05-03
**Decisão Oficial:** Os 9 setores atuais são operacionais. Os 14 são visão futura. Não expandir agora.

---

## Mapeamento 9 → 14

| # | Setor OMNIS (9 atuais) | Blueprint Futuro (14) | Status |
|---|----------------------|----------------------|--------|
| 1 | `mission_control` | Core / Orquestração | ✅ Mapeado |
| 2 | `marketing_enterprise` | Conteúdo + Marketing | ✅ Mapeado |
| 3 | — *(dentro de marketing)* | Design | ⏳ Subcapacidade |
| 4 | `automation_integrations` | Publicação / ARGOS | ⏳ Subcamada |
| 5 | `sales_revenue` | Vendas / Conversão | ✅ Mapeado |
| 6 | — *(futuro)* | Relacionamento / DM | 🔮 Futuro |
| 7 | `finance_capital` | Financeiro | ✅ Mapeado |
| 8 | `memory_knowledge` | Memória / Conhecimento | ✅ Mapeado |
| 9 | — *(futuro)* | Inteligência / Pesquisa | 🔮 Futuro |
| 10 | `app_factory` | Engenharia | ✅ Mapeado |
| 11 | `automation_integrations` | Automação | ✅ Mapeado |
| 12 | `security_audit` | Auditoria / Segurança | ✅ Transversal |
| 13 | — *(meta-processo)* | Criação de Skills | 🔮 Em app_factory |
| 14 | — *(meta-processo)* | Criação de Setores | 🔮 Em runtime_agentic |

---

## Decisões de Boundary

| Blueprint Futuro | Onde fica agora | Por quê |
|-----------------|----------------|---------|
| Design | `marketing_enterprise` (subcapacidade) | Design de conteúdo é parte do fluxo de marketing |
| Publicação / ARGOS | `marketing_enterprise` + `automation_integrations` | ARGOS é subcamada operacional, não setor |
| Relacionamento / DM | Não implementado | Só depois do OAuth base funcionar |
| Inteligência / Pesquisa | `memory_knowledge` (parcial) | Precisa de Akasha+Qdrant operacionais |
| Criação de Skills | `app_factory` | É meta-processo de engenharia |
| Criação de Setores | `runtime_agentic` | É meta-processo de orquestração |

---

## Setores Operacionais (9)

Ver `config/sectors.yaml` para definições completas.

| Setor | Status | Fase |
|-------|--------|------|
| `marketing_enterprise` | ✅ operational | 2 |
| `sales_revenue` | 📋 blueprint | 3 |
| `app_factory` | 📋 blueprint | 2 |
| `automation_integrations` | 📋 blueprint | 3 |
| `memory_knowledge` | ✅ operational | 2 |
| `finance_capital` | 📋 blueprint | 4 |
| `security_audit` | ✅ operational | 1 |
| `mission_control` | ✅ operational | 1 |
| `runtime_agentic` | 📋 blueprint | 5+ |

---

## Próximos Passos

1. Manter 9 setores. Não expandir.
2. Quando um setor blueprint for implementado, atualizar `config/sectors.yaml`.
3. Quando um novo setor for necessário, criar via `app_factory` (meta-processo).
4. Revisar esta reconciliação quando Fase 4 (memória) e Fase 6 (runtime) começarem.

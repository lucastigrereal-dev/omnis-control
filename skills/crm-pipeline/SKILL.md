---
name: crm-pipeline
description: "Pipeline de vendas para hotéis: lead → qualificado → proposta → negociação → fechado/perdido"
sector: vendas_crm
model: haiku
cost_estimate: "$0.00/run (sqlite local)"
status: active
trigger: manual ou via jarvis-delegate
---

# CRM Pipeline

Gestão de vendas para hotéis. Pipeline completo: lead → qualificado → proposta → negociação → fechado/perdido.

## Modos

| Comando | Descrição |
|---|---|
| `crm-pipeline lead --nome "Hotel X" --hotel "Nome" --cidade "Natal" --valor 990 --perfil lucastigrereal` | Adicionar novo lead |
| `crm-pipeline list` | Listar todos leads |
| `crm-pipeline list --estagio qualificado` | Filtrar por estágio |
| `crm-pipeline list --dias 7` | Filtrar por próximo contato |
| `crm-pipeline stage --id 1 --estagio qualificado` | Avançar lead |
| `crm-pipeline proposta --id 1 --pacote Growth --valor 990` | Registrar proposta |
| `crm-pipeline today` | Follow-ups dos próximos 3 dias |
| `crm-pipeline metrics` | Métricas do pipeline |

## Estágios

`lead` → `qualificado` → `proposta` → `negociacao` → `fechado` | `perdido`

## Pacotes

- **Starter** R$350 — 1 collab, 1 perfil
- **Growth** R$990/mês — 3 collabs, 3 páginas + SEOgram
- **Premium** R$1.200 — 4 collabs + 3 stories, 3+ perfis

## Output

JSON padronizado com `status`, `next_action` e dados do lead.

## DB

`~/JARVIS_OS/01_MEMORY/crm_pipeline.db` — SQLite local, zero dependências.

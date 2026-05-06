---
name: revenue-tracker
description: "Receitas e custos da operação Instagram por mês"
sector: financeiro_metricas
model: haiku
cost_estimate: "$0.00/run (sqlite local)"
status: active
trigger: manual
---

# Revenue Tracker

Registro de receitas (collabs por pacote) e custos operacionais.

## Modos

| Comando | Descrição |
|---|---|
| `revenue-tracker add --cliente "Hotel X" --pacote Growth --mes 2026-04` | Receber collab |
| `revenue-tracker list` | Listar todas receitas |
| `revenue-tracker resumo` | Resumo por mês (receita - custo = lucro) |
| `revenue-tracker custo --descricao "Canva Pro" --valor 45 --mes 2026-04 --recorrente` | Registrar custo |

## Pacotes

Starter R$350 | Growth R$990 | Premium R$1.200

## DB

`~/JARVIS_OS/01_MEMORY/revenue.db` — SQLite local.

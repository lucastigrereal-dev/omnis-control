# OMNIS Próximo Roadmap — P5+

**Data:** 2026-05-09 | **Base:** P4 completo, ~1513 testes

> P4.0–P4.4 ENTREGUES: Mission Orchestrator, Sector Registry, Skill Matcher, Capability Gap Detector, Approval Center Local.
> Roadmap abaixo reflete P5+.

## P4.0 — Mission Status Dashboard

**Objetivo:** Visão unificada do estado de todas as missões ativas.

- CLI: `mission dashboard` — lista missões com status, asset, report
- Combina: mission_packages/ + asset_inbox_registry.jsonl + mission_reports.jsonl
- Output: tabela Rich com colunas: mission_id | intent | account | asset_assigned | outcome
- Testes: 15 mínimo
- **Sem LangGraph. Sem CrewAI. Sem rede.**

## P4.1 — Asset Inbox → Queue Bridge

**Objetivo:** Fluxo direto de asset importado para queue slot com verificação de formato.

- CLI: `asset-inbox assign <id> --queue <queue_id>` já existe
- Adicionar: validação de formato (jpg/png → image, mp4/mov → video) ao criar VideoAsset
- Adicionar: `asset-inbox bridge --date <YYYY-MM-DD>` — atribui asset a slot livre do dia
- Testes: 12 mínimo

## P4.2 — Mission Package Validator

**Objetivo:** Validate completude e qualidade de um mission package.

- CLI: `mission validate <mission_id>` — score 0–100
- Checks: arquivos obrigatórios, asset_reference.json, manifest campos, sem placeholders
- Output JSON com score + blockers + warnings
- Testes: 15 mínimo

## P4.3 — Delivery Zip Builder

**Objetivo:** Criar zip de entrega de mission package pronto para compartilhar.

- CLI: `mission zip <mission_id>` → `exports/zips/<mission_id>.zip`
- Inclui: todos os arquivos do pacote exceto artefatos de teste
- Gitignored: `exports/zips/`
- Testes: 10 mínimo

## P4.4 — Mission Summary HTML Render

**Objetivo:** Render HTML legível do mission brief para revisão offline.

- CLI: `mission render <mission_id>` → `exports/renders/<mission_id>.html`
- Template minimalista, sem JS externo, sem CDN
- Inclui: brief + plano + asset info + checklist
- Gitignored: `exports/renders/`
- Testes: 10 mínimo

## P4.5 — Multi-Mission Batch Runner

**Objetivo:** Criar múltiplas missões em batch a partir de CSV.

- CLI: `mission batch <csv_path>` — colunas: request_text, account_handle, objective
- Relatório de batch: quantas criadas, erros, IDs
- Testes: 12 mínimo
- **Sem LangGraph. Sem CrewAI. Sem rede.**

---

## Não Implementar Nesta Fase

- LangGraph
- CrewAI
- Meta API / Instagram
- OAuth
- Qualquer chamada de rede

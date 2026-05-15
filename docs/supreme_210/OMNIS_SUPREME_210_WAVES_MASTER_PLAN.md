# OMNIS SUPREME 210 WAVES — Master Plan

**Date:** 2026-05-15
**Version:** 1.0

---

## Visao

OMNIS Supreme e um sistema operacional agentivo local-first que executa missoes de conteudo ponta a ponta: intake → contexto → planejamento → squad → skills → execucao dry-run → artefatos → aprovacao → logs → aprendizado → entrega.

As 210 waves constroem esse sistema em camadas, cada wave adicionando capacidade real atras de gates de seguranca.

## Principios arquiteturais

1. **Local-first** — Tudo roda local antes de integracao externa
2. **Dry-run default** — `dry_run=True` universal, sem excecao
3. **Mock-first** — Adapters mock antes de reais
4. **Feature flag** — Toda integracao real atras de flag desligavel
5. **Approval gate** — Acao externa requer aprovacao humana
6. **Observability first** — Metricas antes de autonomia
7. **Akasha foundation** — Memoria solida antes de canais externos
8. **Contract before runtime** — Interface antes de implementacao
9. **Test before merge** — Suite verde entre waves
10. **Report before next** — Handoff documentado antes de avancar

## Estrutura de camadas

```
CAMADA 6 — Supreme RC           (W201-W210)  Release Candidate final
CAMADA 5 — Real Missions         (W191-W200)  Missoes controladas
CAMADA 4 — Production Hardening  (W181-W190)  Timeouts, retries, profiling
CAMADA 3 — External Bridges      (W151-W180)  MCP, Remote Control, KRATOS
CAMADA 2 — Domain Services       (W081-W150)  Publisher, Content, Video, Sales, App, Auto
CAMADA 1 — Core Runtime          (W011-W080)  Mission, Memory, Obs, Skills, Forge, Squad, Graph
CAMADA 0 — Foundation            (W001-W010)  Merge, Baseline, Governance
```

## Sequencia de construcao

```
W001-W010  : Foundation — merge, audit, scaffold
W011-W020  : Mission OS — contracts, packages, states
W021-W030  : Memory/Akasha — real sink behind flag
W031-W040  : Observability — logs, traces, metrics
W041-W050  : Skill Execution — runtime, gates, sandbox
W051-W060  : Capability Forge — gap detect, build, test
W061-W070  : Squad Composer — role registry, squad assembly
W071-W080  : Execution Graph — nodes, edges, retries, rollback
W081-W090  : Publisher/ARGOS — content pipeline
W091-W100  : Content Factory — Instagram, SEOgram, calendar
W101-W110  : Video Studio — ingest, transcribe, cuts
W111-W120  : Sales/CRM — DMs, pipeline, leads
W121-W130  : Commercial/SDR — hotel prospecting
W131-W140  : App Factory — PRD, schema, API, frontend
W141-W150  : Automation/n8n — workflows as tools
W151-W160  : MCP/Plugin — real MCP bridge
W161-W170  : Remote Control — Telegram/WhatsApp
W171-W180  : KRATOS Bridge — cockpit payloads
W181-W190  : Production Hardening — timeouts, retries, profiles
W191-W200  : First Real Missions — controlled pilots
W201-W210  : Supreme RC — release candidate
```

## Cada wave = 10 blocos

```
B1 — Model/contract definition
B2 — Core logic/service
B3 — Permission/security gate
B4 — Dry-run executor or mock adapter
B5 — CLI command (if applicable)
B6 — Event/audit logging
B7 — Integration/smoke tests
B8 — Documentation
B9 — Edge cases and hardening
B10 — Wave validation, report, and commit
```

## Gates de transicao

Entre cada wave:
1. Todos os 10 blocos PASS ou PASS_WITH_NOTES
2. Targeted tests passam
3. Working tree limpo (apenas arquivos da wave)
4. Git commit feito com mensagem conventional
5. Relatorio da wave em `reports/`
6. Nenhum gate de seguranca violado

Entre cada grupo (a cada 10 waves):
1. Full suite passa (ou subset relevante)
2. Progress tracking atualizado
3. Review de seguranca do grupo
4. Decisao de continuar registrada

## Tracking

Progresso registrado em:
- `docs/supreme_210/OMNIS_SUPREME_210_WAVES_PROGRESS.md` — status visual
- `docs/supreme_210/progress/supreme_210_progress.jsonl` — maquina-readable
- Commits git com mensagens `feat(omnis): wave <N> <slug>`

# ARQUITETURA — OMNIS / omnis-control

## Arquitetura Atual (Fases 1+2C)

```
┌──────────────────────────────────────────────────────────────┐
│                    CLI (Typer)                                │
│       jarvis.py                      omnis.py                │
├──────────────┬──────────────┬───────────────────────────────┤
│  checkers/   │  runners/    │  reports/                     │
│  skills      │  skill_runner│  status_report               │
│  docker      │  (timeout)   │                               │
│  publisher   │              │  docs/                        │
│  memory      │              │  ESTADO_ATUAL                 │
│  obsidian    │              │  PROXIMOS_PASSOS              │
│  disk        │              │  ARQUITETURA                  │
│  video_pipeline│            │  CONTENT_QUEUE                │
│               │              │  CAPTION_APPROVAL             │
├──────────────┴──────────────┴───────────────────────────────┤
│  content_queue/        video_assets/         utils/         │
│  accounts.py (CRUD)    registry.py (JSONL)   logger         │
│  models.py (QueueItem) scanner.py (scan)     safe_paths     │
│  queue.py (generate)   models.py (VideoAsset)               │
│  caption_approval/                                          │
│  models.py / drafts.py / approvals.py / templates.py         │
├─────────────────────────────────────────────────────────────┤
│  data/                                                       │
│  accounts.jsonl     Contas Instagram                         │
│  video_assets.jsonl Assets de vídeo                          │
│  content_queue.jsonl  Grade editorial                        │
│  caption_drafts.jsonl Rascunhos de legenda                   │
│  approval_log.jsonl   Log de aprovações                     │
│  caption_templates.json Templates de legenda                 │
│  exports/             CSVs exportados                        │
├─────────────────────────────────────────────────────────────┤
│  logs/ missions.jsonl / tool_runs.jsonl                     │
└─────────────────────────────────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌──────────────────┐
│ .claude/    │ │ publisher-os│ │ Docker / Akasha   │
│ skills/     │ │ FastAPI     │ │ Qdrant / Obsidian │
│ registry/   │ │ porta 8000  │ │                   │
└─────────────┘ └─────────────┘ └──────────────────┘
```

## Arquitetura Futura (Planejada)

```
                         OMNIS
                           │
            ┌──────────────┼──────────────┐
            │              │              │
     Control Plane  Execution Plane  Memory Plane
     (CLI, logs,    (skills, crews,  (Akasha, Qdrant,
      approval gate) LangGraph)       Obsidian)
            │              │              │
            └──────────────┼──────────────┘
                           │
                    Publishing Plane
                    (ARGOS, Instagram,
                     agendamento)
                           │
                    Security Plane
                    (guardrails, OAuth,
                     approval gate)
                           │
                    Observability Plane
                    (métricas, logs,
                     diagnóstico)
```

## Decisões Arquiteturais

1. **Cabine mínima vital primeiro** — Não construir o que não é necessário para
   diagnosticar o ecossistema.

2. **Read-only em sistemas existentes** — As fases 1 e 2 não modificam nada fora de
   `~/omnis-control/`. Isso reduz risco a zero.

3. **Logs estruturados com session_id** — Prepara o terreno para LangGraph e
   rastreabilidade distribuída.

4. **Python puro, sem framework pesado** — Typer + Rich + httpx. Nada de
   Django, FastAPI ou dependências desnecessárias.

5. **Venv local** — Isolamento total, sem contaminação do sistema.

6. **JSONL como storage local** — Simples, versionável, sem dependência de banco.
   O(n) para menos de 3.000 itens é aceitável.

7. **Dois sources of truth** — `accounts.jsonl` é a fonte operacional canônica;
   `CLAUDE.md` é documentação/contexto humano.

8. **Content Queue é planejamento, não execução** — A fila organiza o que precisa
   ser produzido. Publisher OS continua sendo o motor de publicação real.

## Componentes

| Componente | Tecnologia | Função |
|-----------|-----------|--------|
| CLI | Typer | Interface de linha de comando |
| Checkers | Python puro | Verificam saúde dos componentes |
| Runner | subprocess | Executa skills com timeout |
| Logger | JSONL | Logs estruturados com session_id |
| Safe Paths | Python puro | Bloqueia path traversal |
| Reports | Markdown | Gera relatórios de estado |
| Video Assets (Fase 2A) | Python + JSONL | Registro de assets de vídeo com estados |
| Content Queue (Fase 2B) | Python + JSONL | Cadastro de contas + fila editorial |
| Account Registry (2B) | Python + JSONL | Cadastro de contas Instagram |
| Caption Draft (Fase 2C) | Python + JSONL | Rascunho de legendas com versionamento |
| Approval Gate (Fase 2C) | Python + JSONL | Aprovação/rejeição + log auditável |
| Template Library (Fase 2C) | Python + JSON | Templates de legenda por objetivo |

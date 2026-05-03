# OMNIS — Relatório Completo da Estrutura

**Gerado em:** 2026-05-02
**Propósito:** Cabine mínima de controle do ecossistema de conteúdo Instagram (6 perfis, 690K+ seguidores)
**Fases concluídas:** Fase 1, 1.1, 2A, 2B, 2C, 2D

---

## 1. Arquitetura Geral

```
┌──────────────────────────────────────────────────────────────────┐
│                        CLI (Typer)                                │
│              jarvis.py  /  omnis.py (mesmo CLI, 2 entry points)   │
├────────────────┬────────────────┬────────────────────────────────┤
│   Checkers     │    Runners     │         Reports                │
│  (7 módulos)   │  skill_runner  │    status_report.py           │
├────────────────┴────────────────┴────────────────────────────────┤
│              Módulos de Negócio (3 domínios)                      │
│                                                                   │
│  Video Assets     Content Queue      Caption Approval             │
│  (Fase 2A)        (Fase 2B)          (Fase 2C)                   │
│  ┌──────────┐    ┌────────────┐    ┌─────────────────┐           │
│  │registry  │    │accounts    │    │models.py        │           │
│  │scanner   │    │models      │    │drafts.py (CRUD) │           │
│  │queue     │    │queue       │    │approvals.py     │           │
│  │models    │    │            │    │templates.py     │           │
│  │status    │    │            │    │                 │           │
│  └──────────┘    └────────────┘    └─────────────────┘           │
├──────────────────────────────────────────────────────────────────┤
│  Utils                    │  Logs                                │
│  logger (JSONL)           │  missions.jsonl                      │
│  safe_paths               │  tool_runs.jsonl                     │
├──────────────────────────────────────────────────────────────────┤
│  data/ (armazenamento local JSONL)                               │
│  accounts  content_queue  caption_drafts  approval_log           │
│  caption_templates  video_assets(0)                              │
└──────────────────────────────────────────────────────────────────┘
```

### Princípios Arquiteturais

| Princípio | Descrição |
|-----------|-----------|
| **Cabine mínima vital** | Só o necessário para diagnosticar e controlar o ecossistema |
| **Read-only externo** | Nada fora de `~/omnis-control/` é modificado |
| **JSONL como storage** | Simples, versionável, sem dependência de banco |
| **Unidirecional** | `caption_approval → content_queue` (nunca o inverso) |
| **Autonomia no cercado** | Age dentro do projeto, não mexe no resto do sistema |

---

## 2. Árvore de Arquivos

```
omnis-control/
├── config/
│   └── paths.yaml                        # Caminhos e URLs do ecossistema
├── data/
│   ├── accounts.jsonl                    # 2 contas Instagram
│   ├── approval_log.jsonl                # 82 eventos de approval
│   ├── caption_drafts.jsonl              # 41 rascunhos de legenda
│   ├── caption_templates.json            # 6 templates
│   ├── content_queue.jsonl               # 42 itens na fila editorial
│   └── exports/
│       └── queue_export_20260502_193249.csv
├── docs/
│   ├── ARQUITETURA.md                    # Arquitetura atual e futura
│   ├── CAPTION_APPROVAL.md               # Documentação Fase 2C
│   ├── CONTENT_QUEUE.md                  # Documentação Fase 2B
│   ├── ESTADO_ATUAL_RESUMIDO.md          # Report snapshot
│   ├── PROXIMOS_PASSOS.md                # Roadmap
│   ├── RELATORIO_COMPLETO.md             # ← Este arquivo
│   └── VIDEO_ASSET_REGISTRY.md           # Documentação Fase 2A
├── logs/
│   ├── missions.jsonl                    # 386 missões registradas
│   └── tool_runs.jsonl                   # 18 execuções de ferramentas
├── scripts/                              # (vazio — scripts temporários limpos)
├── src/
│   ├── cli.py                            # CLI principal (1.599 linhas)
│   ├── caption_approval/                 # Fase 2C — Legendas + Approval
│   │   ├── __init__.py
│   │   ├── models.py                     # CaptionDraft, DraftStatus, ApprovalLogEntry
│   │   ├── drafts.py                     # DraftsManager (CRUD + versionamento)
│   │   ├── approvals.py                  # ApprovalGate (validate, approve, reject)
│   │   └── templates.py                  # TemplateLibrary (6 templates)
│   ├── checkers/                         # 7 checkers de diagnóstico
│   │   ├── disk_check.py                 # Espaço em disco
│   │   ├── docker_check.py               # Containers Docker
│   │   ├── memory_check.py               # Qdrant + Akasha
│   │   ├── obsidian_check.py             # Vault Obsidian
│   │   ├── publisher_check.py            # Publisher OS API
│   │   ├── skills_check.py               # Skills Claude
│   │   └── video_pipeline_check.py       # Pipeline de vídeo
│   ├── content_queue/                    # Fase 2B — Contas + Fila
│   │   ├── __init__.py
│   │   ├── accounts.py                   # AccountRegistry (CRUD contas)
│   │   ├── models.py                     # QueueItem, QueueStatus, Priority
│   │   └── queue.py                      # Queue (geração, assign, export)
│   ├── reports/
│   │   └── status_report.py              # Gera relatório Markdown
│   ├── runners/
│   │   └── skill_runner.py               # Executa skills com timeout
│   ├── utils/
│   │   ├── logger.py                     # Log estruturado JSONL
│   │   └── safe_paths.py                 # Bloqueio de path traversal
│   └── video_assets/                     # Fase 2A — Assets de vídeo
│       ├── __init__.py
│       ├── models.py                     # VideoAsset, AssetStatus
│       ├── queue.py                      # Fila de publicação
│       ├── registry.py                   # Registry CRUD
│       ├── scanner.py                    # Scanner de diretórios
│       └── status.py                     # AssetStatus enum
├── tests/
│   ├── test_caption_approval.py          # 49 testes
│   ├── test_cli.py                       # 7 testes
│   ├── test_content_queue.py             # 38 testes
│   ├── test_e2e.py                       # 26 testes E2E
│   ├── test_fase1_1.py                   # 10 testes
│   ├── test_safe_paths.py                # 12 testes
│   ├── test_skill_runner.py              # 6 testes
│   └── test_video_assets.py              # 53 testes
├── jarvis.py                             # Entry point (legado)
├── omnis.py                              # Entry point (principal)
├── pyproject.toml                        # Projeto Python
├── README.md                             # Documentação inicial
└── config/paths.yaml                     # Config centralizada
```

---

## 3. Métricas de Código

### 3.1. LOC por Módulo

| Domínio | Arquivos | LOC | % do src |
|---------|----------|-----|----------|
| **CLI** | `cli.py` | 1.599 | 33,5% |
| **Checkers** (7) | `checkers/` | 730 | 15,3% |
| **Caption Approval** (4) | `caption_approval/` | 743 | 15,6% |
| **Content Queue** (3) | `content_queue/` | 561 | 11,8% |
| **Video Assets** (5) | `video_assets/` | 541 | 11,3% |
| **Reports** (1) | `reports/` | 300 | 6,3% |
| **Utils** (2) | `utils/` | 160 | 3,4% |
| **Runners** (1) | `runners/` | 98 | 2,1% |
| **Entry points** (2) | `jarvis.py` + `omnis.py` | 53 | — |
| **Total src** | **29 arquivos** | **4.785** | **100%** |

### 3.2. Testes

| Suite | Testes | LOC | Cobertura |
|-------|--------|-----|-----------|
| Video Assets | 53 | 494 | CRUD, scan, estados, schedule, publish |
| Caption Approval | 49 | 464 | CRUD, submit, approve, reject, templates, stale, versionamento |
| Content Queue | 38 | 494 | CRUD, geração, assign, export, stats |
| E2E | 26 | 355 | Fluxos completos CLI |
| Safe Paths | 12 | 99 | Path traversal, segurança |
| Fase 1.1 | 10 | 127 | Diagnóstico adicional |
| CLI | 7 | 102 | Comandos básicos |
| Skill Runner | 6 | 125 | Execução com timeout |
| **Total** | **201** | **2.260** | **201/201 passing** |

### 3.3. Dados Armazenados

| Arquivo | Registros | Tamanho | Propósito |
|---------|-----------|---------|-----------|
| `missions.jsonl` | 386 | 81 KB | Log de todas as operações |
| `caption_drafts.jsonl` | 41 | 27 KB | Rascunhos de legenda |
| `content_queue.jsonl` | 42 | 14 KB | Fila editorial |
| `approval_log.jsonl` | 82 | 20 KB | Log de aprovações |
| `caption_templates.json` | 6 | 3 KB | Templates de legenda |
| `accounts.jsonl` | 2 | 1 KB | Contas Instagram |
| `tool_runs.jsonl` | 18 | 5 KB | Log de execuções |

---

## 4. Checkers — Diagnóstico do Ecossistema

| Checker | O que verifica | Como |
|---------|---------------|------|
| **disk** | Espaço em disco C: | `psutil` — crítico se <10% livre |
| **docker** | Containers rodando, unhealthy | `docker ps` via subprocess |
| **publisher** | Publisher OS na porta 8000 | `httpx` + `socket` |
| **memory** | Qdrant (6333) + Akasha (5432) | HTTP + `docker ps` |
| **obsidian** | Vault: path, .md count, pastas | `os.walk` |
| **skills** | Skills Claude: total, executáveis, órfãs | `os` + `yaml` |
| **video_pipeline** | Pipeline de vídeo: sinais, riscos | Multi-source scan |

### Status Atual (2026-05-02)

| Componente | Status | Detalhes |
|-----------|--------|----------|
| Disco | 🔴 **CRÍTICO** | 8,1% livre (74,8 GB de 924 GB) |
| Docker | 🟡 18 running, 2 unhealthy | `crm-tigre-backend`, `jarvis_frontend` |
| Publisher OS | ⚪ Porta 8000 aberta, sem resposta HTTP | API não respondeu |
| Qdrant | 🔴 Inacessível | Erro de conexão (WinError 10054) |
| Akasha | 🟢 Container healthy | pgvector/pg16 na 5432 |
| Obsidian | 🟢 7.833 arquivos .md | 15 pastas principais |
| Skills | 🟢 98 detectadas | 17 executáveis, 38 doc folder, 43 doc file |
| Video Pipeline | 🟢 Operational (high confidence) | 90 evidências, 0 assets no registro |
| Content Queue | 🟢 42 itens, 2 contas | 1 caption_ready, 41 needs_asset |
| Caption Approval | 🟢 41 drafts em needs_review | 0 stale, 82 eventos de log |

---

## 5. Módulos de Negócio

### 5.1. Video Asset Registry (Fase 2A)

**Propósito:** Rastreamento local de arquivos de vídeo.

| Comando | Função |
|---------|--------|
| `omnis video-assets scan` | Varre diretórios em busca de vídeos |
| `omnis video-assets list` | Lista assets com filtros |
| `omnis video-assets inbox` | Assets aguardando triagem |
| `omnis video-assets update` | Atualiza metadados |
| `omnis video-assets schedule` | Agenda para publicação |
| `omnis video-assets publish` | Marca como publicado |
| `omnis video-assets stats` | Estatísticas agregadas |
| `omnis video-assets export` | Exporta como CSV |

**Estados possíveis:** `inbox → ready → scheduled → published`

**Estado atual:** 0 assets registrados. Nenhum arquivo de vídeo encontrado nos diretórios de busca.

### 5.2. Content Queue (Fase 2B)

**Propósito:** Planejamento editorial — grade de conteúdo para contas Instagram.

| Comando | Função |
|---------|--------|
| `omnis queue generate --days N` | Gera fila para N dias |
| `omnis queue list` | Lista itens da fila |
| `omnis queue today` | Itens do dia |
| `omnis queue stats` | Estatísticas |
| `omnis queue assign` | Vincula asset a slot |
| `omnis queue export` | Exporta CSV |
| `omnis accounts add` | Cadastra conta |
| `omnis accounts list` | Lista contas |

**Pipeline de status:** `needs_asset → needs_caption → caption_ready → scheduled → published`

**Estado atual:**
- 2 contas: @lucastigrereal (high), @afamiliatigrereal (medium)
- 42 itens gerados (21 por conta, 7 dias, 3 slots/dia: 08:50, 17:50, 20:50)
- 1 `caption_ready`, 41 `needs_asset`

### 5.3. Caption Approval (Fase 2C)

**Propósito:** Rascunho e aprovação de legendas — controle de qualidade editorial.

| Comando | Função |
|---------|--------|
| `omnis captions create <queue_id>` | Cria rascunho (com `--template`) |
| `omnis captions list` | Lista rascunhos |
| `omnis captions show <id>` | Mostra detalhes |
| `omnis captions update <id>` | Atualiza (versionamento automático) |
| `omnis captions submit <id>` | Submete para revisão |
| `omnis captions export` | Exporta CSV |
| `omnis approvals pending` | Lista pendentes |
| `omnis approvals approve <id>` | Aprova (queue → caption_ready) |
| `omnis approvals reject <id>` | Rejeita (queue → needs_caption) |
| `omnis approvals log` | Log auditável |
| `omnis templates list` | Lista templates |

**Pipeline de status do draft:** `draft → needs_review → approved ✓ / rejected ✗ → revised`

**Pré-validação (approve):**
- **Bloqueia:** texto vazio, <10 caracteres, placeholders `[HOOK A REVISAR]` etc.
- **Warning:** <3 hashtags, CTA não definido

**Versionamento:**
- Create → v1
- Update com alteração de conteúdo → v+1
- Reject → não altera versão
- Update após rejected → revised, v+1, rejection_reason = null

**Estado atual:**
- 41 drafts criados com templates (Fase 2D), todos em `needs_review`
- 6 templates (alcance_reels, alcance_carousel, autoridade_feed, conversao_feed, relacionamento_stories, teste_flex)
- 82 eventos no approval log

---

## 6. CLI — Comandos Disponíveis (18)

```
omnis.py / jarvis.py (comandos idênticos)

Comandos de diagnóstico:
  status              Saúde geral do ecossistema
  skills              Lista skills detectadas
  skill-info          Detalhes de uma skill
  run-skill           Executa skill com timeout
  publisher-health    Publisher OS na porta 8000
  docker-status       Containers Docker (read-only)
  memory-status       Qdrant + Akasha
  obsidian-status     Vault Obsidian
  doctor              Diagnóstico completo em JSON
  report              Gera relatório Markdown
  video-status        Pipeline de vídeo

Comandos de operação:
  video-assets        Registro de assets de vídeo (8 subcomandos)
  accounts            Cadastro de contas (6 subcomandos)
  queue               Fila editorial (8 subcomandos)
  captions            Rascunhos de legenda (6 subcomandos)
  approvals           Gate de aprovação (4 subcomandos)
  templates           Templates de legenda (2 subcomandos)
```

---

## 7. Ecossistema Externo (não-modificado pelo OMNIS)

| Sistema | Localização | Função | Acesso |
|---------|-------------|--------|--------|
| **Publisher OS** | `~/publisher-os/` | Motor de publicação (CrewAI + 20 agentes) | Porta 8000 |
| **Akasha** | Docker (pgvector) | Memória de longo prazo, 20K+ docs | Porta 5432 |
| **Qdrant** | Docker | Search semântico, embeddings | Porta 6333 |
| **Obsidian** | `~/Desktop/.../ComandoCentral` | Knowledge base, 7.833 .md files | Local |
| **CRMs** | Docker (3 containers) | CRM Tigre (backend + frontend + redis) | Portas 3001/4000 |
| **Jarvis OS** | `~/JARVIS_OS/` | Claude Code skills e registries | Local |
| **Skills Claude** | `~/.claude/skills/` | 113 skills (17 executáveis) | Local |

### Skills Executáveis (17)

```
argos-bridge                create_instagram_carousel     jarvis-brain
create_30_day_calendar      create_sales_dm_sequence      jarvis-decide
crm-pipeline                export_content_batch_to_csv   jarvis-delegate
generate_seogram_caption    jarvis-guardrails             jarvis-memory-write
jarvis-morning              jarvis-router                 revenue-tracker
skill-creator               video_to_content
```

---

## 8. Docker — Containers (18 running, 2 unhealthy)

| Container | Status | Portas |
|-----------|--------|--------|
| publisher-core | Up 2 dias | :8000 |
| litellm | Up 5 dias | :4002 |
| n8n | Up 5 dias | :5678 |
| publish-worker | Up 8 dias | — |
| open-webui | Up 8 dias (healthy) | :3100 |
| redis (pub) | Up 8 dias | :6382 |
| qdrant | Up 8 dias | :6333-6334 |
| supabase-db | Up 8 dias | :5434 |
| minio | Up 8 dias (healthy) | :9000-9001 |
| akasha-postgres | Up 8 dias (healthy) | :5432 |
| **crm-tigre-backend** | **Up 8 dias (unhealthy)** | **:4000** |
| crm-tigre-frontend | Up 8 dias (healthy) | :3001 |
| crm-tigre-redis | Up 8 dias | :6380 |
| crm-tigre-postgres | Up 8 dias | :5433 |
| aurora_redis | Up 8 dias | :6381 |
| **jarvis_frontend** | **Up 8 dias (unhealthy)** | **:8080** |
| jarvis_executor_api | Up 8 dias (healthy) | :3000 |
| jarvis_postgres | Up 8 dias | — |

---

## 9. Testes — Detalhamento

```
201 passed in 31.54s

Suítes:
  test_video_assets.py      53 ✓  (CRUD, scan, estados, fila, segurança)
  test_caption_approval.py  49 ✓  (CRUD, submit, approve, reject, templates, stale)
  test_content_queue.py     38 ✓  (contas, geração, assign, stats, export)
  test_e2e.py               26 ✓  (fluxos completos CLI)
  test_safe_paths.py        12 ✓  (path traversal, segurança)
  test_fase1_1.py           10 ✓  (diagnóstico)
  test_cli.py                7 ✓  (comandos básicos)
  test_skill_runner.py       6 ✓  (execução com timeout)
```

### Categorias de Testes

| Categoria | Qtd | O que cobre |
|-----------|-----|-------------|
| CRUD (create/read/update/delete) | ~45 | Operações básicas de dados |
| Regras de negócio | ~35 | Validação, versionamento, transições |
| Approve/Reject | ~20 | Approval gate, pré-validação |
| Scan/Import | ~15 | Scanner de vídeo, dedup, dry-run |
| Geração de fila | ~12 | Geração de calendário, distribuição |
| Export/CSV | ~8 | Exportação de dados |
| Segurança | ~12 | Path traversal, read-only, isolamento |
| E2E | ~26 | Fluxos completos via CLI |
| Templates | ~10 | Renderização, match, fallback |
| Stale detection | ~5 | Detecção de drafts parados |

---

## 10. Segurança

| Mecanismo | Descrição |
|-----------|-----------|
| **Safe Paths** | Bloqueia path traversal em todos os comandos |
| **Read-only externo** | Nenhum comando modifica arquivos fora de `~/omnis-control/` |
| **Sem .env exposto** | Nenhuma variável de ambiente é lida ou exposta |
| **Sem API externa** | Nenhuma chamada a Instagram, Meta, ou APIs externas |
| **Sem modificação Docker** | Todos os checkers Docker são read-only |
| **Log auditável** | Approval log append-only com actor, timestamp, reason |
| **Dry-run em scan** | Scanner de vídeo tem modo dry-run padrão |

---

## 11. Riscos Ativos

| Risco | Severidade | Impacto | Ação necessária |
|-------|-----------|---------|-----------------|
| **Disco C: 8,1% livre** | 🔴 Crítico | Docker pode falhar, logs podem parar | Saneamento (Fase 5) |
| **2 containers unhealthy** | 🟡 Médio | crm-tigre-backend, jarvis_frontend | Diagnóstico e reparo |
| **0 video assets** | 🟡 Médio | Fila não avança para scheduled | Produzir ou baixar vídeos |
| **41 drafts pendentes** | 🟢 Leve | Precisam de revisão humana | Revisar e aprovar |
| **Qdrant inacessível** | 🟡 Médio | Search semântico offline | Verificar conexão |

---

## 12. Roadmap

| Fase | Status | Entrega |
|------|--------|---------|
| **Fase 1** — Cabine mínima | ✅ Concluída | CLI, 6 checkers, logs, reports |
| **Fase 1.1** — Diagnóstico+E2E | ✅ Concluída | Testes E2E, diagnóstico refinado |
| **Fase 2A** — Video Asset Registry | ✅ Concluída | CRUD, scan, estados, fila |
| **Fase 2B** — Content Queue | ✅ Concluída | Contas, fila, assign, export |
| **Fase 2C** — Caption+Approval | ✅ Concluída | Drafts, approval, templates |
| **Fase 2D** — Batch captions | ✅ Concluída | 41 drafts criados e submetidos |
| **Fase 3** — OAuth Meta | ⬅️ Próximo | Conectar Publisher OS |
| **Fase 4** — Memória conectada | ⏳ Pendente | Obsidian→Qdrant→Akasha |
| **Fase 5** — Saneamento Docker | ⏳ Pendente | Limpeza de disco/containers |
| **Fase 6** — Runtime Agentic | ⏳ Pendente | LangGraph, tool router |
| **Fase 7** — CrewAI Integration | ⏳ Pendente | Coordenação skills+crews |

---

## 13. Comandos Rápidos

```bash
# Diagnóstico
python omnis.py status                  # Status resumido
python omnis.py doctor                  # Diagnóstico JSON completo
python omnis.py report                  # Gera relatório Markdown

# Queue
python omnis.py queue stats             # Estatísticas da fila
python omnis.py queue today             # Itens do dia
python omnis.py queue list              # Todos os itens

# Captions
python omnis.py captions list           # Todos os drafts
python omnis.py approvals pending       # Pendentes de revisão
python omnis.py approvals log --limit 10  # Últimas aprovações
python omnis.py templates list          # Templates disponíveis

# Aprovar (fluxo completo)
python omnis.py approvals show <id>     # Ver draft
python omnis.py approvals approve <id>  # Aprovar
python omnis.py approvals reject <id> --reason "..."  # Rejeitar

# Docker
python omnis.py docker-status           # Containers
python omnis.py memory-status           # Qdrant + Akasha

# Testes
python -m pytest tests/ -q             # 201 testes em 32s
```

---

## 14. Resumo Numérico

| Métrica | Valor |
|---------|-------|
| Arquivos .py | 39 |
| LOC total | 7.045 |
| LOC src | 4.785 |
| LOC tests | 2.260 |
| Testes | 201 |
| Checkers | 7 |
| Comandos CLI | 18 |
| Contas Instagram | 2 |
| Itens na fila | 42 |
| Drafts de legenda | 41 |
| Templates | 6 |
| Eventos de approval | 82 |
| Skills Claude | 98 (17 executáveis) |
| Containers Docker | 18 running (2 unhealthy) |
| Arquivos Obsidian | 7.833 |
| Commits git | 56 |
| Missões registradas | 386 |

# ROADMAP EXECUTADO — Fases de Implementação (Ponta a Ponta)

> **Operador:** Lucas Tigre (Tigrão) — 100% solo  
> **Período:** Março — Maio 2026  
> **Stack:** Claude Code + Docker + Python + PostgreSQL + CrewAI + LiteLLM  
> **Propósito:** Um homem, uma máquina, um império de mídia — 2.32M seguidores, 6 perfis

---

## FASE 0 — SETUP DA INFRAESTRUTURA

### Objetivo
Estabilizar o ambiente local com Docker, bancos de dados e serviços core rodando 24/7.

### O que foi executado

- [x] **Docker Compose** — 18 containers configurados em 4 stacks
  - Publisher OS (8 containers): publisher-core, litellm, n8n, worker, redis, qdrant, supabase-db, minio
  - Akasha (1 container): akasha-postgres com pgvector
  - CRM Tigre (4 containers): backend, frontend, redis, postgres
  - Jarvis Executor (3 containers): executor API, frontend, postgres
  - Open WebUI (1 container): interface chat local
  - Aurora Redis (1 container): cache auxiliar

- [x] **Redes e Portas** — Mapeamento completo (17 portas)
  - Gateway central LiteLLM :4002
  - Banco vetorial Qdrant :6333
  - Automação n8n :5678
  - Storage MinIO :9000

- [x] **Akasha DB** — PostgreSQL + pgvector :5432
  - 9 domínios de conhecimento
  - Busca híbrida (pgvector + tsvector português)
  - Embeddings 768d (nomic-embed-text via Ollama)

- [x] **Biblioteca Sabedoria** — 376 livros processados
  - Análise Pareto de 12 partes por livro
  - 5.386 insights extraídos
  - Pipeline de inserção: `inserir_livro_v3.py --replace`

- [x] **Obsidian Vault** — 7.833 arquivos .md (2.8 GB)
  - Base de conhecimento interligada em grafo
  - Acessível via Jarvis-brain para contexto

### Arquivos criados
- `docker-compose.yml` em cada stack
- `config/paths.yaml` — configuração central de caminhos
- Scripts de inicialização (`start.sh`, `setup.sh`)

### Marcos (Commits)
- `97c31f3` — Repositório oficial criado
- `ee62903` — Renomeado para omnis-control
- `1ef4e02` — Estrutura inicial de diretórios

---

## FASE 1 — CABINE MÍNIMA VITAL (CLI)

### Objetivo
CLI funcional com 6 checkers de estado do sistema + 25 testes.

### O que foi executado

- [x] **CLI Principal** — `jarvis.py` e `omnis.py`
  - Comandos de diagnóstico
  - Verificação de saúde dos serviços
  - Scanner de disco READ-ONLY

- [x] **6 Checkers**
  1. Docker checker — containers rodando
  2. Disk checker — espaço em disco
  3. DB checker — conexão Akasha
  4. Skill checker — skills registradas
  5. Git checker — estado do repositório
  6. Network checker — portas acessíveis

- [x] **25 Testes** — Script de diagnóstico E2E
  - `diagnose_e2e.json`
  - `diagnose_omnis.json`

- [x] **Disk Audit READ-ONLY**
  - `scripts/disk_audit_readonly.py` — scanner usando `du` via bash
  - Varre 8 diretórios-alvo (omnis-control, publisher-os, JARVIS_OS, llm-router, etc.)
  - Detecta node_modules, arquivos grandes (>100MB), archives (.zip, .tar.gz)
  - Estima reclaimable do Docker (70+ GB safe)
  - NUNCA deleta, move ou modifica nada
  - Saída: `docs/disk_audit_report.json` + stdout legível

### Marcos
- `f36a292` — Cabine Mínima Vital (CLI + 6 checkers + 25 testes)

---

## FASE 2A — CREATIVE BRIEF

### Objetivo
Sistema de briefs criativos com dataclasses, JSONL persistence e validação de legenda.

### O que foi executado

- [x] **Modelo CreativeBrief** (dataclass)
  - 15 campos: creative_brief_id, queue_id, caption_draft_id, account_handle, format, objective, visual_direction, script, shot_list, design_notes, editing_notes, asset_requirements, tool_suggestions, status, warnings, timestamps
  - `__post_init__` com auto-timestamp
  - `to_dict()` / `from_dict()` para serialização

- [x] **CRUD de Briefs** — `briefs.py`
  - `create_brief()` — valida caption_draft_id, gera warnings
  - `list_briefs()` — com filtro opcional por status
  - `get_brief()` — por ID
  - `update_brief_status()` — draft → approved/rejected/in_production
  - `create_review()` — registro de revisão

- [x] **Validação de Legenda**
  - Warning automático se caption_draft não aprovado
  - Gate de aprovação antes de produção

- [x] **JSONL Persistence**
  - `data/creative_briefs.jsonl`
  - `data/creative_review_log.jsonl`
  - Append-only, seguro para crash

### Arquivos criados
- `src/creative_production/__init__.py`
- `src/creative_production/models.py`
- `src/creative_production/briefs.py`

### Testes
- `test_create_brief` — criação com warnings
- `test_list_briefs` — listagem com múltiplos briefs
- `test_get_brief` — busca por ID
- `test_update_brief_status` — transição de status
- `test_model_creative_brief_defaults` — defaults corretos

---

## FASE 2B — PRODUCTION QUEUE

### Objetivo
Fila de produção com itens, assets e estatísticas.

### O que foi executado

- [x] **Modelo ProductionItem** (dataclass)
  - 11 campos: production_id, queue_id, creative_brief_id, asset_type, tool_target, status, asset_path, asset_id, review_notes, timestamps

- [x] **CRUD da Fila** — `production_queue.py`
  - `create_production_item()` — cria item na fila
  - `list_production_items()` — lista com filtros
  - `update_item_status()` — pending → in_progress → done/failed
  - `attach_asset()` — vincula asset ao item (marca como done)
  - `get_queue_stats()` — total, pending, in_progress, done, failed

- [x] **JSONL Persistence**
  - `data/production_queue.jsonl`
  - Append-only

### Arquivos criados
- `src/creative_production/production_queue.py`

### Testes
- `test_create_production_item`
- `test_list_production_items`
- `test_attach_asset`
- `test_get_queue_stats`

---

## FASE 2C — CAPTION DRAFT + APPROVAL GATE

### Objetivo
Gate de aprovação de legendas + revisão criativa integrada.

### O que foi executado

- [x] **Review Module** — `review.py`
  - `approve_brief()` — aprova + atualiza status
  - `reject_brief()` — rejeita + feedback
  - `is_ready_for_argos()` — verifica se pronto para publicação
  - Valida: caption aprovado + brief aprovado

- [x] **Exporter** — `exporter.py`
  - `export_package()` — gera pacote de produção
  - Estrutura: brief.md, script.md, shot_list.md, production_checklist.md
  - Destino: `data/exports/{brief_id}/`

### Arquivos criados
- `src/creative_production/review.py`
- `src/creative_production/exporter.py`

### Testes
- `test_review_approve` / `test_review_reject`
- `test_approve_nonexistent_brief` — edge case
- `test_is_ready_for_argos` — not approved / nonexistent
- `test_export_package` — pacote completo com 4 arquivos
- `test_export_package_invalid_brief` — edge case
- `test_list_packages_empty`

---

## FASE 2D — ARGOS DRAFT BRIDGE

### Objetivo
Ponte de publicação que prepara conteúdo pronto para o Instagram.

### O que foi executado

- [x] **Argos Bridge Skill**
  - `skills/argos-bridge/` — skill completa
  - Prepara pacote de publicação (legenda + asset + metadados)
  - Gate de qualidade antes de enviar
  - Pronto, aguardando OAuth Meta para postar

- [x] **Pipeline Ponta a Ponta** (documentado)
  - `docs/WORKFLOW_PONTA_A_PONTA.md`
  - Queue → Caption Draft → Creative Brief → Production → Review → Export → Argos

### Marcos
- `96e9714` — Fase 2E — Argos Draft Bridge completa

---

## FASE S0 — ENTERPRISE SECTOR BLUEPRINT

### Objetivo
Definir os 7 setores de negócio e reconciliar todo o ecossistema.

### O que foi executado

- [x] **7 Setores Definidos** — `registry/sectors.yaml`
  1. Mídia & Conteúdo
  2. Comercial / SDR Hotéis
  3. Vendas & CRM
  4. Conhecimento & Inteligência
  5. Produto & Tecnologia
  6. Financeiro & Métricas
  7. Operações & Organização

- [x] **Documentos**
  - `docs/ENTERPRISE_SECTORS.md` — especificação completa
  - `docs/SECTORS_RECONCILIATION.md` — reconciliação com assets existentes

### Marcos
- `2bb2bb7` — Fase S0 — Enterprise Sector Blueprint completo

---

## FASE 3A — AUTOMATION & INTEGRATION REGISTRY

### Objetivo
Registro de automações n8n + cliente de integração + schemas de manifesto.

### O que foi executado

- [x] **n8n Client** — `src/integrations/n8n_client.py`
  - Cliente HTTP para API do n8n
  - Criar, listar, executar workflows
  - Testes unitários com mock

- [x] **Schema de Manifesto** — `schemas/manifest.schema.json`
  - Validação de manifestos de skill
  - Campos obrigatórios: name, version, description, sector, entry

- [x] **Workflows n8n Exportados** — `workflows/n8n/`
  - Workflows de automação versionados no Git

- [x] **Testes de Integração**
  - `tests/integrations/test_n8n_client.py`
  - `tests/integrations/__init__.py`

### Marcos
- `4628e22` — Fase 3A — Automation & Integration Registry

---

## FASE CONSOLIDAÇÃO — RUNBOOKS + DECISÕES

### Objetivo
Documentar decisões irreversíveis, runbooks de recuperação e protocolo de execução.

### O que foi executado

- [x] **3 Decisões Irreversíveis**
  - D1: Claude Code Nativo (orquestrador = CLI, não framework)
  - D2: 7 Setores (domínios de negócio isolados)
  - D3: Auditoria First (nunca executar sem confirmação)

- [x] **Protocolo 15-15-20**
  - 15 min planejamento → 15 min execução → 20 min documentação
  - Ciclo de micro-entrega para TDAH

- [x] **Runbooks**
  - `docs/QDRANT_RECOVERY_RUNBOOK.md`
  - `docs/META_OAUTH_RUNBOOK.md`
  - `docs/LEGACY_CONTAINERS.md`

- [x] **Superprompts**
  - `docs/SUPERPROMPT_MISSAO_COMPLETA.md`
  - `docs/SUPERPROMPT_v2_CIRURGICO.md`

### Marcos
- `99c76c3` — Decisões, runbooks, protocolo 15-15-20 e scan-default

---

## FASE ECOSYSTEM — M1 a M6

### Objetivo
Estruturação completa do ecossistema OMNIS em 6 marcos.

### O que foi executado

- [x] **M1: Fundação** — Repositório, Docker, configs
- [x] **M2: Módulo Criativo** — Creative Production OS completo
- [x] **M3: Skills Core** — 7 skills (router, brain, delegate, guardrails, decide, memory-write, morning)
- [x] **M4: Registros** — 7 arquivos YAML de configuração central
- [x] **M5: Testes** — 311 testes, suite completa
- [x] **M6: Documentação** — 40+ documentos em docs/

### Marcos
- `5b0dbd3` — M1-M6 estruturação completa do ecossistema
- `9f78877` — Pipeline ponta a ponta IDEA → PRODUCE → DRAFT

---

## FASE G1 — EXECUÇÃO SEQUENCIAL COMPLETA

### Objetivo
Executar todas as fases anteriores em sequência, validando cada uma antes de avançar.

### O que foi executado

- [x] **G1 Preflight** — `docs/G1_PREFLIGHT_PLAN.md`
  - Verificação pré-execução
  - Dependências entre fases
  - Rollback plan

- [x] **Execução Completa**
  - Fase 0 ✅ → Fase 1 ✅ → Fase 2A ✅ → Fase 2B ✅ → Fase 2C ✅ → Fase 2D ✅
  - Fase S0 ✅ → Fase 3A ✅ → Consolidação ✅

- [x] **Relatório de Execução**
  - `docs/RELATORIO_EXECUCAO_SEQUENCIAL_OMNIS.md`

### Marcos
- `0663988` — Complete sequential execution — G1, Fase 0, Fase 1, Fase 2

---

## FASE B — 17 SKILLS + REGISTRY + TESTES

### Objetivo
Criar 17 skills completas (run.py + SKILL.md + manifest.json), 7 registros YAML e bateria de 24 testes.

### O que foi executado

- [x] **7 Skills Core**
  1. `jarvis-router` — classifica intenção em 7 setores (89 LOC)
  2. `jarvis-brain` — contexto multi-fonte (154 LOC)
  3. `jarvis-delegate` — roteia para skill (96 LOC)
  4. `jarvis-guardrails` — 18 regras de segurança (112 LOC)
  5. `jarvis-decide` — Decision Engine com fórmula (84 LOC)
  6. `jarvis-memory-write` — persiste em Akasha + Git (131 LOC)
  7. `jarvis-morning` — briefing matinal (78 LOC)

- [x] **9 Skills Setoriais**
  1. `generate_seogram_caption` — legendas SEO
  2. `create_instagram_carousel` — carrosséis
  3. `create_30_day_content_calendar` — calendário mensal
  4. `video_to_content` — vídeo → conteúdo
  5. `crm-pipeline` — pipeline de vendas
  6. `revenue-tracker` — receita
  7. `argos-bridge` — ponte de publicação
  8. `create_sales_dm_sequence` — DMs de venda
  9. `export_content_batch_to_csv` — exportação lote

- [x] **1 Skill Meta**
  - `skill-creator` — cria skills no padrão (269 LOC)

- [x] **7 Registros YAML**
  - `sectors.yaml`, `skills.yaml`, `agents.yaml`, `workflows.yaml`
  - `decision_engine.yaml`, `guardrails.yaml`, `models.yaml`

- [x] **24 Testes Core** — `tests/test_skills_core.py`
  - Frontmatter, sintaxe, registro, imports

- [x] **Skill Runner** — `src/runners/skill_runner.py`
  - Engine de execução com path configurável via env
  - Validação via `safe_paths.py`

### Marcos
- `1b8024a` — Security: .claude isolation
- `f0a5e49` — Hooks de segurança + fix git root
- `3ab9792` — 4 skills core (merge/promove/cria) + padronização YAML
- `5564c7f` — Relatório completo da estrutura — 14 seções, 201 testes
- `d5f5d2f` — Recovery + 17 skills run.py + 311 testes

---

## FASE RECOVERY — PÓS-CRASH CLAUDE CODE

### Objetivo
Recuperar módulo Creative Production + Disk Audit de um git stash após crash do Claude Code.

### O que foi executado

- [x] **Diagnóstico** — Identificar 3 testes falhando de 304
- [x] **Branch Recovery** — `recovery/stash-fase1-creative-production`
- [x] **6 Correções**
  1. `caption_draft_id: Optional[str] = None` — dataclass fix
  2. Fixture movida: `data/briefs/` → `tests/fixtures/creative_production/`
  3. `_gen_manifests.py` arquivado em `scripts/archive/`
  4. `config/paths.yaml` atualizado: `~/omnis-control/skills`
  5. `skill_runner.py` + `safe_paths.py`: path configurável via `OMNIS_SKILLS_PATH`
  6. `test_safe_paths.py`: lista skills do projeto
- [x] **311/311 Testes Passando**
- [x] **17 Skills com run.py + SKILL.md + manifest.json**
- [x] **Documentos de Recovery**
  - `docs/recovery/CONFLICTS_CREATIVE_PRODUCTION_RECOVERY.md`
  - `docs/recovery/RELATORIO_RECOVERY_CREATIVE_PRODUCTION_FINAL.md`
- [x] **Relatório Supremo** — `docs/OMNIS_SUPREME_REPORT.md` (1.019 linhas)

### Marcos
- `d5f5d2f` — Recovery complete
- `d2d103c` — Supreme report

---

## PUBLISHER OS — FÁBRICA DE CONTEÚDO

### Objetivo
Sistema autônomo de produção de conteúdo com 20 agentes CrewAI, fila inteligente, scheduler e SDR.

### O que foi executado

- [x] **8 Containers Docker**
  - publisher-core (:8000), litellm (:4002), n8n (:5678), worker, redis (:6382), qdrant (:6333), supabase-db (:5434), minio (:9000)

- [x] **Core Engine**
  - `core/queue/post_scheduler.py` — scheduler com jitter ±20min, bloqueio noturno, 2h/perfil
  - `core/gateway/config.yaml` — caption-fast via Gemini 2.5 Flash
  - `core/policy_engine_v2.py` — engine de políticas v2
  - `core/state_machine/` — máquina de estados

- [x] **20 Agentes CrewAI** (5 crews)
  - Content Production (8 agentes): Strategy, SEO, Copywriter, Visual, Brand, Engagement, Editor, Quality
  - SDR & Sales (3 agentes): Lead Qualifier, Pitch Generator, Follow-up Manager
  - Research & Trends (4 agentes): Trend Analyzer, Competitor Monitor, Audience Insight, Content Researcher
  - Analytics (3 agentes): Performance Analyst, Report Generator, Optimization Advisor
  - Learning & Memory (2 agentes): Memory Curator, Pattern Detector

- [x] **SDR Qualifier v2** — `intelligence/sdr/qualifier_v2.py`
  - PydanticAI + Akasha + Claude Haiku
  - Schema: HotelLead (hotel_name, contact, segment, estimated_value, priority, reason)

- [x] **MCP Server** — `mcp_server.py`
  - 12 ferramentas expostas via Model Context Protocol
  - produce_content, run_crew, check_job, get_briefing, get_trends, evaluate_content, etc.

- [x] **Memória** — `intelligence/memory/mem0_graph_config.py`
  - Kuzu graph + LiteLLM local-fast
  - Embeddings 768d (nomic-embed-text)

- [x] **Testes** — 31 pytest + 10 testes integrados (Sprint 2 ABA5)

### Marcos (Git)
- `133405d` — JARVIS-v4-completo
- `15d1a95` — fix-all-bugs-130-tests
- `951d491` — Eliminar openai/local-fast model errors
- `ec533fc` — Integrate ARGOS publishing flow foundation
- `f36b553` — Add ARGOS metrics sync foundation

---

## BIBLIOTECA SABEDORIA — 376 LIVROS

### Objetivo
Processar 376 livros de alta performance com análise Pareto e armazenar no PostgreSQL.

### O que foi executado

- [x] **376 Livros Processados** — V3 com 12 partes cada
  - Capítulos detalhados
  - Histórias reais
  - Experimentos baseados em dados
  - Analogias e metáforas
  - Exemplos práticos
  - 10 perguntas por livro com respostas
  - Insights acionáveis (~5.386 total)

- [x] **Pipeline de Inserção**
  - `inserir_livro_v3.py --replace` — insere/substitui no PostgreSQL
  - JSONs em `extraidos/` — versionados
  - Validação: `check_estado.py`, `monitor_projeto.py`

- [x] **Dashboard** — `dashboard/` com relatórios de progresso
- [x] **Mapas Mentais** — `mapas/` com visualizações

### Marcos (Git)
- 57 commits total
- Missão V3: 376/376 livros (100% concluída)

---

## INFRAESTRUTURA — 18 CONTAINERS (ESTADO ATUAL)

### Objetivo
Manter 18 containers rodando 24/7 com saúde monitorada.

### Estado Atual (2026-05-06)

```
PUBLISHER OS (8) — TODOS SAUDÁVEIS
├── publisher-core        :8000   ✅ Up 6 dias
├── litellm               :4002   ✅ Up 8 dias
├── n8n                   :5678   ✅ Up 8 dias
├── publish-worker                ✅ Up 12 dias
├── redis                 :6382   ✅ Up 12 dias
├── qdrant              :6333-34  ✅ Up 12 dias
├── supabase-db           :5434   ✅ Up 12 dias
└── minio              :9000-01   ✅ Up 12 dias

AKASHA (1) — SAUDÁVEL
├── akasha-postgres       :5432   ✅ Up 12 dias

OPEN WEBUI (1) — SAUDÁVEL
├── open-webui            :3100   ✅ Up 12 dias

CRM TIGRE (4) — 1 UNHEALTHY (NÃO CRÍTICO)
├── crm-tigre-backend     :4000   ⚠️ Up 12 dias (UNHEALTHY)
├── crm-tigre-frontend    :3001   ✅ Up 12 dias
├── crm-tigre-redis       :6380   ✅ Up 12 dias
├── crm-tigre-postgres    :5433   ✅ Up 12 dias

JARVIS (3) — 1 UNHEALTHY (NÃO CRÍTICO)
├── jarvis_frontend       :8080   ⚠️ Up 12 dias (UNHEALTHY)
├── jarvis_executor_api   :3000   ✅ Up 12 dias
├── jarvis_postgres               ✅ Up 12 dias

AURORA (1) — SAUDÁVEL
└── aurora_redis          :6381   ✅ Up 12 dias
```

---

## MÉTRICAS GLOBAIS DO ECOSSISTEMA

| Categoria | Total |
|-----------|-------|
| Containers Docker | 18 (16 saudáveis) |
| Bancos de Dados | 5 |
| Modelos de IA | 8 (4 cloud + 4 locais) |
| Skills (OMNIS) | 17 |
| Skills (.claude) | 35+ |
| **Total Skills** | **52** |
| Linhas Python (OMNIS) | 14.052 |
| Testes Automatizados | 311 |
| Documentos (Akasha) | 20.262 |
| Chunks Vetorizados | 606.602 |
| Livros (Biblioteca) | 376 |
| Insights Extraídos | ~5.386 |
| Arquivos Obsidian | 7.833 (2.8 GB) |
| Agentes CrewAI | 20 |
| Ferramentas MCP | 12 |
| Commits (OMNIS) | 14 |
| Commits (Publisher OS) | 9+ |
| Commits (Biblioteca) | 57 |
| Documentos de Doc | 40+ |
| Seguidores Instagram | 2.320.000+ |
| Perfis | 6 |

---

## PRÓXIMOS PASSOS (NÃO EXECUTADOS)

| Prioridade | Fase | Descrição | Status |
|-----------|------|-----------|--------|
| 🔴 P0 | Conectar OAuth Meta | 6 contas Instagram → postagem real | Pendente |
| 🔴 P0 | Ativar Argos | Gate de publicação real | Pendente |
| 🟡 P1 | Pipeline 150 Influenciadores | Interior SP — prospecção em massa | Pendente |
| 🟡 P1 | Dashboard Financeiro | Receita × métricas em tempo real | Pendente |
| 🟢 P2 | Fix Containers Unhealthy | CRM backend + Jarvis frontend | Pendente |
| 🟢 P3 | Mobile App | Acompanhamento do celular | Pendente |

---

*Documento gerado em 2026-05-06 para exportação ao Notion.*  
*OMNIS — Do latim "omnis" = "tudo", "cada", "todo".*  
*"O que gera dinheiro hoje?" — A pergunta guia.*

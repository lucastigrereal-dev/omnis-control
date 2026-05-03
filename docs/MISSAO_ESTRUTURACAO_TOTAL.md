# MISSAO ESTRUTURACAO TOTAL — OMNIS ECOSYSTEM
# Data: 2026-05-03 | Modelo: Sonnet 4.6
# Estado: 227 testes, cockpit OK, 40 drafts needs_review
# D003/D006/D007/D008 absolutas. pytest antes de commitar.

## CONTEXTO — NAO RECONSTRUIR

# OMNIS ~/omnis-control/ — 227 testes, cockpit funcionando
# Setores operational: marketing_enterprise, memory_knowledge, security_audit, mission_control
# Setores blueprint: sales_revenue, app_factory, automation_integrations, finance_capital, runtime_agentic
# Skills com run.py (17): jarvis-router, jarvis-brain, jarvis-delegate, jarvis-decide,
#   jarvis-guardrails, jarvis-memory-write, jarvis-morning, argos-bridge,
#   generate_seogram_caption, create_30_day_content_calendar, create_instagram_carousel,
#   create_sales_dm_sequence, export_content_batch_to_csv, video_to_content,
#   crm-pipeline, revenue-tracker, skill-creator
# Publisher-OS: FastAPI :8000, 8 containers UP, MCP 12 tools, SocialAccount 0 rows
# Daily-Prophet: ~/daily-prophet-hotels — Next.js SDR hoteis, .env.local existe
# LLM-Router: ~/llm-router/ — hub_social.py, task_router.py, config.yaml
# Akasha: PostgreSQL :5432, 11 tabelas com dados reais
# Qdrant: :6333 UP, sem colecoes configuradas

## SEQUENCIA (executar nessa ordem, OAuth por ultimo)

# M1 → Setores blueprint → partial (sectors.yaml + sectors_check.py)
# M2 → Skill Runner (invocar .claude/skills sem modificar)
# M3 → LLM Router bridge (ler ~/llm-router/config.yaml)
# M4 → Daily Prophet checker (setor sales_revenue)
# M5 → Akasha Reader (memoria real)
# M6 → Qdrant Indexer (criar colecoes, indexar drafts)
# M7 → [POR ULTIMO, SO COM AUTORIZACAO] META OAuth

## M1 — SETORES BLUEPRINT PARCIAL (20 min)

# Editar config/sectors.yaml
# Para cada setor blueprint, adicionar:
#   status: "partial"
#   available_skills: [skills ja existentes mapeadas abaixo]
#   next_action: "1 frase do que falta"
#
# Mapeamento:
# sales_revenue:         create_sales_dm_sequence, crm-pipeline, revenue-tracker,
#                        hotel-lead-scorer(md), lead-qualifier(md), follow-up-generator(md)
# app_factory:           skill-creator, subagent-driven-development(md)
# automation_integrations: llm-router (~/llm-router/), setup_n8n_triggers(publisher-os)
# finance_capital:       revenue-tracker, roi-calculator(md), revenue.db
# runtime_agentic:       jarvis-router, jarvis-decide, jarvis-delegate

# CRIAR: src/checkers/sectors_check.py
# Le sectors.yaml e retorna dict {setor_id: status}
# Nunca inventa logica — apenas le config

# CLI:
#   omnis sectors           listar setores com status
#   omnis sectors --json    output JSON

# Teste: test_sectors_check.py
#   todos os 9 setores aparecem no output
#   status e string valida: operational/partial/blueprint

## M2 — SKILL RUNNER (25 min)

# CRIAR: src/skills/skill_runner.py

# SKILLS_PATH = Path.home() / ".claude" / "skills"
#
# def list_skills() -> list[dict]:
#     retorna [{name, path}] para cada skill com run.py
#
# def run_skill(name: str, args: list = None) -> dict:
#     subprocess.run com timeout=60
#     retorna {stdout, stderr, returncode}
#     NUNCA lanca excecao — erro vai no dict

# CLI:
#   omnis skills list                         listar disponiveis
#   omnis skills run generate_seogram_caption executar skill
#   omnis skills run jarvis-morning           briefing Jarvis

# Teste: test_skill_runner.py
#   list_skills retorna >= 17 items
#   run_skill invalida retorna returncode=1 com stderr
#   run_skill com mock subprocess nao crasha

## M3 — LLM ROUTER BRIDGE (15 min)

# CRIAR: src/intelligence/llm_router_bridge.py
# Le ~/llm-router/config.yaml (read-only, nao modifica)
#
# def get_model_for_task(task_type: str) -> str:
#     le config.yaml, retorna modelo recomendado
#     ex: "caption" -> "claude-haiku-4-5"
#         "synthesis" -> "claude-sonnet-4-6"
#
# def list_models() -> dict:
#     retorna todo o config de modelos

# CLI:
#   omnis llm models          modelos configurados
#   omnis llm suggest caption qual modelo para caption

# Teste: test_llm_router_bridge.py
#   config_readable: config.yaml existe
#   get_model retorna string, nao crasha se arquivo ausente

## M4 — DAILY PROPHET CHECKER (15 min)

# CRIAR: src/checkers/daily_prophet_check.py
#
# def check_daily_prophet() -> dict:
#     root = Path.home() / "daily-prophet-hotels"
#     return {
#         "exists": root.exists(),
#         "has_env": (root / ".env.local").exists(),
#         "scripts": listagem de scripts/,
#         "sql_files": count de *.sql,
#         "status": "configured" se has_env else "missing_env"
#     }
#     NUNCA lanca excecao — retorna dict com error key se falhar

# Adicionar ao sectors.yaml em sales_revenue:
#   external_systems: [{name: daily-prophet-hotels, status: configured}]

# CLI:
#   omnis sales status   status setor + daily prophet

# Teste: test_daily_prophet_check.py
#   retorna dict com chaves esperadas
#   nao crasha se pasta ausente

## M5 — AKASHA READER (25 min)

# Verificar primeiro: pip show psycopg2-binary
# Se ausente: pip install psycopg2-binary

# CRIAR: src/memory/akasha_reader.py
# DSN = "postgresql://akasha:akasha123@localhost:5432/akasha"
# (senha local default, sem valor em prod)
#
# def ping() -> bool:
#     connect_timeout=3, retorna True/False
#
# def get_recent_memories(limit: int = 5) -> list[dict]:
#     SELECT content, created_at FROM memoria_global ORDER BY created_at DESC LIMIT N
#     retorna [{content, created_at}] ou [{error: msg}]
#
# def get_project_context(project_name: str) -> str | None:
#     busca em memoria_projetos por ILIKE

# CLI:
#   omnis memory recent          ultimas 5 memorias
#   omnis memory project omnis   contexto do projeto

# Adicionar ao briefing: se ping() False, adicionar "Akasha offline" nas acoes

# Teste: test_akasha_reader.py
#   ping retorna bool, nao excecao
#   get_recent handles offline (mock psycopg2)

## M6 — QDRANT INDEXER (20 min)

# Verificar: pip show qdrant-client sentence-transformers
# Se ausentes: pip install qdrant-client sentence-transformers

# CRIAR: src/memory/qdrant_indexer.py
# COLLECTION = "omnis_drafts"
# VECTOR_SIZE = 384 (all-MiniLM-L6-v2)
#
# def get_status() -> dict:
#     tenta conectar :6333, retorna colecoes e contagem
#     retorna {available: False} se offline
#
# def ensure_collection() -> bool:
#     cria "omnis_drafts" se nao existir
#
# def index_drafts(path: str = "data/caption_drafts.jsonl") -> dict:
#     le drafts, gera embeddings, indexa no Qdrant
#     fallback: se sentence-transformers ausente, usa hash simples como vetor
#     retorna {indexed: N, skipped: N, errors: []}

# CLI:
#   omnis memory qdrant status   colecoes + contagem
#   omnis memory qdrant index    indexa drafts (pede confirmacao)

# Teste: test_qdrant_indexer.py
#   get_status retorna dict com "available" key
#   nao crasha se Qdrant offline

## M7 — META OAUTH [SO COM AUTORIZACAO EXPLICITA DO LUCAS]

# NAO EXECUTAR AGORA
# O prompt de execucao esta em: docs/META_OAUTH_RUNBOOK.md
#
# Quando Lucas disser "pode rodar OAuth":
# 1. Lucas coloca META_APP_SECRET no publisher-os/.env (so ele)
# 2. python publisher-os/scripts/oauth_setup.py
# 3. Seguir URL no browser
# 4. Validar: GET http://localhost:8000/api/v1/accounts
# 5. Configurar 6 contas
# 6. Testar 1 post

## COMMIT FINAL (apos M1-M6)

# python -m pytest tests/ -q --tb=short
# Esperado: 250+ testes

# git add -A
# git commit -m "feat(ecosystem): M1-M6 estruturacao completa
#
# M1: sectors.yaml — 5 setores blueprint->partial com skills mapeadas
# M2: src/skills/skill_runner.py — invoca .claude/skills
# M3: src/intelligence/llm_router_bridge.py — le ~/llm-router/config.yaml
# M4: src/checkers/daily_prophet_check.py — SDR hotels
# M5: src/memory/akasha_reader.py — memoria real Akasha
# M6: src/memory/qdrant_indexer.py — colecoes e indexacao
# Tests: N passed
# Next: M7 META OAuth (aguardando autorizacao)"

## VERIFICACAO FINAL

# python omnis.py sectors              9 setores com status
# python omnis.py skills list          17+ skills disponiveis
# python omnis.py skills run jarvis-morning  executa skill real
# python omnis.py llm models           modelos configurados
# python omnis.py sales status         SDR + daily prophet
# python omnis.py memory recent        ultimas memorias Akasha
# python omnis.py memory qdrant status status colecoes
# python omnis.py briefing             health score completo
# python -m pytest tests/ -q          250+ verde

# NAO FAZER: HTTP externo, ler .env, tocar publisher-os/.claude/JARVIS_OS,
#            OAuth sem autorizacao, docker prune automatico.

# Bora.

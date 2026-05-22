# OMNIS INTEGRATION LOG

Iniciado: 05/22/2026 14:12:36

- [2026-05-22 14:12:36] [START] AUTORUN OPTIMIZED iniciado em C:\Users\lucas\omnis-control
- [2026-05-22 14:12:36] [GUARD] GUARDRAIL ativo: nao recomecar do zero, nao tocar KRATOS (somente leitura)
- [2026-05-22 14:12:37] [INFO] Estado git omnis-control: feature/omnis-5waves-runtime-supreme @ 5589a07
- [2026-05-22 14:12:37] [WARN] Working tree SUJA — commitar/stashar antes de mudancas estruturais
- [2026-05-22 14:12:37] [INFO] Python: Python 3.12.10
- [2026-05-22 14:12:37] [INFO] --- Inventario de portas (estado real) ---
- [2026-05-22 14:12:42] [INFO]   :5173 KRATOS Frontend -> DOWN
- [2026-05-22 14:12:42] [INFO]   :5432 PostgreSQL (Akasha - canonico) -> UP
- [2026-05-22 14:12:46] [INFO]   :6333 Qdrant -> DOWN
- [2026-05-22 14:12:46] [INFO]   :6381 Redis (canonico) -> UP
- [2026-05-22 14:12:50] [INFO]   :6382 Redis (Publisher OS) -> DOWN
- [2026-05-22 14:12:54] [INFO]   :8000 Publisher OS API -> DOWN
- [2026-05-22 14:12:54] [INFO]   :11434 Ollama -> UP
- [2026-05-22 14:12:54] [INFO] --- Containers Docker existentes ---
- [2026-05-22 14:12:54] [INFO]   publisher-os-publisher-core-1 | Exited (255) 2 weeks ago | 0.0.0.0:8000->8000/tcp
- [2026-05-22 14:12:54] [INFO]   publisher-os-litellm-1 | Exited (255) 2 weeks ago | 0.0.0.0:4002->4000/tcp
- [2026-05-22 14:12:54] [INFO]   publisher-os-n8n-1 | Exited (255) 2 weeks ago | 0.0.0.0:5678->5678/tcp
- [2026-05-22 14:12:54] [INFO]   publisher-os-supabase-db-1 | Exited (255) 2 weeks ago | 0.0.0.0:5434->5432/tcp
- [2026-05-22 14:12:54] [INFO]   publisher-os-redis-1 | Exited (255) 22 hours ago | 0.0.0.0:6382->6379/tcp
- [2026-05-22 14:12:54] [INFO]   publisher-os-qdrant-1 | Exited (255) 22 hours ago | 0.0.0.0:6333-6334->6333-6334/tcp
- [2026-05-22 14:12:54] [INFO]   publisher-os-publish-worker-1 | Up 22 hours | 
- [2026-05-22 14:12:54] [INFO]   open-webui | Up 22 hours (healthy) | 0.0.0.0:3100->8080/tcp, [::]:3100->8080/tcp
- [2026-05-22 14:12:54] [INFO]   akasha-postgres | Up 22 hours (healthy) | 0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp
- [2026-05-22 14:12:54] [INFO]   crm-tigre-backend | Up 22 hours (healthy) | 0.0.0.0:4000->4000/tcp, [::]:4000->4000/tcp
- [2026-05-22 14:12:54] [INFO]   crm-tigre-frontend | Up 22 hours (healthy) | 0.0.0.0:3001->80/tcp, [::]:3001->80/tcp
- [2026-05-22 14:12:54] [INFO]   crm-tigre-redis | Up 22 hours (healthy) | 0.0.0.0:6380->6379/tcp, [::]:6380->6379/tcp
- [2026-05-22 14:12:54] [INFO]   crm-tigre-postgres | Up 22 hours (healthy) | 0.0.0.0:5433->5432/tcp, [::]:5433->5432/tcp
- [2026-05-22 14:12:54] [INFO]   aurora_redis | Up 22 hours | 0.0.0.0:6381->6379/tcp, [::]:6381->6379/tcp
- [2026-05-22 14:12:54] [INFO]   jarvis_frontend | Up 22 hours (unhealthy) | 0.0.0.0:8080->80/tcp, [::]:8080->80/tcp
- [2026-05-22 14:12:54] [INFO]   jarvis_executor_api | Up 22 hours (healthy) | 0.0.0.0:3000->3000/tcp, [::]:3000->3000/tcp
- [2026-05-22 14:12:54] [INFO]   jarvis_postgres | Up 22 hours (healthy) | 5432/tcp
- [2026-05-22 14:12:54] [INFO] --- Deps criticas (gap do pyproject minimalista) ---
- [2026-05-22 14:12:55] [INFO]   langgraph -> instalado
- [2026-05-22 14:12:55] [INFO]   litellm -> instalado
- [2026-05-22 14:12:55] [INFO]   fastapi -> instalado
- [2026-05-22 14:12:55] [INFO]   mem0ai -> FALTANDO
- [2026-05-22 14:12:55] [INFO]   crewai -> FALTANDO
- [2026-05-22 14:12:55] [INFO]   sentence_transformers -> instalado
- [2026-05-22 14:12:55] [INFO] requirements-activate.txt criado (so o que falta, sem litellm-gateway)
- [2026-05-22 14:12:55] [INFO] Instalando deps de ativacao (pode demorar)...
- [2026-05-22 14:12:56] [INFO]   verify: langgraph OK
- [2026-05-22 14:12:56] [INFO]   verify: mem0 FALHOU: No module named 'mem0'
- [2026-05-22 14:12:56] [INFO] akasha-postgres ja esta UP — nao tocar
- [2026-05-22 14:12:57] [INFO] aurora_redis ja esta UP — nao tocar
- [2026-05-22 14:12:57] [INFO] Reativando container existente: publisher-os-qdrant
- [2026-05-22 14:12:57] [INFO] Reativando container existente: publisher-os-redis
- [2026-05-22 14:12:57] [INFO] Ollama UP :11434
- [2026-05-22 14:12:57] [INFO] Rodando baseline de testes (subset rapido)...
- [2026-05-22 14:13:03] [INFO]   baseline: ERROR tests/observability/test_e2e_dryrun.py
- [2026-05-22 14:13:03] [INFO]   baseline: !!!!!!!!!!!!!!!!!!! Interrupted: 7 errors during collection !!!!!!!!!!!!!!!!!!!
- [2026-05-22 14:13:03] [INFO]   baseline: 8631 tests collected, 7 errors in 4.28s
- [2026-05-22 14:13:03] [INFO] --- Modulos com dry_run, classificados por risco ---
- [2026-05-22 14:13:03] [INFO]   L0-L2 (seguro p/ ativar): observability, metrics, reports, knowledge_context, memory_intel
- [2026-05-22 14:13:03] [INFO]   L3+ (PERMANECE dry_run ate gate humano): sales_crm, sales, real_world_actions, publisher, argos_bridge, commercial_sdr
- [2026-05-22 14:13:03] [PAUSE] PAUSA HUMANA REGISTRADA: Decidir quais modulos L0-L2 ativar para execucao real
- [2026-05-22 14:13:03] [GUARD] Por seguranca, NENHUM dry_run foi virado automaticamente. Ative manualmente apos revisar.
- [2026-05-22 14:13:03] [INFO] KRATOS presente — bridge tem os dois lados
- [2026-05-22 14:13:03] [INFO] KRATOS backend/app/main.py existe (31 routers + SSE) — NAO recriar gateway
- [2026-05-22 14:13:03] [PAUSE] PAUSA HUMANA REGISTRADA: Subir KRATOS backend: uvicorn app.main:app (dentro de backend/)
- [2026-05-22 14:13:04] [INFO] Smoke test da kratos_bridge (lado OMNIS)...
- [2026-05-22 14:13:04] [INFO] src.kratos_bridge.bridge importavel OK
- [2026-05-22 14:13:04] [INFO] --- Estado pos-AUTORUN ---
- [2026-05-22 14:13:04] [INFO]   :5432 -> UP
- [2026-05-22 14:13:04] [INFO]   :6381 -> UP
- [2026-05-22 14:13:08] [INFO]   :6333 -> DOWN
- [2026-05-22 14:13:08] [INFO]   :11434 -> UP
- [2026-05-22 14:13:12] [INFO]   :8000 -> DOWN
- [2026-05-22 14:13:12] [INFO] Rodando suite de testes pos-mudancas...
- [2026-05-22 14:13:17] [INFO]   test: ERROR tests/integration/test_wave7b_war_room_to_report.py
- [2026-05-22 14:13:17] [INFO]   test: ERROR tests/observability/test_audit.py
- [2026-05-22 14:13:17] [INFO]   test: ERROR tests/observability/test_e2e_dryrun.py
- [2026-05-22 14:13:17] [INFO]   test: !!!!!!!!!!!!!!!!!!! Interrupted: 7 errors during collection !!!!!!!!!!!!!!!!!!!
- [2026-05-22 14:13:17] [INFO]   test: 7 errors in 3.21s

## PAUSAS HUMANAS PENDENTES

| O que fazer | Onde | Tempo |
|---|---|---|
| Decidir quais modulos L0-L2 ativar para execucao real | Revisar lista acima + rodar testes | 10 min |
| Subir KRATOS backend: uvicorn app.main:app (dentro de backend/) | Terminal separado | 2 min |
- [2026-05-22 14:13:17] [END] AUTORUN concluido. 2 pausas humanas registradas.

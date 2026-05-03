# ESTADO ATUAL RESUMIDO — OMNIS / JARVIS CONTROL

**Gerado em:** 2026-05-03T10:10:36Z
**Session ID:** `84f0884b-ec8e-4a37-8663-64e59bb3d68d`

## 1. RISCOS IMEDIATOS

- 🔴 **DISCO CRÍTICO**: C:\ — 8.1% livre (75.3 GB de 924.3 GB). Risco de falha em Docker, logs e builds. Não executar builds pesados antes de saneamento.

- 🟡 **Containers unhealthy:** crm-tigre-backend, jarvis_frontend (2 de 18)

---

## 2. Resumo executivo

Sistema OMNIS operacional. 98 skills detectadas, 18 containers rodando, Publisher OS não identificado na porta 8000. Memória: Qdrant inacessível, Akasha encontrado.

## 3. Status geral

- **Skills:** 98 (17 executáveis)
- **Docker:** 18 rodando, 2 unhealthy
- **Publisher OS:** port_open_no_response
- **Qdrant:** falha
- **Akasha:** ok
- **Obsidian:** 7,833 .md files
- **Disco:** critical

## 4. Skills

| Tipo | Quantidade |
|------|-----------|
| Executáveis (com run.py) | 17 |
| Doc (pasta com SKILL.md) | 38 |
| Doc (arquivo .md solto) | 43 |

## 5. Publisher OS

- **Status:** port_open_no_response
- **Identificado:** Não
- **Porta 8000 aberta:** True

## 6. Docker

- **Rodando:** 18
- **Unhealthy:** 2

| Container | Status | Portas |
|-----------|--------|-------|
| ✅ publisher-os-publisher-core-1 | Up 3 days | 0.0.0.0:8000->8000/tcp, [::]:8000->8000/ |
| ✅ publisher-os-litellm-1 | Up 5 days | 0.0.0.0:4002->4000/tcp, [::]:4002->4000/ |
| ✅ publisher-os-n8n-1 | Up 5 days | 0.0.0.0:5678->5678/tcp, [::]:5678->5678/ |
| ✅ publisher-os-publish-worker-1 | Up 9 days |  |
| ✅ open-webui | Up 9 days (healthy) | 0.0.0.0:3100->8080/tcp, [::]:3100->8080/ |
| ✅ publisher-os-redis-1 | Up 9 days | 0.0.0.0:6382->6379/tcp, [::]:6382->6379/ |
| ✅ publisher-os-qdrant-1 | Up 9 days | 0.0.0.0:6333-6334->6333-6334/tcp, [::]:6 |
| ✅ publisher-os-supabase-db-1 | Up 9 days | 0.0.0.0:5434->5432/tcp, [::]:5434->5432/ |
| ✅ publisher-os-minio-1 | Up 9 days (healthy) | 0.0.0.0:9000-9001->9000-9001/tcp, [::]:9 |
| ✅ akasha-postgres | Up 9 days (healthy) | 0.0.0.0:5432->5432/tcp, [::]:5432->5432/ |
| 🔴 crm-tigre-backend | Up 9 days (unhealthy) | 0.0.0.0:4000->4000/tcp, [::]:4000->4000/ |
| ✅ crm-tigre-frontend | Up 9 days (healthy) | 0.0.0.0:3001->80/tcp, [::]:3001->80/tcp |
| ✅ crm-tigre-redis | Up 9 days (healthy) | 0.0.0.0:6380->6379/tcp, [::]:6380->6379/ |
| ✅ crm-tigre-postgres | Up 9 days (healthy) | 0.0.0.0:5433->5432/tcp, [::]:5433->5432/ |
| ✅ aurora_redis | Up 9 days | 0.0.0.0:6381->6379/tcp, [::]:6381->6379/ |
| 🔴 jarvis_frontend | Up 9 days (unhealthy) | 0.0.0.0:8080->80/tcp, [::]:8080->80/tcp |
| ✅ jarvis_executor_api | Up 9 days (healthy) | 0.0.0.0:3000->3000/tcp, [::]:3000->3000/ |
| ✅ jarvis_postgres | Up 9 days (healthy) | 5432/tcp |

## 7. Memória

- **Qdrant (http://localhost:6333):** inacessível
- **Akasha (container akasha-postgres):** encontrado
  - Status: Up 9 days (healthy)

## 8. Obsidian

- **Vault:** C:\Users\lucas\Desktop\ARQUIVOS_MANUS_CLAUDE\OBSIDIAN\ComandoCentral
- **Arquivos .md:** 7833
- **Pastas principais:**
  - .obsidian
  - 00_Contexto
  - 01_SDR_Hoteis
  - 02_Hub_Social
  - 03_Apps
  - 04_Templates
  - 05_Leads_Qualificados
  - 05_Skills
  - 06_Midias
  - 07_PDFs
  - 08_Docs_Word
  - 09_Planilhas
  - 10_Textos
  - 90_Output
  - 91_Lixeira

## 9. Video Pipeline

- **Classificação:** operational
- **Confiança:** high

**Sinais:**
  - ❌ local_video_files_found
  - ❌ google_drive_code_found
  - ✅ video_ingestion_code_found
  - ❌ video_asset_registry_found
  - ❌ video_asset_schema_found
  - ✅ content_queue_found
  - ✅ daily_queue_found
  - ❌ caption_generation_found
  - ✅ publisher_integration_found
  - ✅ instagram_account_mapping_found
  - ✅ account_registry_found
  - ✅ content_queue_found_explicit
  - ✅ used_or_published_marker_found

**Counts:**
  - local_video_files: 0
  - keyword_hits: 0
  - total_evidence: 90
  - registry_assets: 0
  - registry_accounts: 2
  - queue_items: 42
  - scan_duration_ms: 71
  - scan_timed_out: False

## 10. Content Queue (Fase 2B)

- **Contas cadastradas:** 2 (2 ativas)
- **Itens na fila:** 42
- **Precisa de asset:** 40
- **Precisa de legenda:** 0
- **Aprovados:** 0
- **Agendados:** 0

**Distribuição por conta:**
  - @afamiliatigrereal: 21 itens
  - @lucastigrereal: 21 itens

## 11. Caption Approval (Fase 2C)

- **Total de rascunhos:** 41
- **Pendentes de revisão:** 40
- **Stale (> 3 dias):** 0

**Distribuição por status:**
  - ✅ approved: 1
  - ⚠️ needs_review: 40

## 12. Argos Bridge (Fase 2E)

- **Total de ArgosDrafts:** 0

## 13. Segurança

- Nenhum .env foi lido ou exposto
- Nenhuma API externa foi chamada
- Nenhum container foi modificado
- Nenhuma skill foi executada sem confirmação
- Path traversal é bloqueado em todos os comandos

## 14. Próximos passos

1. **Fase 3 — OAuth Meta:** Configurar META_APP_SECRET, rodar OAuth, validar token
2. **Fase 4 — Memória conectada:** Obsidian read-only -> Qdrant search -> Akasha discovery
3. **Fase 5 — Saneamento Docker:** Limpeza de imagens e volumes não utilizados
5. **Fase 6 — Runtime agentic:** LangGraph, tool router, critic loop

## 15. O que NÃO foi alterado

- `~/.claude/` — não modificado
- `~/publisher-os/` — não modificado
- `~/JARVIS_OS/` — não modificado
- Obsidian vault — não modificado
- Docker — não modificado (read-only)
- .env — não lido
- Instagram / Meta API — não chamado

## 16. Comandos úteis

```bash
python jarvis.py status
python jarvis.py skills
python jarvis.py doctor > diagnose.json
python jarvis.py report
python jarvis.py publisher-health
python jarvis.py docker-status
python jarvis.py obsidian-status
python jarvis.py video-status
python omnis.py video-status
python omnis.py accounts add @handle --tags tag1,tag2
python omnis.py accounts list
python omnis.py queue generate --days 7 --apply
python omnis.py queue list
python omnis.py queue today
python omnis.py queue stats
python omnis.py queue assign <queue_id> <asset_id>
python omnis.py queue export
python omnis.py captions create <queue_id> --text "..." --hashtags tag1,tag2
python omnis.py captions list
python omnis.py captions show <draft_id>
python omnis.py captions update <draft_id> --text "..."
python omnis.py captions submit <draft_id>
python omnis.py captions export
python omnis.py approvals pending
python omnis.py approvals approve <draft_id>
python omnis.py approvals reject <draft_id> --reason "..."
python omnis.py approvals log
python omnis.py templates list
python omnis.py templates show <template_id>
```
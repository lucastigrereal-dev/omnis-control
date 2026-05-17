# ESTADO ATUAL RESUMIDO — OMNIS / JARVIS CONTROL

**Gerado em:** 2026-05-17T00:09:12Z
**Session ID:** `d835efca-62dd-4d46-b78a-e99930dc7a82`

## 1. RISCOS IMEDIATOS

- 🟡 **DISCO EM ALERTA**: C:\ — 16.1% livre (148.7 GB de 924.3 GB). Planejar saneamento antes da Fase 2.

---

## 2. Resumo executivo

Sistema OMNIS operacional. 75 skills detectadas, 0 containers rodando, Publisher OS não identificado na porta 8000. Memória: Qdrant inacessível, Akasha não encontrado.

## 3. Status geral

- **Skills:** 75 (8 executáveis)
- **Docker:** 0 rodando, 0 unhealthy
- **Publisher OS:** port_closed
- **Qdrant:** falha
- **Akasha:** falha
- **Obsidian:** não encontrado .md files
- **Disco:** warning

## 4. Skills

| Tipo | Quantidade |
|------|-----------|
| Executáveis (com run.py) | 8 |
| Doc (pasta com SKILL.md) | 24 |
| Doc (arquivo .md solto) | 43 |

## 5. Publisher OS

- **Status:** port_closed
- **Identificado:** Não
- **Porta 8000 aberta:** False

## 6. Docker

- **Rodando:** 0
- **Unhealthy:** 0


## 7. Memória

- **Qdrant (http://localhost:6333):** inacessível
- **Akasha (container akasha-postgres):** não encontrado

## 8. Obsidian

- **Vault:** C:\Users\lucas\Desktop\ARQUIVOS_MANUS_CLAUDE\OBSIDIAN\ComandoCentral
- **Arquivos .md:** timeout
- **Pastas principais:**

## 9. Video Pipeline

- **Classificação:** operational
- **Confiança:** high

**Sinais:**
  - ❌ local_video_files_found
  - ❌ google_drive_code_found
  - ✅ video_ingestion_code_found
  - ✅ video_asset_registry_found
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
  - total_evidence: 89
  - registry_assets: 1
  - registry_accounts: 2
  - queue_items: 42
  - scan_duration_ms: 79
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

- **Total de rascunhos:** 42
- **Pendentes de revisão:** 40
- **Stale (> 3 dias):** 40

**Distribuição por status:**
  - ✅ approved: 1
  - ✅ draft: 1
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
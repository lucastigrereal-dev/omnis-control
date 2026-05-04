# Workflow Ponta a Ponta — OMNIS

**Data:** 2026-05-04
**Status:** Implementado
**Versão:** 1.0

---

## Visão Geral

Fluxo unificado de produção de conteúdo: da ideia à publicação nos 6 perfis Instagram.

```
IDEA → PLAN → BRIEF → PRODUCE → DRAFT → APPROVE → QUEUE → PUBLISH
  │       │        │        │        │        │         │        │
  │    OMNIS    OMNIS   Publisher  ARGOS    Cockpit  Publisher  Meta
  │    Queue    Doc     OS CrewAI  Bridge   :3200    OS BullMQ  GraphAPI
  │    JSONL    .md     MCP tool  JSONL    approve  MCP tool   (future)
```

## Estágios

### 1. IDEA
Entrada: tema, formato, página alvo, objetivo (alcance/autoridade/conversão).

### 2. PLAN — OMNIS Content Queue
Gera slots editoriais na fila local (`data/content_queue.jsonl`).

```bash
omnis queue generate --days 7
omnis queue list
omnis queue stats
```

**Status:** `planned` → `needs_asset` → `needs_caption`

### 3. BRIEF — OMNIS Doc
Briefing de conteúdo com diretrizes, formato, referências.

### 4. PRODUCE — Publisher OS CrewAI
Envia o briefing para a crew de produção do Publisher OS.

```bash
omnis workflow run --topic "Viagem em família para Natal" \
  --pagina afamiliatigrereal --formato carrossel
```

**Integração:** HTTP para `POST /api/v1/crews/run` no Publisher OS (`:8000`).

### 5. DRAFT — ARGOS Bridge
Converte o resultado da produção em um ArgosDraft local.

```bash
omnis argos-drafts create <queue_id>
omnis argos-drafts list
```

**Status:** `local_draft` → (pronto para aprovação)

### 6. APPROVE — Approval Gate
Revisão humana. Pode ser feita:
- Via CLI: `omnis caption approve <draft_id>`
- Via Cockpit Publisher OS (`:3200`)

### 7. QUEUE — Publisher OS BullMQ
Enfileira o post aprovado para publicação.

```bash
omnis workflow enqueue <draft_id>
```

**Integração:** ARGOS MCP tool `argos_enqueue_post` via Publisher OS.

### 8. PUBLISH — Meta Graph API
Publicação real no Instagram. **Depende de OAuth Meta** (pendente).

## Comandos OMNIS

### Workflow completo (automático)
```bash
omnis workflow run --topic "Tema" --pagina handle --formato carrossel
```
Executa: IDEA → PLAN → BRIEF → PRODUCE → DRAFT → APPROVE (ponto de pausa)

### Steps individuais
```bash
omnis workflow status                          # Status do pipeline
omnis workflow run --topic "X" --pagina handle # Pipeline completo
omnis workflow enqueue <draft_id>              # Enfileira no Publisher OS
```

## Arquitetura de Integração

```
┌──────────────────────────────────────────────────────────────┐
│                        OMNIS CLI                             │
│  omnis workflow, omnis queue, omnis argos-drafts             │
├──────────────────────────────────────────────────────────────┤
│                    Workflow Engine                            │
│  src/workflow/engine.py — orquestração dos estágios          │
├──────────────────┬───────────────────┬───────────────────────┤
│  OMNIS Local     │  ARGOS Bridge     │  Publisher OS HTTP    │
│  content_queue/  │  argos_bridge/    │  :8000/api/v1/        │
│  caption_approval│  data/argos_*.jsonl│  MCP tools via HTTP   │
│  data/*.jsonl    │                   │                       │
└──────────────────┴───────────────────┴───────────────────────┘
```

## Próximos Passos

- [ ] Conectar 6 contas Instagram (Account Registry)
- [ ] OAuth Meta (último passo)
- [ ] Dashboard de métricas no OMNIS

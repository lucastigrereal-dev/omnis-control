---
id: argos-bridge
name: ARGOS Bridge
description: Ponte entre skills Instagram e o pipeline de publicacao ARGOS (API → BullMQ → publish-worker → Graph API)
status: active
sector: midia_conteudo
model: null
cost_estimate: 0
inputs:
  - mode: caption|carousel|calendar|video|evaluate|list|accounts
  - pagina: string (handle Instagram)
outputs:
  - post_id: string (UUID do post no ARGOS)
  - status_post: draft|scheduled
  - next_action: string
---

# ARGOS Bridge

Conecta os outputs das 6 skills Instagram ao pipeline de publicacao ARGOS.

## Pipeline Completo

```
Skill → 60_OUTPUTS/ → argos-bridge → ARGOS API (:8000) → BullMQ (Redis)
  → publish-worker (TypeScript) → Graph API v21.0 → Instagram
```

## Modos de Uso

### 1. caption — Criar post a partir de legenda SEOgram
```bash
python run.py caption --pagina lucastigrereal --caption "Legenda aqui" \
  --media-url "https://..." --schedule "2026-05-01T10:00:00"
```

### 2. carousel — Importar carrossel
```bash
python run.py carousel --pagina afamiliatigrereal --file carrossel.json
```

### 3. calendar — Importar calendario editorial (bulk)
```bash
python run.py calendar --pagina lucastigrereal --file calendario_30_dias.json
```

### 4. video — Criar post de Reels
```bash
python run.py video --pagina oinatalrn --media-url "https://..." \
  --caption "Novo video!" --schedule "2026-05-01T14:00:00"
```

### 5. evaluate — Avaliar conteudo antes de publicar
```bash
python run.py evaluate --text "Conteudo para avaliar" --pagina lucastigrereal
```

### 6. list — Ver fila de publicacao
```bash
python run.py list
python run.py list --status scheduled
```

### 7. accounts — Ver contas cadastradas
```bash
python run.py accounts
```

## Fluxo de Aprovacao Recomendado

1. Gerar conteudo com skill setorial → salva em `60_OUTPUTS/`
2. Avaliar com `argos-bridge evaluate` (ContentJudge)
3. Criar post com `argos-bridge caption` (status: draft)
4. Revisar na fila de aprovacao: `GET /api/v1/argos/approval-queue`
5. Agendar: `PATCH /api/v1/argos/posts/{id}/schedule`
6. Enfileirar: `POST /api/v1/argos/posts/{id}/enqueue`
7. Worker publica via Graph API

## next_action

Sempre retorna o proximo passo concreto (ex: "approve 30 posts", "enqueue scheduled posts").

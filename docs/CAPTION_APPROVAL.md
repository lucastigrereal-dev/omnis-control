# Caption Draft + Approval Gate — Fase 2C

Sistema local de rascunho e aprovação de legendas para o Instagram.
Não substitui o Publisher OS — é o controle de qualidade editorial.

## Premissa

> Caption Draft é o **rascunho**. Approval Gate é o **freio**.
> Nenhum conteúdo publicado sem passar pelo gate.

## Status Pipeline

```
draft → needs_review → approved (queue=caption_ready)
                      → rejected (queue=needs_caption) → revised → needs_review
```

### Estados do Draft

| Status | Significado |
|--------|-------------|
| `draft` | Sendo escrito |
| `needs_review` | Aguardando aprovação |
| `approved` | Aprovado (queue → caption_ready) |
| `rejected` | Rejeitado (queue → needs_caption) |
| `revised` | Revisado após reject/approve |
| `stale` | Parado > 3 dias em needs_review/revised |

## Modelos

### CaptionDraft
`data/caption_drafts.jsonl`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| draft_id | str | ID único (12 hex) |
| queue_id | str | Referência ao slot na Content Queue |
| account_handle | str | Conta Instagram |
| caption_text | str | Texto da legenda |
| hashtags | list[str] | Lista de hashtags |
| cta | str | Call to action |
| status | str | draft / needs_review / approved / rejected / revised / stale |
| version | int | Versão do rascunho |
| objective | str | alcance / autoridade / conversao / relacionamento / teste |
| format | str | reels / carousel / stories / feed / unknown |
| notes | str | Notas internas |
| rejection_reason | str | Motivo da rejeição (preenchido ao rejeitar) |
| asset_id | str | Asset de vídeo associado |
| created_at | str | ISO 8601 |
| updated_at | str | ISO 8601 |

### ApprovalLogEntry
`data/approval_log.jsonl` (append-only)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| event_id | str | ID único (12 hex) |
| draft_id | str | Referência ao draft |
| queue_id | str | Referência ao slot |
| action | str | created / updated / submitted / approved / rejected |
| actor | str | `local_user` (sempre) |
| reason | str | Motivo (preenchido em rejected) |
| previous_status | str | Status anterior |
| new_status | str | Status novo |
| timestamp | str | ISO 8601 |

## Regras de Versionamento

- **Create** → version = 1
- **Update com alteração de conteúdo** (caption_text, hashtags, cta) → version += 1
- **Reject** → não altera versão
- **Update após rejected** → status = revised, version += 1, rejection_reason = null
- **Update após approved** → status = revised, version += 1
- **--force** → atualiza draft existente como revised, versionando

## Pré-Validação (approve)

### Bloqueia aprovação se:
- Texto vazio
- Texto < 10 caracteres
- Placeholders não resolvidos: `[HOOK A REVISAR]`, `[CORPO DA LEGENDA A REVISAR]`, `[CTA A DEFINIR]`

### Warning (não bloqueia):
- Menos de 3 hashtags
- CTA não definido ou muito curto

## Templates

Organizados por **objetivo** primeiro. 5 templates padrão:

| ID | Objetivo | Formato | Propósito |
|----|----------|---------|-----------|
| `alcance_reels` | alcance | reels | Hook forte, viral |
| `alcance_carousel` | alcance | carousel | Deslizar, engajar |
| `autoridade_feed` | autoridade | qualquer | Dados, cases, autoridade |
| `conversao_feed` | conversao | qualquer | Oferta, CTA direto |
| `relacionamento_stories` | relacionamento | qualquer | Perguntas, opinião |
| `teste_flex` | teste | qualquer | Experimento |

## CLI

### Captions
```bash
python omnis.py captions create <queue_id> --text "..." --hashtags tag1,tag2
python omnis.py captions list [--status] [--account]
python omnis.py captions show <draft_id>
python omnis.py captions update <draft_id> [--text] [--hashtags] [--cta]
python omnis.py captions submit <draft_id>
python omnis.py captions export [--status] [--account]
```

### Approvals
```bash
python omnis.py approvals pending
python omnis.py approvals approve <draft_id>
python omnis.py approvals reject <draft_id> --reason "..."
python omnis.py approvals log [--limit] [--draft] [--action]
```

### Templates
```bash
python omnis.py templates list [--objective]
python omnis.py templates show <template_id>
```

## Dependências

- `caption_approval → content_queue` (unidirecional)
- `content_queue` **NUNCA** importa `caption_approval`
- Aprovação atualiza queue status via função injetada (`queue_updater`)

## Arquivos

| Arquivo | Propósito |
|---------|-----------|
| `src/caption_approval/models.py` | CaptionDraft, DraftStatus, CaptionTemplate, ApprovalLogEntry |
| `src/caption_approval/drafts.py` | DraftsManager CRUD + approval log |
| `src/caption_approval/approvals.py` | ApprovalGate: validate, approve, reject |
| `src/caption_approval/templates.py` | TemplateLibrary com templates padrão |
| `data/caption_drafts.jsonl` | Armazenamento de rascunhos |
| `data/approval_log.jsonl` | Log append-only de aprovações |
| `data/caption_templates.json` | Templates de legenda |
| `tests/test_caption_approval.py` | 49 testes |

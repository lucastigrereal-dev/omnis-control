# Creative Production Pipeline

## Fluxo Completo

```
Queue Item → Caption Draft → Caption Approval → Creative Brief →
Production Item → Creative Review → Export Package (13 artefatos) →
Argos Draft (futuro)
```

---

## 1. Queue Item

**Entrada:** Item da fila de conteúdo (ideia bruta)
**Status possíveis:** `pending`, `caption_ready`, `needs_asset`, `approved`, `scheduled`
**Saída:** `queue_id` + `account_handle`

---

## 2. Caption Draft → Caption Approval

**Entrada:** Rascunho de legenda
**Status possíveis:** `draft`, `needs_review`, `approved`, `rejected`
**Gate:** Apenas captions `approved` podem seguir para produção
**Saída:** `caption_draft_id` aprovado

---

## 3. Creative Brief

**Entrada:** `queue_id` + `caption_draft_id` + especificações criativas
**Campos obrigatórios:** account_handle, format, objective, visual_direction
**Warnings possíveis:**
- `QUEUE_NOT_FOUND` — queue_id não existe na fila
- `CAPTION_DRAFT_NOT_FOUND` — draft_id não encontrado
- `CAPTION_NOT_APPROVED` — caption não aprovado (ou não fornecido)
**Status possíveis:** `draft`, `approved`, `rejected`, `in_production`

---

## 4. Production Item

**Entrada:** `creative_brief_id` + especificações de asset
**Campos:** asset_type (video, image, carousel_asset), tool_target (canva, capcut, runway)
**Status possíveis:** `pending`, `in_progress`, `done`, `failed`, `skipped`
**Gate:** Asset deve ser attachado (`attach_asset()`) para marcar como `done`

---

## 5. Creative Review

**Entrada:** `creative_brief_id`
**Ações:** `approve_brief()`, `reject_brief()`, `request_changes()`
**Status possíveis:** `approved`, `rejected`, `changes_requested`
**Gate combinado (is_ready_for_argos):**
- Caption approved ✅
- Creative approved ✅
- Asset attached ✅
- Resultado: `READY_FOR_ARGOS` ou lista de issues

---

## 6. Export Package

**Entrada:** `brief_id` (brief aprovado)
**Saída:** Diretório em `data/exports/creative_packages/<package_id>/`

### Artefatos (13 no total):

| # | Arquivo | Tipo | Obrigatório |
|---|---------|------|-------------|
| 1 | `brief.md` | Markdown | Sim |
| 2 | `caption.txt` | Texto | Sim |
| 3 | `hashtags.txt` | Texto | Sim |
| 4 | `script.md` | Markdown | Sim |
| 5 | `shot_list.md` | Markdown | Sim |
| 6 | `design_notes.md` | Markdown | Sim |
| 7 | `editing_notes.md` | Markdown | Sim |
| 8 | `asset_requirements.json` | JSON | Sim |
| 9 | `tool_suggestions.md` | Markdown | Sim |
| 10 | `production_checklist.md` | Markdown | Sim |
| 11 | `preview.html` | HTML | Sim |
| 12 | `mock_image.png` | PNG | Sim |
| 13 | `WARNINGS.md` | Markdown | Apenas se houver avisos |

---

## 7. Argos Draft (Futuro)

**Entrada:** Export Package completo
**Destino:** Bridge de publicação para Instagram
**Dependência:** OAuth Meta configurado

# P1.3b — Post Preflight Blocker Audit

**Data:** 2026-05-08

---

## Diagnóstico

### 1. Qual é o draft aprovado?

`draft_id=1d482d82` — v2, @lucastigrereal
Texto: "O Brasil tem lugares que parecem cena de..."

### 2. Está ligado a qual queue item?

`queue_id=0b79aa1c` — @lucastigrereal, status=`caption_ready`

### 3. Existem 2 slots caption_ready sem asset?

| queue_id | conta | asset |
|---|---|---|
| 0b79aa1c | @lucastigrereal | NONE |
| cd0d11f7 | @lucastigrereal | NONE (também sem draft!) |

### 4. Por que a queue tinha 0 aprovados/agendados?

**Bug P1.3b corrigido:** `_check_queue_items()` só verificava `("approved", "scheduled")`, excluindo `caption_ready`. Adicionado `caption_ready` à lista.

### 5. Bloqueio é:

- `assets_ready` (opcional): true — 0 de 2 slots têm asset. Não é bloqueante.
- Os 40 drafts `needs_review` têm placeholder `[HOOK A REVISAR]` — nenhum texto real
- 1 draft `draft` órfão sem queue

### 6. Menor ação segura para preparar 1 post:

1. Atribuir asset ao slot `0b79aa1c`: `omnis queue assign 0b79aa1c <asset_id>`
2. Verificar legenda: `omnis post package 0b79aa1c`
3. Com legenda OK e asset atribuído, post fica pronto para revisão humana

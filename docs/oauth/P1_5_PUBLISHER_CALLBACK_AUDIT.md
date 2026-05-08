# P1.5 — Publisher OS Callback Audit

**Data:** 2026-05-08 | **Publisher OS branch:** argos-evolucao-passo-0

---

## Perguntas e Respostas

### 1. A rota `/api/v1/argos/oauth/callback` existe?

**ANTES de P1.5:** NAO. Retornava HTTP 404.

**DEPOIS de P1.5:** SIM. Implementado stub seguro em `core/api/main.py`.

### 2. Qual arquivo registra rotas FastAPI?

`core/api/main.py` — todas as rotas sao definidas com decorators `@app.get(...)` / `@app.post(...)` diretamente na instancia `app`.

### 3. Existe router ARGOS?

Nao ha um router separado para ARGOS. As rotas `/api/v1/argos/*` sao definidas inline em `main.py`:
- `GET /api/v1/argos/oauth/url` (linha 465)
- `POST /api/v1/argos/oauth/token` (linha 483)
- `GET /api/v1/argos/oauth/callback` (linha 551 — NOVO P1.5)
- `GET /api/v1/argos/publish-status` (linha 345)
- `GET /api/v1/argos/social-accounts` (linha 417)
- E varias outras...

### 4. Existe modulo auth/oauth?

Ha roteamento inline, nao modulo separado. O `scripts/oauth_setup.py` prove CLI manual para o fluxo OAuth.

### 5. O Publisher Core :8000 esta saudavel?

`curl http://localhost:8000/health` → `{"status":"healthy"}`

### 6. A ausencia era bug, TODO ou rota com caminho diferente?

**Bug/gap arquitetural.** As rotas `oauth/url` e `oauth/token` existiam, mas o callback (que a Meta redireciona) nao tinha endpoint web. O fluxo OAuth so funcionava com o script CLI manual `oauth_setup.py callback --code CODE`, onde o usuario precisava copiar o code manualmente da barra de endereco do navegador.

A rota corrigida em P1.5 permite que o fluxo OAuth Meta funcione automaticamente: a Meta redireciona o navegador para o callback, que recebe o `code` e pode fazer o token exchange.

# P1.4 — GO/NO-GO: OAuth Meta Validation + First Post Package

**Data:** 2026-05-08 | **Status OAuth:** `human_required` | **Status Post:** `partial`

---

## OAuth Real — NO-GO

**Por que:** 3 variaveis obrigatorias nao estao prontas:
- `META_APP_SECRET` esta vazio
- `META_GRAPH_VERSION` nao existe no .env
- `INSTAGRAM_BUSINESS_ACCOUNT_ID` esta vazio (e usa nome antigo `INSTAGRAM_BUSINESS_ID`)

**O que falta:**
1. Lucas preencher `META_APP_SECRET` com valor real do Meta Developers.
2. Adicionar `META_GRAPH_VERSION=v20.0` ao .env.
3. Preencher `INSTAGRAM_BUSINESS_ACCOUNT_ID` com o ID real do Business Account.
4. Verificar se `FACEBOOK_PAGE_ID` e `META_ACCESS_TOKEN` sao necessarios agora ou depois.

**Riscos:**
- Sem `META_APP_SECRET`, o fluxo OAuth nao consegue completar o token exchange.
- Callback URL (`localhost:8000/api/v1/argos/oauth/callback`) retorna 404 — rota nao implementada no Publisher OS.
- Sem a rota de callback, mesmo com credenciais, o redirect do Meta nao tem onde cair.

**Quando sera GO:**
Quando `omnis oauth probe` mostrar `present` para META_APP_SECRET e META_GRAPH_VERSION, e a rota de callback existir.

---

## Primeiro Post Real — NO-GO

**Por que:** 2 condicoes nao atendidas:
- OAuth nao esta pronto (bloqueio upstream).
- Asset nao atribuido ao slot `0b79aa1c`.

**Candidato identificado:**
- Queue ID: `0b79aa1c`
- Conta: `@lucastigrereal` (ALERTA: conta de alto risco para teste)
- Draft ID: `1d482d82` (aprovado, texto real)
- Status: `caption_ready`
- Asset: **ausente**
- Formato: carrossel

**O que falta:**
1. OAuth funcional.
2. Lucas atribuir asset ao slot: `omnis queue assign 0b79aa1c <asset_id>`.
3. Revisar e aprovar editorialmente o draft 1d482d82.
4. Escolher conta de menor risco para primeiro teste (@afamiliatigrereal sugerida).

**Riscos:**
- @lucastigrereal (690K) e a conta principal — erro no primeiro post teria visibilidade maxima.
- Carrossel sem multiplas imagens e carrossel fake.

**Quando sera GO:**
Quando OAuth estiver `ready`, asset atribuido, Lucas autorizar conteudo e conta.

---

## Resumo GO/NO-GO

| Gate | Veredito | Bloqueio Principal |
|---|---|---|
| OAuth Real | **NO-GO** | META_APP_SECRET vazio |
| Primeiro Post Real | **NO-GO** | OAuth + Asset ausente |
| Env Probe Seguro | **GO** | Infra pronta |
| Readiness Checker | **GO** | 15 checks funcionais |
| Package Local Dry-Run | **GO** | Candidato documentado |

---

## Proximos 5 Passos para Lucas

1. `[_]` Preencher `META_APP_SECRET` no `~/publisher-os/.env` (Meta Developers > App Settings > Basic).
2. `[_]` Adicionar `META_GRAPH_VERSION=v20.0` ao mesmo .env.
3. `[_]` Renomear `INSTAGRAM_BUSINESS_ID` para `INSTAGRAM_BUSINESS_ACCOUNT_ID` e preencher valor.
4. `[_]` Rodar `python jarvis.py oauth validate` para confirmar que tudo esta `present`.
5. `[_]` Atribuir asset ao slot `0b79aa1c` e rodar `python jarvis.py post package 0b79aa1c` para revisar.

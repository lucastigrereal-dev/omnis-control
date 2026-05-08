# P1.4 — Env Probe Report

**Data:** 2026-05-08 | **Ferramenta:** `src/oauth_readiness/env_probe.py`

---

## Resultado do Probe contra ~/publisher-os/.env

| Variavel | Status | Obrigatoria |
|---|---|---|
| META_APP_ID | `present` | Sim |
| META_APP_SECRET | `empty` | Sim |
| META_REDIRECT_URI | `present` | Sim |
| META_GRAPH_VERSION | `missing` | Sim |
| INSTAGRAM_BUSINESS_ACCOUNT_ID | `empty` (via alias INSTAGRAM_BUSINESS_ID) | Nao |
| FACEBOOK_PAGE_ID | `missing` | Nao |
| META_ACCESS_TOKEN | `missing` | Nao |

**Resumo:** 2 presentes, 2 vazias, 3 ausentes de 7 esperadas.

---

## Acoes humanas necessarias

1. Preencher `META_APP_SECRET` no `~/publisher-os/.env` com o valor do Meta Developers dashboard.
2. Adicionar `META_GRAPH_VERSION=v20.0` (ou versao atual) no .env.
3. Padronizar `INSTAGRAM_BUSINESS_ID` para `INSTAGRAM_BUSINESS_ACCOUNT_ID` e preencher com ID real.
4. Opcional: adicionar `FACEBOOK_PAGE_ID` se necessario para publicacao.
5. Opcional: `META_ACCESS_TOKEN` sera gerado pelo fluxo OAuth ou preenchido manualmente depois.

---

## Seguranca

- `env_probe.py` **nunca armazena ou retorna valores**.
- 31 testes de seguranca dedicados (test_env_probe.py + test_no_secrets_leaked.py).
- 59/59 testes no modulo `oauth_readiness` passam.
- Output humano e JSON contem apenas status (`present/missing/empty/invalid_format`).
- `__repr__` e `__str__` dos modelos nao expoem valores.
- `safe_summary()` garante que nenhum valor aparece em texto livre.

---

## CLI Disponivel

```bash
python jarvis.py oauth probe              # Status seguro das variaveis
python jarvis.py oauth probe --json       # JSON sem valores
python jarvis.py oauth validate           # Probe + readiness + GO/NO-GO
python jarvis.py oauth validate --json    # JSON completo sem valores
```

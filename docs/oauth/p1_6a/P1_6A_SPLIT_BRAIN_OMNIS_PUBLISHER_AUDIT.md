# P1.6A — Split-Brain OMNIS ↔ Publisher OS Audit

**Data:** 2026-05-08

---

## Diagnostico

OMNIS Control e Publisher OS mantem registros de conta Instagram **independentes e nao sincronizados**.

### OMNIS Control
- Arquivo: `data/accounts.jsonl`
- Modelo: `Account` dataclass (account_id, handle, platform, instagram_user_id, tags, priority, active)
- 2 contas cadastradas
- Nao contem: facebook_page_id, instagram_business_account_id, access_token

### Publisher OS
- Tabela: `social_accounts` (Supabase Postgres :5434)
- Colunas: platform, name, ig_user_id, access_token, followers_count
- Populado dinamicamente pelo fluxo OAuth real em `core/api/main.py`
- Contem tokens reais (apos OAuth)

## Riscos

1. **Duplicacao**: mesma conta pode ter IDs diferentes nos dois sistemas
2. **Dessincronizacao**: OMNIS pode achar que conta nao existe, mas Publisher ja tem token
3. **Sobrescrita acidental**: update em um sistema nao reflete no outro
4. **Token storage duplicado**: risco de vazamento se .env e DB tiverem tokens diferentes

## Recomendacao

1. Nao sincronizar agora — risco de mover token real sem querer
2. Futuro: Publisher OS expoe endpoint read-only `GET /api/v1/argos/social-accounts` (ja existe na linha 418)
3. OMNIS consulta esse endpoint como fonte de verdade para status OAuth
4. `accounts.jsonl` permanece como config operacional (tags, priority, posting times)

---

**Fim do split-brain audit.**

# P1.6A — Accounts Registry Audit

**Data:** 2026-05-08

---

## Contas no OMNIS (`data/accounts.jsonl`)

| Campo | @lucastigrereal | @afamiliatigrereal |
|---|---|---|
| account_id | c225c8d0ea69 | 84033ab95c56 |
| display_name | Lucas Tigre | A Familia Tigre |
| platform | instagram | instagram |
| priority | high | medium |
| active | Sim | Sim |
| instagram_user_id | null | null |
| facebook_page_id | nao existe no modelo | nao existe no modelo |
| tags | pessoal, ia | familia, viagem |

## Contas AUSENTES do Registry

4 handles conhecidos nao estao no `accounts.jsonl`:

| Handle | Seguidores | Nicho |
|---|---|---|
| @oinatalrn | 630K | Turismo Natal/RN |
| @agenteviajabrasil | 452K | Viagens Brasil |
| @oquecomernatalrn | 249K | Gastronomia Natal |
| @natalaivoueu | 240K | Guia Natal, praias |

## Publisher OS — Tabela `social_accounts`

Publisher OS tem tabela propria com colunas: platform, name, ig_user_id, access_token, followers_count. O codigo em `core/api/main.py` faz token exchange real e obtem `instagram_business_account` via Meta API.

**Risco de split-brain**: OMNIS e Publisher OS mantem registros de conta independentes.

## Diagnostico

### 1. Quais contas existem no OMNIS?
2: @lucastigrereal, @afamiliatigrereal

### 2. Quais contas existem no Publisher OS?
Nao foi possivel verificar sem acesso ao DB. A tabela `social_accounts` existe e e populada dinamicamente pelo fluxo OAuth.

### 3. Existe split-brain?
**Sim, potencial.** OMNIS tem registry estatico (2 contas), Publisher OS tem DB proprio com OAuth real. Nao ha sincronizacao entre eles.

### 4. Fonte canonica nesta fase?
`data/accounts.jsonl` do OMNIS. Publisher OS DB e fonte de execucao, nao de configuracao.

### 5. Campos faltantes no modelo Account do OMNIS?
- `instagram_business_account_id`
- `facebook_page_id`
- Ambos sao `null`/ausentes nas 2 contas existentes

### 6. Conta recomendada para primeiro teste?
**@afamiliatigrereal** (320K, medium risk, conta de familia)

### 7. Contas bloqueadas por risco?
**@lucastigrereal** — critical (690K, autoridade, conta principal)

---

**Fim da auditoria. Prosseguindo para Fase 2.**

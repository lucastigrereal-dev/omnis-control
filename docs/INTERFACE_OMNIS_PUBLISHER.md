# Interface OMNIS Control ↔ Publisher OS

**Data:** 2026-05-08 | **Versao:** 1.0

---

## 1. Papeis

| Sistema | Papel | Repo |
|---|---|---|
| **OMNIS Control** | Control plane — audit, validate, readiness, CLI | omnis-control |
| **Publisher OS** | Execution plane — OAuth, publish, schedule, store | publisher-os |

OMNIS decide. Publisher executa. OMNIS nunca publica direto. Publisher nunca decide.

---

## 2. Endpoints Publisher OS (consumidos pelo OMNIS)

| Metodo | Rota | Status | Uso OMNIS |
|---|---|---|---|
| GET | `/health` | healthy | readiness check |
| GET | `/api/v1/argos/oauth/callback` | dry-run | callback audit |
| GET | `/api/v1/argos/oauth/url` | implementado | gerar URL de autorizacao |
| POST | `/api/v1/argos/oauth/token` | implementado | token exchange |
| GET | `/api/v1/argos/social-accounts` | implementado | listar contas conectadas |
| GET | `/api/v1/argos/publish-status` | implementado | status de publicacao |

---

## 3. Dados de Conta

### OMNIS (`data/accounts.jsonl`)
- Fonte canonica de CONFIGURACAO operacional
- Campos: handle, tags, priority, posting_times, formats, active
- NAO contem tokens ou secrets
- Atualizado manualmente ou via CLI

### Publisher OS (`social_accounts` table)
- Fonte canonica de EXECUCAO
- Campos: platform, name, ig_user_id, access_token, followers_count
- CONTEM tokens reais (apos OAuth)
- Atualizado pelo fluxo OAuth

### Regra de Sincronizacao
- **P1.6A: NAO sincronizar** — risco de vazar token
- **Futuro:** OMNIS consulta `GET /api/v1/argos/social-accounts` como read-only
- **Futuro:** Reconciliacao por handle + platform

---

## 4. Regras de Seguranca

1. OMNIS nunca le valores de token/secret do Publisher OS
2. Publisher OS nunca expoe token em endpoints GET
3. `.env` do Publisher OS e a UNICA fonte de credenciais Meta
4. OMNIS `.env` e apenas para config local dev
5. NENHUM .env e commitado
6. NENHUM token e logado ou impresso

---

## 5. Fluxo OAuth (contrato)

```
1. OMNIS: oauth probe → verifica vars PRESENT
2. OMNIS: oauth validate → confirma readiness
3. Lucas: preenche .env manualmente
4. OMNIS: oauth start → redireciona para Publisher OS
5. Publisher OS: gera URL autorizacao Meta
6. Lucas: autoriza no navegador
7. Meta: redireciona para callback do Publisher OS
8. Publisher OS: recebe code → troca por token → armazena em social_accounts
9. OMNIS: consulta GET /api/v1/argos/social-accounts → confirma conexao
```

---

## 6. Evolucao Futura

- [ ] Publisher OS: endpoint `GET /api/v1/argos/accounts/{handle}/readiness`
- [ ] Publisher OS: endpoint `GET /api/v1/argos/accounts` (lista todas)
- [ ] OMNIS: reconcilia accounts.jsonl ↔ social_accounts
- [ ] OMNIS: comando `oauth sync` para espelhar contas
- [ ] Token rotation automatizada
- [ ] Webhook de token expiry

---

**Fim do contrato de interface.**

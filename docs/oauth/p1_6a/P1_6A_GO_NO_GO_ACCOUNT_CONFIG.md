# P1.6A — GO/NO-GO Account Configuration

**Data:** 2026-05-08

---

## OAuth Real

### NO-GO

Ainda requer acoes humanas:

- `META_APP_SECRET`: **empty** — Lucas precisa preencher
- `META_GRAPH_VERSION`: **missing** — precisa adicionar ao .env
- `INSTAGRAM_BUSINESS_ACCOUNT_ID`: **empty** (alias) — renomear e preencher
- `FACEBOOK_PAGE_ID`: **missing** — recomendado preencher

### O que esta pronto

- Callback route: HTTP 200 (P1.5)
- META_APP_ID: preenchido e valido
- META_REDIRECT_URI: preenchido
- Account readiness model: Pydantic v2 implementado
- CLI `oauth accounts` funcional
- CLI `oauth account-readiness` funcional
- Publisher OS: healthy
- Testes: 788 passando

### Quando sera GO

```
META_APP_SECRET present
META_GRAPH_VERSION present
INSTAGRAM_BUSINESS_ACCOUNT_ID present
Lucas acordado e autorizando
```

---

## Primeiro Post Real

### NO-GO

- OAuth nao esta pronto (dependencia upstream)
- Asset nao atribuido ao slot
- Nenhum slot em conta de baixo risco
- @lucastigrereal bloqueado permanentemente para primeiro teste

### O que esta pronto

- Safe First Post Plan documentado
- @afamiliatigrereal definida como conta candidata
- Asset security criteria definidos
- Post preflight funcional (7/8 passam, 1 aviso)

### Quando sera GO

```
OAuth ready
Slot caption_ready em @afamiliatigrereal
Asset atribuido (organico, seguro)
Lucas revisou e autorizou legenda + midia
Lucas acordado
```

---

## Resumo P1.6A

| Gate | Veredito |
|---|---|
| OAuth Real | NO-GO |
| Post Real | NO-GO |
| Callback Route | GO |
| Account Registry Audit | GO |
| Account Readiness Model | GO |
| CLI Accounts | GO |
| Config Template | GO |
| Interface Contract | GO |
| Safe First Post Plan | GO |
| Split-Brain Doc | GO |

---

## Acoes Lucas (Top 5)

1. `[_]` Pegar `META_APP_SECRET` no Meta Developers
2. `[_]` Adicionar `META_GRAPH_VERSION=v20.0` ao .env
3. `[_]` Renomear `INSTAGRAM_BUSINESS_ID` → `INSTAGRAM_BUSINESS_ACCOUNT_ID` e preencher
4. `[_]` Rodar `python jarvis.py oauth probe` e confirmar PRESENT
5. `[_]` Criar slot para @afamiliatigrereal com asset seguro

---

**Fim do P1.6A. Sem push. Sem OAuth real. Sem post real.**

# META_ENV_VARS — Variáveis de Ambiente Meta/Instagram

Documentação das variáveis necessárias para OAuth Meta no Publisher OS.

---

## Variáveis obrigatórias

| Variável | Descrição | Onde obter |
|---|---|---|
| `META_APP_ID` | ID do aplicativo Meta (Facebook App) | [Meta Developers](https://developers.facebook.com) → Meus Apps → ID do app |
| `META_APP_SECRET` | Secret do aplicativo Meta | Meta Developers → Configurações do App → Básico → Chave secreta |
| `META_REDIRECT_URI` | URL de callback OAuth (ex: `https://seudominio.com/oauth/callback`) | Definida por você nas configurações do app Meta |

## Variáveis opcionais

| Variável | Descrição | Quando precisa |
|---|---|---|
| `META_GRAPH_VERSION` | Versão da Graph API (default: v20.0) | Se Meta atualizar versão mínima |
| `INSTAGRAM_BUSINESS_ACCOUNT_ID` | ID da conta Instagram Business conectada | Após conectar conta via OAuth |
| `FACEBOOK_PAGE_ID` | ID da página Facebook vinculada | Após conectar página via OAuth |
| `META_ACCESS_TOKEN` | Token de acesso gerado pelo fluxo OAuth | Gerado automaticamente após OAuth |

## NUNCA commitar

- Nunca coloque valores reais no `.env.example`
- Nunca comite o arquivo `.env`
- O `.env` já está no `.gitignore`
- Valores reais só existem em `~/publisher-os/.env` local

## Depois de preencher

```bash
omnis oauth readiness          # verifica se está tudo pronto
omnis oauth checklist           # lista os 12 checks
omnis oauth start              # inicia fluxo OAuth (requer Lucas acordado)
```

## Aliases aceitos

O OAuth Readiness também detecta estes nomes alternativos:
- `META_SECRET` (alias para META_APP_SECRET)
- `CALLBACK_URL` (alias para META_REDIRECT_URI)

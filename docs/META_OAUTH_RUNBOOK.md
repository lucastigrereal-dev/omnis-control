# META OAuth RUNBOOK — Instagram Graph API

**Data:** 2026-05-03
**Status:** ⏳ Preparação (não executar sem autorização explícita)
**Fase:** `META-0 — OAuth Readiness & Manual Token Setup`

---

## Visão Geral

Para publicar nos 6 perfis Instagram via OMNIS/ARGOS, é necessário:
1. Um **Facebook App** com permissão `instagram_basic`, `instagram_content_publish`, `pages_read_engagement`
2. **Meta App ID** e **App Secret** configurados
3. **Token de Longa Duração** (60 dias) para cada perfil
4. Um **sistema de refresh** para renovar antes de expirar

---

## Pré-requisitos

| Item | Status | Onde encontrar |
|------|--------|---------------|
| Meta App ID | `1434393165369254` | `config/paths.yaml` ou `.env` |
| Meta App Secret | ⏳ Pendente | `.env` (não lido) |
| Instagram Business Account IDs | ⏳ Pendente | Via Graph API |
| Redirect URI | ⏳ Pendente | `http://localhost:3002/api/auth/callback/instagram` |

---

## Checklist de Preparação (Manual, Seguro)

### 1. Verificar se já existem credenciais
```bash
# Apenas verificar se o arquivo existe — NÃO LER CONTEÚDO
ls -la ~/omnis-control/.env
ls -la ~/omnis-control/.env.local
```

### 2. Configurar variáveis no .env (quando estiver pronto)
```env
META_APP_ID=1434393165369254
META_APP_SECRET=seu_secret_aqui
META_REDIRECT_URI=http://localhost:3002/api/auth/callback/instagram
```

### 3. URL para obter token de curta duração
```
https://api.instagram.com/oauth/authorize
  ?client_id={META_APP_ID}
  &redirect_uri={META_REDIRECT_URI}
  &scope=instagram_basic,instagram_content_publish,pages_read_engagement
  &response_type=code
```

### 4. Trocar código por token
```bash
# Exemplo (NÃO EXECUTAR AGORA)
curl -X POST https://api.instagram.com/oauth/access_token \
  -d client_id={META_APP_ID} \
  -d client_secret={META_APP_SECRET} \
  -d grant_type=authorization_code \
  -d redirect_uri={META_REDIRECT_URI} \
  -d code={CODE_DO_PASSO_ANTERIOR}
```

### 5. Trocar token curto por longo (60 dias)
```bash
# Exemplo (NÃO EXECUTAR AGORA)
curl "https://graph.facebook.com/v19.0/{IG_USER_ID}?access_token={SHORT_TOKEN}&fields=access_token&grant_type=ig_exchange_token"
```

---

## 6 Perfis para Conectar

| Perfil | IG Business ID | Status |
|--------|---------------|--------|
| @lucastigrereal | Pendente | ⏳ |
| @oinatalrn | Pendente | ⏳ |
| @agenteviajabrasil | Pendente | ⏳ |
| @afamiliatigrereal | Pendente | ⏳ |
| @oquecomernatalrn | Pendente | ⏳ |
| @natalaivoueu | Pendente | ⏳ |

---

## Riscos

- Token de curta duração expira em 1 hora — precisa do código rápido.
- Token de longa duração expira em 60 dias — precisa de refresh automático.
- Meta pode revogar token se o App estiver em modo development.
- App precisa estar em **modo live** para usuários não-testadores.
- Cada perfil precisa ser conectado individualmente.

---

## Próximos Passos (Quando Autorizado)

### Fase META-0.1
1. Configurar `META_APP_SECRET` no `.env`
2. Testar conexão com App ID + Secret
3. Obter token de curta duração via browser
4. Trocar por token de longa duração
5. Testar `GET /me/accounts` no Graph API

### Fase META-0.2 (Futura)
1. Conectar cada perfil
2. Armazenar tokens com data de expiração
3. Criar rotina de refresh
4. Validar permissão `instagram_content_publish`

---

## Referências

- [Meta Graph API — Instagram](https://developers.facebook.com/docs/instagram-api/)
- [Long-lived Access Tokens](https://developers.facebook.com/docs/instagram-api/getting-started#long-lived-access-tokens)
- [Content Publishing](https://developers.facebook.com/docs/instagram-api/guides/content-publishing/)

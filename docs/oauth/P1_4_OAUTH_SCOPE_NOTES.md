# P1.4 — OAuth Scope Notes (documentacao)

**Data:** 2026-05-08 | **Nao validado com Meta (sem OAuth real)**

---

## Scopes Esperados

Para publicacao de conteudo no Instagram via Meta Graph API:

| Scope | Necessario para | Obrigatorio |
|---|---|---|
| `instagram_basic` | Ler dados basicos do perfil Instagram | Sim |
| `instagram_content_publish` | Publicar posts/reels/stories | Sim |
| `pages_show_list` | Listar paginas do Facebook vinculadas | Se usar Facebook Page |
| `pages_read_engagement` | Ler metricas de engajamento | Nao (futuro) |
| `instagram_manage_messages` | Responder DMs | Nao (futuro) |
| `business_management` | Gerenciar Business Account | Talvez |

## Fluxo OAuth Esperado

```
1. App → Meta: /oauth/authorize (scopes, redirect_uri, app_id)
2. Meta → Navegador: Tela de login/autorizacao
3. Usuario → Meta: Autoriza scopes
4. Meta → Callback: redirect_uri?code=AUTHORIZATION_CODE
5. App → Meta: /oauth/access_token (code, app_id, app_secret)
6. Meta → App: access_token (short-lived, ~1h)
7. App → Meta: /oauth/access_token (grant_type=fb_exchange_token)
8. Meta → App: access_token (long-lived, ~60 dias)
```

## Verificacao Futura

Quando OAuth estiver funcional, confirmar:
- Quais scopes a Meta exige para o tipo de app "Business Login for Instagram".
- Se o access_token gerado tem permissoes suficientes.
- Se o token long-lived funciona para publicacao sem re-autenticacao.

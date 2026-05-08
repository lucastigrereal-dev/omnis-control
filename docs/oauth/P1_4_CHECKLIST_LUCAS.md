# P1.4 — Checklist para Lucas (acoes humanas)

**Data:** 2026-05-08 | **Imprima e tique conforme completa.**

---

## BLOCO 1 — Credenciais Meta (.env)

- `[_]` 1. Abrir Meta Developers: https://developers.facebook.com/apps/1434393165369254
- `[_]` 2. Copiar `META_APP_SECRET` de App Settings > Basic
- `[_]` 3. Editar `~/publisher-os/.env` e colar em `META_APP_SECRET=...`
- `[_]` 4. Mudar `INSTAGRAM_BUSINESS_ID` para `INSTAGRAM_BUSINESS_ACCOUNT_ID`
- `[_]` 5. Preencher `INSTAGRAM_BUSINESS_ACCOUNT_ID` com o ID real (Meta Business Suite)
- `[_]` 6. Adicionar `META_GRAPH_VERSION=v20.0` no .env
- `[_]` 7. (Opcional) Adicionar `FACEBOOK_PAGE_ID` se necessario
- `[_]` 8. Rodar: `python jarvis.py oauth probe`

**Esperado:** Todas as obrigatorias mostrando `PRESENT`

---

## BLOCO 2 — Validar Infra

- `[_]` 9. Garantir Docker Desktop rodando
- `[_]` 10. Rodar: `python jarvis.py oauth readiness`
- `[_]` 11. Rodar: `python jarvis.py oauth validate`
- `[_]` 12. Verificar que Publisher OS :8000 responde: `python jarvis.py publisher-health`

**Esperado:** Status `ready` ou, se ainda `human_required`, apenas para token (pos-OAuth).

---

## BLOCO 3 — OAuth Real (quando credenciais prontas)

- `[_]` 13. Verificar rota de callback existe no Publisher OS (`/api/v1/argos/oauth/callback`)
- `[_]` 14. Verificar redirect URI na whitelist do Meta App (localhost:8000)
- `[_]` 15. Rodar fluxo OAuth (comando a definir em P1.5)
- `[_]` 16. Autorizar no navegador
- `[_]` 17. Confirmar que `META_ACCESS_TOKEN` foi gerado e armazenado

**Esperado:** Token funcional no .env ou vault.

---

## BLOCO 4 — Preparar Primeiro Post

- `[_]` 18. Revisar draft `1d482d82`: "O Brasil tem lugares que parecem cena de..."
- `[_]` 19. Atribuir asset: `python jarvis.py queue assign 0b79aa1c <asset_id>`
- `[_]` 20. Rodar: `python jarvis.py post package 0b79aa1c`
- `[_]` 21. Revisar pacote completo: legenda, asset, CTA, hashtags
- `[_]` 22. Decidir conta para primeiro teste (sugestao: @afamiliatigrereal, nao @lucastigrereal)

**Esperado:** `ready: true` no PostPackage.

---

## BLOCO 5 — Publicar (quando TUDO pronto)

- `[_]` 23. Confirmar que OAuth esta funcional
- `[_]` 24. Confirmar que Lucas esta acordado e autorizando
- `[_]` 25. Executar comando de publish real (a definir em P1.6)
- `[_]` 26. Verificar post publicado no Instagram
- `[_]` 27. Monitorar primeiros 15min para erros

**LEMBRETE:** NO-GO sem humano acordado. Sempre.

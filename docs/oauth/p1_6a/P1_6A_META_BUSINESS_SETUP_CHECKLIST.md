# P1.6A — Meta Business Setup Checklist

**Data:** 2026-05-08 | **Imprima e tique.**

---

## BLOCO 1 — Escolher conta teste

- [ ] 1. Confirmar conta teste: **@afamiliatigrereal** (320K, familia)
- [ ] 2. Confirmar que NAO e @lucastigrereal (bloqueada)
- [ ] 3. Verificar se @afamiliatigrereal e Instagram Business ou Creator
- [ ] 4. Confirmar que esta vinculada a uma Facebook Page

## BLOCO 2 — Obter IDs da Meta

- [ ] 5. Pegar Facebook Page ID da pagina vinculada
- [ ] 6. Pegar Instagram Business Account ID
- [ ] 7. Anotar ambos em local seguro (fora do repo)

## BLOCO 3 — Meta Developers

- [ ] 8. Entrar em https://developers.facebook.com/apps/1434393165369254
- [ ] 9. Settings > Basic > App Secret — copiar `META_APP_SECRET`
- [ ] 10. Confirmar redirect URI na whitelist:
    `http://localhost:8000/api/v1/argos/oauth/callback`
- [ ] 11. Products > Instagram > Instagram Business Login > Settings
- [ ] 12. Confirmar scopes:
    - `instagram_business_basic`
    - `instagram_business_content_publish`
    - `pages_read_engagement`
    - `pages_show_list`

## BLOCO 4 — Preencher .env do Publisher OS

- [ ] 13. Editar `C:\Users\lucas\publisher-os\.env`
- [ ] 14. `META_APP_SECRET=<valor real>`
- [ ] 15. `META_GRAPH_VERSION=v20.0`
- [ ] 16. Renomear `INSTAGRAM_BUSINESS_ID` → `INSTAGRAM_BUSINESS_ACCOUNT_ID`
- [ ] 17. Preencher `INSTAGRAM_BUSINESS_ACCOUNT_ID=<valor real>`
- [ ] 18. Preencher `FACEBOOK_PAGE_ID=<valor real>`
- [ ] 19. Salvar arquivo

## BLOCO 5 — Validar com OMNIS

- [ ] 20. Rodar: `cd C:\Users\lucas\omnis-control`
- [ ] 21. Rodar: `python jarvis.py oauth probe`
- [ ] 22. Confirmar META_APP_SECRET, META_GRAPH_VERSION, META_APP_ID como PRESENT
- [ ] 23. Rodar: `python jarvis.py oauth validate`
- [ ] 24. Rodar: `python jarvis.py oauth accounts`
- [ ] 25. Rodar: `python jarvis.py oauth account-readiness @afamiliatigrereal`
- [ ] 26. Confirmar `ready_for_oauth: true`

## BLOCO 6 — Testar callback

- [ ] 27. Rodar: `curl "http://localhost:8000/api/v1/argos/oauth/callback"`
- [ ] 28. Confirmar JSON com `"status":"human_required"`
- [ ] 29. Rodar: `curl "http://localhost:8000/api/v1/argos/oauth/callback?code=test_code&state=test"`
- [ ] 30. Confirmar `"code_received":true` e `"token_exchange":"disabled"`

---

**Checklist concluido quando todos os 30 itens estiverem ticados.**

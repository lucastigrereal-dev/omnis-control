# P1.5 — Lucas Meta Setup Checklist

**Data:** 2026-05-08 | **Imprima e tique.**

---

## BLOCO 1 — Meta Developers

- [ ] 1. Entrar em https://developers.facebook.com/apps/1434393165369254
- [ ] 2. Settings > Basic > App Secret
- [ ] 3. Copiar `META_APP_SECRET` (vai precisar da senha do Facebook)
- [ ] 4. Verificar que redirect URI `http://localhost:8000/api/v1/argos/oauth/callback` esta na whitelist
- [ ] 5. Products > Instagram > Instagram Business Login > Settings

---

## BLOCO 2 — .env do Publisher OS

- [ ] 6. Editar `C:\Users\lucas\publisher-os\.env`
- [ ] 7. Colar `META_APP_SECRET=...` (substituir string vazia)
- [ ] 8. Adicionar `META_GRAPH_VERSION=v20.0`
- [ ] 9. Renomear `INSTAGRAM_BUSINESS_ID` para `INSTAGRAM_BUSINESS_ACCOUNT_ID`
- [ ] 10. Preencher `INSTAGRAM_BUSINESS_ACCOUNT_ID` (se souber o ID)
- [ ] 11. (Opcional) Adicionar `FACEBOOK_PAGE_ID`
- [ ] 12. Salvar arquivo

---

## BLOCO 3 — Validar com OMNIS

- [ ] 13. Rodar: `cd C:\Users\lucas\omnis-control`
- [ ] 14. Rodar: `python jarvis.py oauth probe`
- [ ] 15. Confirmar que META_APP_SECRET, META_GRAPH_VERSION e META_APP_ID mostram `PRESENT`
- [ ] 16. Rodar: `python jarvis.py oauth validate`
- [ ] 17. Se mostrar `ready`: fase concluida com sucesso

---

## BLOCO 4 — Testar callback OAuth

- [ ] 18. Rodar: `curl "http://localhost:8000/api/v1/argos/oauth/callback"`
- [ ] 19. Confirmar JSON com `"status":"human_required"` ou `"status":"received_code_dry_run"`
- [ ] 20. Rodar: `curl "http://localhost:8000/api/v1/argos/oauth/callback?code=test_code_123&state=test"`
- [ ] 21. Confirmar `"code_received":true` e `"token_exchange":"disabled"`

---

## Apos OAuth Real (P1.6+)

- [ ] Rodar: `python jarvis.py oauth start`
- [ ] Autorizar no navegador
- [ ] Verificar que `META_ACCESS_TOKEN` foi preenchido
- [ ] Rodar: `python jarvis.py oauth probe`
- [ ] Confirmar todas variaveis como `present`

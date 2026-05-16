# NEXT AFTER GROUP 13 — G14 Setup Note

**Date:** 2026-05-16
**Status:** NOTE ONLY (NAO EXECUTAR)

---

## 1. Gatilho

O prompt mestre `PROMPT_MESTRE_OMNIS_SUPREME.md` (raiz do repo) so deve ser executado apos:
- Fechamento completo de W128, W129 e W130
- Suite completa verde (6955+ testes PASS)
- Commit final do Grupo 13 registrado
- `docs/supreme_210/OMNIS_SUPREME_210_WAVES_PROGRESS.md` atualizado com Grupo 13 = 10/10

## 2. O que o prompt mestre prepara

- **G14 App Factory (W131-W140):** PRD → schema → API → frontend → auth → migration → config → test → package → E2E
- **G14 Content Intelligence (W211-W240):** Expansao futura (reservada, nao detalhar ainda)

## 3. Regra de ouro: auditar antes de executar

Antes de rodar qualquer bloco do prompt mestre:
1. `git status` — confirmar working tree limpo
2. `git log --oneline -5` — confirmar commits do Grupo 13
3. `python -m pytest tests/ --import-mode=importlib -p no:warnings -q` — confirmar suite verde
4. Confirmar `OMNIS_SUPREME_210_WAVES_PROGRESS.md` mostra Grupo 13 = 10/10

**Se o estado real divergir do esperado → seguir o estado real e reportar.**

## 4. Proximo passo atual

Conforme progresso registrado:
- W128+W129: COMPLETE (commit fcd5de0)
- W130: COMPLETE (commit cc149a0)
- Grupo 13: 10/10 FINALIZADO

Se auditoria confirmar o acima → G14 App Factory (W131) e o proximo passo natural.
Se auditoria encontrar divergencia → resolver antes de avancar.

## 5. O que NAO fazer agora

- NAO executar W131
- NAO alterar CLAUDE.md
- NAO criar `.claude/rules` novos
- NAO modificar governanca existente

Apenas registrar esta nota. A execucao real ocorre em sessao futura com autorizacao explicita.

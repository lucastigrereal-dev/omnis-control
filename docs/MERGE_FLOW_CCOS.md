# OMNIS â€” Merge Flow CCOS

Merge Ã© gate, nÃ£o atalho.

## Antes do merge
1. Ver branch.
2. Rodar testes do mÃ³dulo.
3. Rodar suite completa.
4. Rodar scan de secrets/chamadas reais.
5. Confirmar handoff report em docs/.
6. Gerar QA report.
7. Pedir aprovaÃ§Ã£o explÃ­cita de Lucas.

## Comandos de QA
```powershell
git log --oneline -5
python -m pytest tests/ --import-mode=importlib -p no:warnings -q
grep -r "secret\|token=\|api_key=\|password=\|OAuthReal\|publish_real\|send_real\|deploy_real" src/ --include="*.py"
git diff --name-only master HEAD
```

## Preview obrigatÃ³rio
```powershell
git checkout master
git merge --no-commit --no-ff feat/<branch>
git merge --abort
```

## Merge real somente apÃ³s aprovaÃ§Ã£o
```powershell
git merge --no-ff feat/<branch> -m "feat(P<N>): <descriÃ§Ã£o>"
python -m pytest tests/ --import-mode=importlib -p no:warnings -q
```

## Se falhar
```powershell
git revert HEAD --no-edit
```

## Nunca fazer
- git push --force
- git reset --hard
- git clean -fd
- merge sem suite verde
- push sem autorizaÃ§Ã£o explÃ­cita de Lucas

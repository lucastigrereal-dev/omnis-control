# OMNIS Runbook

## Iniciar Sessão
1. Confirmar diretório: `pwd` → deve ser `C:\Users\lucas\omnis-control`
2. `git branch --show-current` → confirmar branch esperada
3. `git status --short` → classificar working tree
4. Ler `docs/project-os/CURRENT_STATE.md`
5. Ler `docs/project-os/WAVE_REGISTRY.md`
6. Decidir: continuar wave ativa ou /omnis-next

## Executar Wave
1. Preflight: branch correta? working tree limpo? roadmap ativo claro?
2. Scope lock: quais arquivos esta wave toca?
3. Implementar: mínimo necessário, dry-run primeiro
4. Testes focados: `python -m pytest tests/<module>/ --import-mode=importlib -p no:warnings -v`
5. Report: o que foi feito, testes, diff
6. Commit seletivo: `git add <specific files>`
7. Atualizar state: wave registry, current state

## Fechar Wave
1. Confirmar todos os blocos concluídos
2. Rodar testes do módulo
3. Rodar `python scripts/omnis_state_check.py`
4. Atualizar `docs/project-os/WAVE_REGISTRY.md`
5. Atualizar `docs/project-os/CURRENT_STATE.md`
6. Atualizar `.claude/state/wave-registry.json`
7. Commit: `feat(scope): close W<NNN> — <name>`

## Fechar Sprint/Grupo
1. Verificar todas as waves do grupo concluídas
2. Rodar suite completa
3. Atualizar `docs/project-os/ROADMAP.md`
4. Gerar handoff em `.claude/state/last-handoff.md`
5. Commit: `chore(omnis): close G<NN> — <group name>`

## Commit Seguro
1. `git status --short`
2. `git diff --stat`
3. Testes do domínio passam
4. Stage seletivo: `git add <file1> <file2> ...`
5. Verificar staged: `git diff --cached --stat`
6. Nenhum segredo, .env, path KRATOS
7. Commit com mensagem convencional

## Parar Sessão
1. Atualizar `.claude/state/last-handoff.md`
2. `git status --short` final
3. Reportar working tree status

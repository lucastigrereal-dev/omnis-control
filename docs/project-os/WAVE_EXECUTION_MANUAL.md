# OMNIS Wave Execution Manual

## Ciclo de Wave (10 passos)

### 1. Preflight
- `git status --short` — working tree classificado?
- `git branch --show-current` — branch correta?
- Roadmap ativo confirmado?

### 2. Ler Registry
- `docs/project-os/WAVE_REGISTRY.md` — wave já não está DONE?
- `docs/project-os/CURRENT_STATE.md` — não há blocker?

### 3. Scope Lock
- Quais arquivos serão criados/modificados?
- NÃO tocar: KRATOS, outros domínios, secrets

### 4. Implementar Mínimo
- dry_run=True como default
- Mock-first para externos
- Código mínimo necessário

### 5. Testes Focados
- `python -m pytest tests/<module>/ --import-mode=importlib -p no:warnings -v`
- Testes do módulo devem passar

### 6. Full Suite (se aplicável)
- `python -m pytest tests/ --import-mode=importlib -p no:warnings -q`
- Classificar falhas (pré-existente vs nova)

### 7. Report
- O que foi implementado
- Testes: X passed
- Diff stat

### 8. Commit Seletivo
- `git add <specific files>`
- `git diff --cached --stat` — revisar
- Commit com mensagem convencional

### 9. Atualizar State
- `docs/project-os/WAVE_REGISTRY.md` — marcar DONE + commit hash
- `docs/project-os/CURRENT_STATE.md` — atualizar
- `.claude/state/wave-registry.json` — atualizar

### 10. Próxima Wave
- Identificar próxima wave no registry
- Ou /omnis-next para decidir

## Stop Rules
- Teste novo quebrando
- Conflito de merge
- P0 detectado
- Escopo incerto

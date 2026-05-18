# OMNIS Continue Wave Prompt

```md
Você está no projeto OMNIS CONTROL.

Sua missão: continuar a wave atual sem perguntar, dentro do escopo definido.

## Pre-execução
1. Leia `CLAUDE.md` e todos os YAMLs do Project OS
2. Rode `git status --short` e `git branch --show-current`
3. Confirme que a wave atual NÃO está DONE/REVIEW no `omnis_wave_registry.yaml`
4. Confirme que o worktree atual cobre o escopo da wave

## Execução
- Execute os blocos restantes da wave
- dry_run=True como padrão universal
- Mock-first para qualquer integração externa

## Validação
- Rode testes específicos do módulo
- Rode `git diff --stat` para revisar escopo

## Commit
- Stage seletivo: apenas arquivos da wave
- Commit message: feat(domínio): descrição clara
- NUNCA `git add .`

## Pós-commit
- Atualize `omnis_wave_registry.yaml` com status DONE e commit hash
- Atualize `omnis_state.yaml` se estado mudou

Se encontrar P0 ou bloqueador real: PARE e reporte.
```

# docs-scribe

## Função
Mantém documentação do Project OS atualizada e consistente.

## Quando chamar
- Após qualquer wave concluída
- Após merge
- Quando estado do repo muda

## Pode tocar
- docs/project-os/*
- .claude/state/*
- omnis_*.yaml (raiz)

## Não pode tocar
- Código fonte
- KRATOS
- README.md (sem autorização)

## Output
Documentação atualizada: CURRENT_STATE.md, WAVE_REGISTRY.md, ROADMAP.md, ACTIVE_WORKTREES.md, GUARDRAILS.md.

## Stop rules
- Inconsistência entre docs e realidade → corrigir antes de escrever
- Mudança estrutural → pedir confirmação

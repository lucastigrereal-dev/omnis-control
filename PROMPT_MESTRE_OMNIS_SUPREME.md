# PROMPT MESTRE — OMNIS CONTROL

Você está no projeto OMNIS CONTROL.

Antes de executar qualquer ação:

1. Leia CLAUDE.md.
2. Leia:
   - omnis.project.yaml
   - omnis_state.yaml
   - omnis_wave_registry.yaml
   - omnis_worktrees.yaml
   - omnis_blocked_items.yaml
   - omnis_guardrails.yaml
3. Leia:
   - docs/OMNIS_GUARDRAILS.md
   - docs/OMNIS_CLAUDE_RUNBOOK.md
   - docs/OMNIS_NEXT_ACTIONS.md
4. Rode:
   - git status --short
   - git branch --show-current
   - git log -1 --oneline

Depois:

1. Identifique a branch/worktree atual.
2. Identifique o escopo permitido.
3. Identifique P0/P1 abertos.
4. Identifique se a próxima ação pode ser executada nesta branch.
5. Não execute se houver risco de duplicação.
6. Não execute se houver P0 bloqueando.

Regras:
- Não faça push.
- Não exponha segredo.
- Não use git add .
- Use staging seletivo.
- Não apague sem dry-run.
- Não duplique waves.
- Atualize YAMLs de estado ao concluir waves.
- Pare em bloqueador real.

Se seguro:
Execute a próxima ação segura de maior prioridade.

Se não seguro:
Entregue relatório de bloqueador.

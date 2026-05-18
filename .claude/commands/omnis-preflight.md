# /omnis-preflight

Preflight check antes de qualquer ação.

## Ações
1. `git status --short` — classificar cada arquivo
2. `git branch --show-current` — branch correta?
3. Verificar `omnis_blocked_items.yaml` — P0 blockers?
4. Verificar `omnis_guardrails.yaml` — ação permitida?
5. Confirmar roadmap ativo em ROADMAP.md
6. Verificar se working tree está classificado (sem arquivos órfãos)

## Output
```
PREFLIGHT — {{DATE}}
Branch: {{BRANCH}} ✅/⚠️
Working tree: {{CLEAN/DIRTY}} ({{CLASSIFICATION}})
Roadmap ativo: {{ROADMAP}} ✅/⚠️
P0: {{COUNT}} ⚠️
Ação segura: {{YES/NO}}
```

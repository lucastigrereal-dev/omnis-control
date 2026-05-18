# OMNIS Error Playbook

| Erro | Severidade | Sinal Técnico | Skill | Deve Parar? | Ação |
|---|---|---|---|---|---|
| Terminal fechou | LOW | Sessão perdida | context-restorer | NÃO | Retomar com `--resume` ou `--continue` |
| Branch errada | HIGH | `git branch` não bate com worktree | git-guardian | SIM | Trocar para branch correta. Não commitar. |
| Segredo encontrado | **P0** | Padrão `sk-`, `api_key`, `token` em arquivo | secret-handler | SIM | Não imprimir. Registrar em blocked_items. Externalizar. |
| Suite falhou | HIGH | `pytest` exit code != 0 | tester | SIM | Verificar se falha é pré-existente. Se nova: corrigir antes de commit. |
| Falha pré-existente | LOW | Mesmo teste que `known_pre_existing_failures` | runtime-auditor | NÃO | Documentar como fora do escopo. Prosseguir. |
| Merge conflict | HIGH | `git merge` reporta conflito | merge-gate | SIM | Resolver conflito. Não forçar merge. |
| Wave duplicada | HIGH | Wave já DONE/REVIEW no registry | git-guardian | SIM | Pausar. Reportar duplicação. Atualizar registry se necessário. |
| Logs untracked | MEDIUM | `reports/ccos/*.log` em `git status` | maintenance-auditor | NÃO | Verificar .gitignore. Decidir política. |
| Paths suspeitos | MEDIUM | Caminhos com caracteres inválidos (CUsers) | maintenance-auditor | NÃO | Auditar. Corrigir encoding. Não apagar sem dry-run. |
| P0 aberto | **P0** | `omnis_blocked_items.yaml` tem P0 `open` | secret-handler | SIM | Resolver P0 antes de novo trabalho. |

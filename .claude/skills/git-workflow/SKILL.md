---
name: git-workflow
description: Workflow Git padrão do OMNIS — commits, branches, PRs, merge gates
version: 1.0.0
tags: [git, workflow, governance, omnis]
---

## Git Workflow OMNIS

**Padrão de branches:**
- `main` → produção, protegida
- `feat/nome-curto` → features
- `fix/nome-curto` → correções
- `wave/W-N` → ondas de desenvolvimento

**Commits (Conventional Commits obrigatório):**
- `feat:` nova funcionalidade
- `fix:` correção de bug
- `chore:` manutenção
- `docs:` documentação
- `test:` testes

**Antes de qualquer commit:**
1. `git status` — verificar arquivos modificados
2. `git diff` — revisar mudanças
3. Nunca commitar arquivos `.env`, secrets, ou dumps de DB
4. Rodar lint e testes se disponíveis

**PRs:** abrir via GitHub MCP, incluir descrição do que muda e referência ao wave/sprint.
**Merge gate:** só mergear em `main` após CI verde e ao menos 1 review.

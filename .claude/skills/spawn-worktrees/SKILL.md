---
name: spawn-worktrees
description: Criar plano seguro de worktrees paralelas.
---

# spawn-worktrees

## Objetivo
Preparar worktrees sem colisÃ£o.

## Processo
1. Validar branch atual.
2. Rodar `git status`.
3. Listar worktrees existentes.
4. Criar apenas worktrees aprovados.
5. Sincronizar `.claude/` com `scripts/omnis-sync-claude.ps1`.

## Regra
NÃ£o criar worktree para Ã©pico dependente antes do gate anterior.

# OMNIS Daily Operation

## Comandos do Dia-a-Dia

```sh
# Estado completo do OMNIS
/omnis-status

# Próxima ação segura
/omnis-next

# Status de waves e grupos
/omnis-wave-status

# Triagem de erro
/omnis-error

# Fechar wave concluída
/omnis-close-wave

# Auditoria completa
/omnis-audit

# Verificar worktrees
/omnis-worktree-status

# Antes de qualquer commit
/omnis-safe-commit

# Release candidate local
/omnis-rc
```

## Fluxo Típico de Sessão

1. Abre Claude Code no repo OMNIS
2. `/omnis-status` — vê estado atual
3. `/omnis-next` — recebe próxima ação
4. Executa a ação (wave, fix, audit)
5. `/omnis-safe-commit` — commit seletivo
6. `/omnis-close-wave` — se concluiu wave
7. Atualiza handoff

## Anti-Padrões

- NÃO digitar `git add .` nunca
- NÃO começar a codar sem `/omnis-status`
- NÃO assumir qual roadmap está ativo
- NÃO tocar em KRATOS

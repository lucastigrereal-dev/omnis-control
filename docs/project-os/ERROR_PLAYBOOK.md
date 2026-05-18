# OMNIS Error Playbook

| Sintoma | Causa Provável | Diagnóstico | Comandos Seguros | Proibido | Quando Parar | Quando Pedir Lucas |
|---|---|---|---|---|---|---|
| Terminal fechou | Sessão expirou | Perdeu contexto | `--resume` ou `--continue` | Recomeçar do zero | Não | Se não achar session ID |
| Diretório errado | Em C:\Users\lucas | `pwd` não é omnis-control | `cd C:\Users\lucas\omnis-control` | Executar comandos ali | Sim | Se não souber voltar |
| Confundiu OMNIS/KRATOS | Contexto ambíguo | Leu kratos-mission-control | Reler PROJECT_OS.md | Tocar KRATOS | Sim | Se já mexeu em KRATOS |
| Branch errada | Worktree trocado | `git branch` não bate | `git branch --show-current` | Commit na branch errada | Sim | Se não sabe qual branch |
| Working tree sujo | Arquivos não commitados | `git status --short` tem M ou ?? | Classificar arquivos | `git add .` ou `git reset --hard` | Apenas se não classificado | Se arquivos misteriosos |
| .claude nested | Setup duplicado | `ls .claude/.claude` existe | Reportar | Apagar sem confirmação | Não | Para decidir qual manter |
| Stale worktrees | Worktree antigo | `git worktree list` mostra paths velhos | Listar no ACTIVE_WORKTREES.md | `git worktree remove` | Não | Para autorizar remoção |
| Roadmap conflitante | G14 + CCOS ativos | WAVE_REGISTRY mostra ambos | Reportar conflito | Executar qualquer wave | Sim | Para decidir prioridade |
| Plano de wave não encontrado | Wave não documentada | Arquivo de plano ausente | Ver WAVE_REGISTRY | Inventar plano | Sim | Para definir escopo |
| pytest falhou | Teste quebrado | `pytest` exit != 0 | Ver se é pré-existente | Commit mesmo assim | Se falha nova | Se não souber causa |
| Import quebrado | Dependência ausente | `ModuleNotFoundError` | `pip list`, verificar venv | Instalar globalmente | Se for external dep | Se duvida do venv |
| Dependency missing | package não instalado | ImportError | Verificar requirements.txt | Instalar sem venv | Não | Se for sistema |
| Test count mudou | Testes adicionados/removidos | Número ≠ esperado | Contar testes, auditar | Ignorar | Se caiu muito | Se não sabe causa |
| Commit misturado | git add . usado | Muitos arquivos staged | `git reset HEAD` (soft) | `git reset --hard` | Se misturado com segredo | Para decidir o que sai |
| git index.lock | Outro git rodando | `.git/index.lock` existe | Esperar ou `rm .git/index.lock` | Forçar sem verificar | Se lock persistir | Se não tem certeza |
| EPERM Windows | Processo segurando arquivo | PermissionError | Fechar apps, esperar | Forçar deleção | Se arquivo crítico | Se não resolver |
| Secrets detectados | Padrão de secret em diff | `sk-`, `api_key`, `token` no diff | NÃO IMPRIMIR. Registrar P0. | Commit, push, deploy | SIM | Para decidir externalização |
| Claude pediu auth | Gate de segurança | Claude bloqueou ação | Ver se ação é permitida no authority model | Burlar o gate | Se ação requer Lucas | Se authority model não cobre |
| Claude parou no meio | Bloqueador ou timeout | Tarefa incompleta | Ver last-handoff.md | Recomeçar do zero | Depende do bloqueador | Se bloqueador real |

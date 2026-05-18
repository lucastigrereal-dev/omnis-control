# OMNIS Skill Routing Manual

## Skills e Agentes Recomendados

| Skill/Agente | Função | Quando Usar | Inputs | Outputs | Risco |
|---|---|---|---|---|---|
| **explorer** | Busca e navegação no codebase | "Onde está X?", "Quais arquivos tocam Y?" | Padrão de busca, domínio | Lista de arquivos, locais | LOW |
| **architect** | Design de arquitetura | Nova feature, refactor grande | Requisitos, constraints | Plano de implementação | MEDIUM |
| **reviewer** | Code review | Antes de merge, após implementação | Diff, arquivos alterados | Lista de issues por severidade | LOW |
| **tester** | Execução e análise de testes | Suite quebrou, nova feature | Módulo alvo | Resultados, diagnóstico | LOW |
| **git-guardian** | Segurança Git | Antes de commit, depois de mudanças | git status, diff | Bloqueios, alertas | LOW |
| **secret-scanner** | Detecção de segredos | Auditoria de segurança, pré-commit | Arquivos de config | Alertas de segredo (sem valor) | LOW |
| **wave-registry-updater** | Atualização de YAMLs | Após concluir wave | ID da wave, status, commit | YAMLs atualizados | LOW |
| **merge-gate** | Gate de merge | Antes de mergear branch | Branch source, target | GO/NO-GO, blockers | MEDIUM |
| **doc-keeper** | Manutenção de docs | Docs desatualizados, nova feature | Domínio, mudanças | Docs atualizados | LOW |
| **runtime-auditor** | Auditoria de Runtime | Verificar estado de missions/events/logs | Módulo first_missions | Relatório de saúde | LOW |
| **health-bridge-auditor** | Auditoria de Health Bridge | Verificar /health, servidor HTTP | health_bridge module | Relatório de saúde | LOW |
| **app-factory-planner** | Planejamento AppFactory | Nova ideia de app, PRD | Briefing, ideia | PRD, schema plan | MEDIUM |
| **maintenance-auditor** | Auditoria de manutenção | Limpeza, paths, reports | Alvo da auditoria | Relatório + recomendações | MEDIUM |
| **worktree-manager** | Gestão de worktrees | Criar/remover/auditar worktrees | Comando, worktree ID | Worktree criado/removido | MEDIUM |

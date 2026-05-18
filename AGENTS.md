# OMNIS Control — Agent Registry

## omnis-orchestrator
- **Função:** Coordenação geral, decide roadmap ativo, consulta state, evita confusão OMNIS/KRATOS
- **Quando chamar:** Início de sessão, decisão de roadmap, conflito entre frentes
- **Pode tocar:** CLAUDE.md, docs/project-os/, .claude/state/
- **Não pode tocar:** src/, tests/, KRATOS
- **Output:** Decisão de próximo passo, state atualizado

## wave-runner
- **Função:** Executar waves sequenciais respeitando WAVE_REGISTRY e gates
- **Quando chamar:** /omnis-next indicar próxima wave, continuação de sprint
- **Pode tocar:** src/ do módulo da wave, tests/ do módulo
- **Não pode tocar:** KRATOS, AppFactory se wave for CCOS, CCOS se wave for AppFactory
- **Output:** Wave concluída com testes, commit, state atualizado
- **Stop rules:** Teste novo quebrado, conflito, P0 detectado

## app-factory-architect
- **Função:** G14 App Factory W131-W140 — modelos, PRD, DB schema, API contract
- **Quando chamar:** Waves App Factory (W133-W140)
- **Pode tocar:** src/app_factory/, tests/app_factory/, docs/app_factory/
- **Não pode tocar:** Runtime, CCOS, Health, KRATOS
- **Output:** Artefatos da wave App Factory

## db-schema-planner
- **Função:** W133 — data models, schema planning
- **Quando chamar:** W133 especificamente
- **Pode tocar:** src/app_factory/schema*, tests/app_factory/test_schema*
- **Não pode tocar:** API, frontend, runtime
- **Output:** Schema YAML/JSON, validação, testes

## api-contract-guardian
- **Função:** Contratos, schemas, validações de compatibilidade
- **Quando chamar:** W134, alterações de API
- **Pode tocar:** src/app_factory/api*, tests/app_factory/test_api*
- **Não pode tocar:** DB schema, frontend
- **Output:** Contrato validado, testes de contrato

## cli-guardian
- **Função:** Comandos CLI — `omnis idea`, `omnis idea plan`, typer apps
- **Quando chamar:** Qualquer wave que crie/modifique CLI
- **Pode tocar:** src/cli_commands/, src/routers/
- **Não pode tocar:** Lógica de negócio, models
- **Output:** CLI testada, help texts, dry-run

## runtime-bridge-guardian
- **Função:** CCOS RuntimeBridge — não misturar com G14
- **Quando chamar:** Se CCOS/P37 for o roadmap ativo
- **Pode tocar:** src/runtime_bridge/ (se existir)
- **Não pode tocar:** App Factory, Health
- **Output:** Runtime bridge operacional
- **Stop rules:** Se G14 também ativo, parar e pedir decisão do Lucas

## test-guardian
- **Função:** Suite, regressão, pytest, contagem de testes
- **Quando chamar:** Antes de commit, depois de merge, /omnis-rc
- **Pode tocar:** tests/ (rodar, não modificar sem wave)
- **Não pode tocar:** src/
- **Output:** Relatório de testes, falhas classificadas

## git-guardian
- **Função:** Branch, worktree, staged diff, safe commit
- **Quando chamar:** Antes de qualquer commit, /omnis-merge-check
- **Pode tocar:** Staging area (seletivo)
- **Não pode tocar:** .git/config, hooks existentes
- **Output:** Staging seguro, commit message, verificação pós-commit

## docs-scribe
- **Função:** State, handoff, reports, documentação
- **Quando chamar:** Após wave, sprint, ou mudança de estado
- **Pode tocar:** docs/project-os/, .claude/state/
- **Não pode tocar:** src/, tests/
- **Output:** Docs atualizados, handoff, state JSON

## release-auditor
- **Função:** RC local, readiness, bloqueios finais
- **Quando chamar:** /omnis-rc, antes de propor merge ao Lucas
- **Pode tocar:** docs/project-os/RELEASE_CANDIDATE_CHECKLIST.md
- **Não pode tocar:** src/, tests/
- **Output:** GO/NO-GO, lista de blockers, RC report

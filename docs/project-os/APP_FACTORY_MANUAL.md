# OMNIS App Factory Manual (G14)

## Waves

### W131 — app-idea-intake
- **Objetivo:** Sistema de entrada de ideias de app
- **Artefatos:** IdeaStore, AppIdea model, validation, dry_run
- **CLI:** `omnis idea`
- **Status:** DONE

### W132 — app-prd-generator
- **Objetivo:** Gerador de PRD automatizado
- **Artefatos:** PRD generator, `omnis idea plan <id>`
- **Commit:** d6f61e6
- **Status:** DONE

### W133 — app-db-schema-planner
- **Objetivo:** Planejador de schema de banco
- **Artefatos:** Schema planner command, data models
- **Tests:** tests/app_factory/test_schema*
- **Status:** DONE (em master, parte de W133-W162)

### W134 — app-api-contract
- **Objetivo:** Construtor de contrato de API
- **Artefatos:** API contract planner, validações
- **Status:** DONE (em master)

### W135 — app-frontend-plan
- **Objetivo:** Plano de frontend
- **Status:** DONE (em master)

### W136 — app-test-plan
- **Objetivo:** Plano de testes automatizado
- **Status:** DONE (em master)

### W137 — app-repo-scaffold
- **Objetivo:** Scaffold de repositório
- **Status:** DONE (em master)

### W138 — app-openhands-mock
- **Objetivo:** Mock do adaptador OpenHands
- **Status:** DONE (em master)

### W139 — app-package-export
- **Objetivo:** Export de pacote de app
- **Status:** DONE (em master)

### W140 — app-factory-e2e
- **Objetivo:** E2E da fábrica de apps
- **Tests:** Pipeline completo com mock adapters
- **Status:** DONE (em master)

## W133-W162 Advanced
- **Status:** DONE — concluído em master (commit 06caa49)
- Worktree omnis-appfactory está em master com o resultado final
- Não requer ação adicional

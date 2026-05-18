# OMNIS Skill Matrix

| Skill | Quando Usar | Arquivos Permitidos | Arquivos Proibidos | Output |
|---|---|---|---|---|
| omnis-orchestration | Sessão nova, decisão de roadmap | docs/project-os/, .claude/state/ | src/, tests/ | Próximo passo |
| omnis-wave-runner | /omnis-next indicar wave | src/<wave>/ e tests/<wave>/ | Outros domínios | Wave done + commit |
| omnis-app-factory | G14 waves W131-W140 | src/app_factory/, tests/app_factory/ | Runtime, CCOS, Health | Artefato App Factory |
| omnis-db-schema | W133 schema planning | src/app_factory/schema* | API, frontend | Schema + testes |
| omnis-api-contract | W134 API contracts | src/app_factory/api* | DB schema | Contrato validado |
| omnis-cli | Comandos typer | src/cli_commands/, src/routers/ | Lógica core | CLI testada |
| omnis-runtime-bridge | CCOS RuntimeBridge | src/runtime_bridge/ | App Factory | Bridge operacional |
| omnis-test-guardian | Pré-commit, merge check | tests/ (rodar) | src/ | Relatório de testes |
| omnis-git-safety | Antes de commit | Staging area | .git/config | Commit seguro |
| omnis-docs-release | Pós-wave, pós-sprint | docs/project-os/, .claude/state/ | src/, tests/ | Docs + state JSON |

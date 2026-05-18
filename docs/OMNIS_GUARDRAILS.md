# OMNIS Guardrails

**Fonte machine-readable:** `omnis_guardrails.yaml`

## Git

- **Nunca fazer push** sem autorização humana explícita
- **Nunca usar `git add .`** — sempre staging seletivo
- **Sempre verificar `git status`** antes de commit
- **Sempre verificar `git diff --stat`** antes de commit

## Segurança

- **Nunca imprimir segredo** no chat, log, ou tela
- **Nunca commitar segredo** — usar env var
- **Padrões de alto risco:** `api_key`, `secret`, `token`, `sk-`, `AKIA`
- **Arquivos de alto risco:** `.env`, `config/*.yaml`, `config/*.json`, `reports/**/*.log`

## Execução

- **Nunca apagar sem dry-run** — simular antes de destruir
- **Nunca executar ação destrutiva** sem autorização humana
- **Sempre dry-run para scaffold** — gerar estrutura antes de popular

## Waves

- **Nunca duplicar wave** — verificar registry antes de executar
- **Sempre atualizar registry** ao concluir wave
- **Sempre auditar duplicação** se trabalhando em paralelo

## Testes

- **Sempre rodar testes do domínio** antes de commit
- **Falha pré-existente permitida:** `test_cli_graph_run_list` (execution_graph)

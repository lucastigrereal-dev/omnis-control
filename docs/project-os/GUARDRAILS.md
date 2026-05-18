# OMNIS Guardrails

## Proibido (nunca)
- Push, deploy, ler .env, .env.*, secrets/
- `git add .`, `git reset --hard`, `git clean -fd`
- `rm -rf`, `Remove-Item -Recurse`
- Tocar KRATOS ou kratos-mission-control
- Executar em C:\Users\lucas (fora do repo)
- Commitar secrets, tokens, keys
- Apagar worktrees sem autorização
- Recomeçar do zero

## Permitido (sempre)
- dry_run=True como default universal
- Staging seletivo (arquivos específicos)
- Rodar testes, build suite
- Criar/atualizar docs de estado
- Commit seletivo com gates passando
- Classificar working tree sujo

## Precisa Autorização
- Push, deploy
- Remover worktree
- Mudar roadmap ativo
- Resolver conflito semântico grande
- Abandonar Supreme 210 ou CCOS
- Mesclar roadmaps
- Ler/copiar secrets

## Git Policy
- Antes de commit: `git status`, `git diff --stat`, testes do domínio
- Staging: `git add <file1> <file2>` (NUNCA `git add .`)
- Commit message: conventional commits
- Bloquear .env, secrets, paths KRATOS

## Secrets Policy
- Nunca ler, imprimir, copiar
- Encontrou: registrar localização (sem valor), adicionar P0, substituir por env var
- Padrões: `sk-`, `api_key`, `secret`, `token`, `password`, `AKIA`, `master key`

## OMNIS/KRATOS Boundary
- OMNIS NUNCA altera arquivos em C:\Users\lucas\kratos-mission-control
- OMNIS NUNCA referencia KRATOS como parte do seu escopo
- Se confundir: parar e verificar PROJECT_OS.md

## Roadmap Conflict Policy
- Se G14 App Factory e CCOS ambos parecerem ativos: PARAR
- Pedir ao Lucas qual roadmap seguir
- Não tentar mesclar automaticamente

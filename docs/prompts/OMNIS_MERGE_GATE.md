# OMNIS Merge Gate Prompt

```md
Você está no projeto OMNIS CONTROL.

Sua missão: avaliar se esta branch pode ser mergeada com segurança.

## Checklist
1. `git status` — working tree limpo no escopo da branch?
2. `git log --oneline` — commits contam história clara?
3. `git diff --stat <base>...HEAD` — apenas arquivos do domínio?
4. Testes do domínio passam?
5. `omnis_blocked_items.yaml` — algum P0 aberto bloqueia?
6. Nenhum segredo nos diffs?

## Scan de Segurança
- grep por `sk-`, `api_key`, `secret`, `token`, `password`, `AKIA` nos diffs
- Verificar arquivos de alto risco (`config/*.yaml`, `.env`)
- Se encontrado: NÃO imprimir valor. Reportar localização.

## Veredito
- **GO** — todos os gates passaram
- **NO-GO** — blockers listados abaixo
- **CONDITIONAL** — passar após resolver [X]

## Bloqueadores Encontrados
[Lista ou "Nenhum"]

## Ordem de Merge Recomendada
Baseado em `omnis_worktrees.yaml` e `omnis_wave_registry.yaml`.
```

# OMNIS Merge Protocol

## Pre-merge Checklist

1. `git status` limpo no escopo da branch
2. `git log --oneline` revisado — commits contam história clara
3. `git diff --stat <base>...HEAD` — arquivos alterados dentro do escopo
4. Testes do domínio passam
5. Nenhum segredo nos diffs
6. Nenhum P0 aberto em `omnis_blocked_items.yaml`

## Ordem Recomendada de Merge

```
1. Resolver P0 (segredo) ← BLOQUEIA TUDO
       ↓
2. Principal Runtime/Health (feature/omnis-5waves-runtime-supreme)
       ↓
3. Maintenance (feature/omnis-maintenance-w201-w205)
       ↓
4. Health separada (se tiver valor adicional)
       ↓
5. AppFactory (feature/omnis-appfactory-w133-w162)
       ↓
6. Templates (feature/omnis-templates-w206-w215)
```

## Regras

- **Nunca mergear com P0 aberto**
- **Nunca forçar merge** (`--no-ff` é ok, `--force` não)
- **Sempre `--ff-only`** quando possível
- Se houver conflito: resolver manualmente, não forçar
- Após cada merge: rodar suite completa
- Após merge final: atualizar todos os YAMLs de estado

## Safety Tags

Criar tag de segurança antes de iniciar merge wave:
```sh
git tag safety/pre-merge-$(date +%Y%m%d-%H%M)
```

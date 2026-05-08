# P1.4 — Working Tree Dirty Files Report

**Data:** 2026-05-08 | **Branch:** master

---

## Arquivos Modificados (3)

| Arquivo | Tipo | Classificacao |
|---|---|---|
| `config/paths.yaml` | Config | Snapshot de config — 1 linha alterada |
| `docs/ESTADO_ATUAL_RESUMIDO.md` | Doc | 83 linhas alteradas — snapshot de estado |
| `docs/disk_audit_report.json` | Data | 58 linhas alteradas — JSON runtime |

## Decisao

**NAO COMMITAR** estes arquivos junto com o codigo P1.4.

Motivo:
- Sao snapshots de runtime/estado, nao parte da implementacao P1.4.
- `paths.yaml` pode conter paths locais especificos.
- `disk_audit_report.json` e gerado automaticamente.

## Recomendacao

1. Commitar em separado como `docs(snapshot): update state and disk audit` se necessario.
2. Ou descartar com `git checkout -- <file>` se forem apenas ruido.
3. Ou adicionar ao `.gitignore` se forem artefatos regeneraveis.

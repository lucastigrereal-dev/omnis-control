# W131 — app-idea-intake: PLANO DE EXECUCAO

**Date:** 2026-05-16
**Wave:** W131 — app-idea-intake (Sistema de entrada de ideias)
**Grupo:** G14 App Factory
**Status:** PLANEJADO — aguardando autorizacao para executar

---

## 1. Contexto

### 1.1 O que ja existe em src/app_factory/

| Arquivo | O que faz | Cobertura de testes |
|---|---|---|
| `models.py` (535 linhas) | `AppIdea`, `AppRequirement`, `AppBlueprint`, `AppArtifact` + todas as funcoes deterministicas de extracao/design | 30 testes ✅ |
| `errors.py` (28 linhas) | `AppFactoryError`, `InvalidAppIdeaError`, `PlannerError`, etc. | 0 testes especificos |
| `planner.py` (113 linhas) | `AppFactoryPlanner`: pipeline Idea → Requirements → Blueprint → Artifact | 0 testes especificos |
| `prd_generator.py` (142 linhas) | `generate_prd()`: blueprint → PRD markdown deterministico | 0 testes especificos |
| `structure_generator.py` (98 linhas) | `generate_project_structure()`: blueprint → arvore de arquivos | 0 testes especificos |
| 9 subpackages novos | `__init__.py` only (Fase 3 setup) | — |

### 1.2 Conclusao da auditoria

O `AppIdea` model **ja existe** e esta completo (title, description, target_audience, features, constraints, domain, status, validate, to_dict/from_dict).

O que **falta** para W131:
- **CLI** — comando `omnis idea` para submeter ideias interativamente
- **Persistencia** — `IdeaRegistry` com CRUD file-backed (JSONL)
- **Dry-run** — modo `dry_run=True` que valida mas nao persiste
- **Integracao** — saida do intake alimenta W132 (`AppFactoryPlanner`)

### 1.3 Relacao com waves seguintes

```
W131 (intake) → AppIdea (JSONL)
                    ↓
W132 (prd-gen) → AppFactoryPlanner.plan(idea) → AppArtifact
                    ↓
W133 (db-schema) → AppArtifact.project_structure → schema SQL
                    ...
```

---

## 2. Escopo da Wave — 10 Blocos

| Bloco | Nome | Descricao |
|---|---|---|
| **B1** | Model audit | Auditar `AppIdea` existente; adicionar campos se necessario para intake |
| **B2** | IdeaRegistry | CRUD file-backed: `add()`, `get()`, `list()`, `update_status()`, `delete()` |
| **B3** | Security gate | Validacao obrigatoria antes de persist; `validate()` chamado em todo `add()` |
| **B4** | Dry-run executor | `IdeaIntake.dry_run=True` → valida + retorna `AppIdea` sem persistir |
| **B5** | CLI command | `omnis idea add --title "X" --desc "Y" --features "a,b" --domain "Z"` |
| **B6** | Audit logging | Eventos: `idea_submitted`, `idea_validated`, `idea_persisted`, `idea_rejected` |
| **B7** | Integration tests | Testar CLI → dry_run → validate → persist → load_history |
| **B8** | Documentation | Docstrings + update SKILL.md + wave report |
| **B9** | Edge cases | Titulo duplicado, features vazias, constraints invalidos, encoding UTF-8 |
| **B10** | Validation + commit | Targeted tests green, wave report, commit |

---

## 3. Squad Assignment

**Squad unica** — W131 e sequencial, sem paralelizacao.

| Campo | Valor |
|---|---|
| Squad | S1 (single) |
| Branch | `feature/omnis-5waves-runtime-supreme` (continuar nesta) |
| Worktree | Nao necessario (sem paralelizacao) |
| Paths permitidos | `src/app_factory/`, `tests/app_factory/`, `data/app_factory/`, `docs/supreme_210/` |
| Paths proibidos | `src/` (outros modulos), `.env`, `exports/`, `config/` (exceto docs) |

---

## 4. Test Strategy

- **Targeted:** `python -m pytest tests/app_factory/ --import-mode=importlib -p no:warnings -v`
- **Full suite ao final:** `python -m pytest tests/ --import-mode=importlib -p no:warnings -q`
- **Novos testes esperados:** ~15-20 (B2 registry + B4 dry-run + B5 CLI + B9 edge cases)
- **Regressao:** 30 testes existentes devem continuar passando

---

## 5. Arquivos a criar/modificar

### Criar (3 novos)
| Arquivo | Bloco |
|---|---|
| `src/app_factory/idea_registry.py` | B2 |
| `src/app_factory/idea_intake.py` | B4 |
| `tests/app_factory/test_idea_intake.py` | B7 |

### Modificar (2 existentes)
| Arquivo | Bloco | Mudanca |
|---|---|---|
| `src/app_factory/cli.py` (ou criar) | B5 | Adicionar comando `idea` |
| `docs/supreme_210/OMNIS_SUPREME_210_WAVES_PROGRESS.md` | B10 | W131 → COMPLETE |

---

## 6. Risk Assessment

| Risco | Probabilidade | Impacto | Mitigacao |
|---|---|---|---|
| Duplicar funcionalidade do `AppFactoryPlanner` | Baixa | Medio | Planner e para W132; intake so persiste ideias |
| `AppIdea` model precisar de campos novos | Media | Baixo | B1 audita antes de codificar |
| CLI conflitar com `src/cli.py` principal (1668 linhas) | Media | Medio | Criar CLI proprio em `src/app_factory/cli.py` ou subcommand |
| Testes existentes quebrarem | Baixa | Alto | Rodar suite existente antes e depois de cada bloco |

---

## 7. Handoff Prompt (S1)

```
Execute W131 — app-idea-intake seguindo o plano em docs/implementation/W131_APP_IDEA_INTAKE_PLAN.md.

Pre-execucao:
- git status (deve estar limpo)
- python -m pytest tests/app_factory/ --import-mode=importlib -p no:warnings -v (30 testes must pass)

Blocos B1→B10 em ordem.
Nao pular gates de seguranca.
dry_run=True universal.
Commit ao final de cada bloco que produzir codigo funcional.
```

---

## 8. Gates de Conclusao

- [ ] 10/10 blocos executados
- [ ] Testes targeted passam (30 existentes + ~15 novos)
- [ ] Full suite verde (6955+)
- [ ] CLI funcional: `python -m src.app_factory.idea_intake --help`
- [ ] Dry-run mode testado e funcional
- [ ] Wave report em `docs/supreme_210/reports/W131_APP_IDEA_INTAKE_REPORT.md`
- [ ] Commit com mensagem convencional
- [ ] Progress tracking atualizado

---

*Plano gerado por wave-plan skill — 2026-05-16*

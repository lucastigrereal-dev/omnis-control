# NAMING CONVENTION AUDIT

**Date:** 2026-05-16
**Auditor:** agent-qa + docs-release (OMNIS CCOS)
**Status:** AUDITADO — nenhuma renomeacao executada

---

## Convencoes detectadas

O repositorio contem 3 convencoes de nomenclatura diferentes.

### 1. snake_case (legado)

Usado por arquivos rastreados no HEAD criados antes do bootstrap CCOS.

| Categoria | Exemplos |
|---|---|
| Hooks | `import_guard.ps1`, `pre_tool_use_guard.ps1`, `session_logger.ps1` |
| Scripts | `omnis_parallel.ps1`, `omnis_parallel_monitor.ps1`, `omnis_super_test.py`, `validate_skills.py`, `disk_analyze.py`, `disk_audit_readonly.py` |
| Agents | `architecture-auditor.md`, `test-guardian.md`, `security-guardian.md`, `documentation-scribe.md`, `app-factory-architect.md`, `app-factory-builder.md` |
| Skills dirs | `scope-lock`, `targeted-test`, `full-suite-gate`, `merge-wave`, `app-factory-api`, `app-factory-prd`, `app-factory-schema`, `wave-plan` |

### 2. kebab-case (bootstrap CCOS)

Usado pelos arquivos novos criados pelo `bootstrap-omnis-ccos.ps1`.

| Categoria | Exemplos |
|---|---|
| Hooks | `pre-tool-guard.ps1`, `post-tool-log.ps1`, `session-stop-report.ps1`, `subagent-stop-report.ps1` |
| Scripts | `omnis-create-worktrees.ps1`, `omnis-safe-test.ps1`, `omnis-secret-scan.ps1`, `omnis-sync-claude.ps1`, `omnis-merge-gate.ps1`, `omnis-report.ps1` |
| Agents | `agent-architect.md`, `agent-executor.md`, `agent-refactor.md`, `agent-qa.md`, `agent-docs-release.md` |
| Skills dirs | `feature-scaffolder`, `repo-architect`, `refactor-guardian`, `qa-merge-gate`, `docs-release`, `spawn-worktrees` |

### 3. snake_case com prefixo (misto)

| Categoria | Exemplos |
|---|---|
| Script | `bootstrap-omnis-ccos.ps1` (kebab-case, mas funcao de bootstrap) |
| Docs | `CCOS_BOOTSTRAP_VALIDATION_REPORT.md` (SCREAMING_SNAKE_CASE com prefixo CCOS) |

---

## Inconsistencias por categoria

### Hooks
```
Antigos: import_guard.ps1          (snake_case)
         pre_tool_use_guard.ps1    (snake_case, verbo_substantivo)
         session_logger.ps1        (snake_case, substantivo_substantivo)

Novos:   pre-tool-guard.ps1        (kebab-case, verbo-substantivo)
         post-tool-log.ps1         (kebab-case)
         session-stop-report.ps1   (kebab-case, 3 palavras)
         subagent-stop-report.ps1  (kebab-case, 3 palavras)
```

### Scripts
```
Antigos: omnis_parallel.ps1             (prefixo_snake_case)
         omnis_parallel_monitor.ps1     (prefixo_snake_case)
         omnis_super_test.py            (prefixo_snake_case)
         validate_skills.py             (verbo_snake_case, sem prefixo)

Novos:   omnis-create-worktrees.ps1     (prefixo-kebab-case)
         omnis-safe-test.ps1            (prefixo-kebab-case)
         omnis-secret-scan.ps1          (prefixo-kebab-case)
         omnis-sync-claude.ps1          (prefixo-kebab-case)
         omnis-merge-gate.ps1           (prefixo-kebab-case)
         omnis-report.ps1               (prefixo-kebab-case)
```

### Agents
```
Antigos: architecture-auditor.md       (kebab-case, sem prefixo agent-)
         test-guardian.md              (kebab-case)
         security-guardian.md          (kebab-case)
         documentation-scribe.md       (kebab-case)
         app-factory-architect.md      (kebab-case com namespace)
         app-factory-builder.md        (kebab-case com namespace)
         REGISTRY.md                   (SCREAMING_SNAKE_CASE)

Novos:   agent-architect.md            (prefixo agent- + kebab-case)
         agent-executor.md             (prefixo agent- + kebab-case)
         agent-refactor.md             (prefixo agent- + kebab-case)
         agent-qa.md                   (prefixo agent- + kebab-case)
         agent-docs-release.md         (prefixo agent- + kebab-case)
```

### Skills (diretorios)
```
Antigos: scope-lock/           (kebab-case)
         targeted-test/        (kebab-case)
         full-suite-gate/      (kebab-case)
         merge-wave/           (kebab-case)
         app-factory-api/      (kebab-case com namespace)
         app-factory-prd/      (kebab-case com namespace)
         app-factory-schema/   (kebab-case com namespace)
         wave-plan/            (kebab-case)

Novos:   feature-scaffolder/   (kebab-case)
         repo-architect/       (kebab-case)
         refactor-guardian/    (kebab-case)
         qa-merge-gate/        (kebab-case)
         docs-release/         (kebab-case)
         spawn-worktrees/      (kebab-case)
```

---

## Resumo das inconsistencias

| Inconsistencia | Exemplos |
|---|---|
| prefixo `agent-` vs sem prefixo | `agent-architect.md` vs `architecture-auditor.md` |
| snake_case vs kebab-case em hooks | `pre_tool_use_guard.ps1` vs `pre-tool-guard.ps1` |
| snake_case vs kebab-case em scripts | `omnis_parallel.ps1` vs `omnis-report.ps1` |
| verbo_substantivo vs verbo-substantivo | `import_guard.ps1` vs `post-tool-log.ps1` |
| REGISTRY.md em SCREAMING_SNAKE | unico arquivo .md no diretorio agents/ que nao segue kebab-case |

---

## Impacto operacional

| Impacto | Nivel |
|---|---|
| Scripts antigos referenciados em docs/hooks? | BAIXO — somente `omnis_parallel.ps1` e `omnis_parallel_monitor.ps1` sao referenciados externamente |
| settings.json quebra se renomearmos hooks? | ALTO — paths estao hardcoded no settings.json |
| Skills tem dependencia entre si? | BAIXO — cada skill e independente |
| Agents sao invocados por nome? | MEDIO — o nome do arquivo define o agent name no frontmatter |

---

## Recomendacao

| Acao | Prioridade |
|---|---|
| Definir convencao unica para hooks | ALTA — afeta settings.json |
| Definir se agents usam prefixo `agent-` ou nao | MEDIA |
| Padronizar scripts: todos `omnis-*` (kebab) ou `omnis_*` (snake) | MEDIA |
| Renomear `REGISTRY.md` → `registry.md` (ou manter como excecao) | BAIXA |
| Executar renomeacao em lote unico, com atualizacao de settings.json | ALTA (quando fizer) |

**Nao renomear nada ainda.** Aguardar decisao de Lucas sobre a convencao preferida.

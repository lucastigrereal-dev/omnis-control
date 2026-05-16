# Subagent Registry

## CCOS Agents (Wave 7B)

| Agent | When to use | Risk level |
|---|---|---|
| agent-architect | Planejar waves, mapear modulos, definir contratos, separar paralelo vs sequencial | Low |
| agent-executor | Executar features com escopo travado e dry_run=True | Medium |
| agent-refactor | Consolidar modulos redundantes com backward compat | Medium |
| agent-qa | Validar suite, scan de secrets, gate de merge, gerar QA report | Low |
| agent-docs-release | Handoff reports, QA reports, changelog, release notes | Low |

## Audit & Guardian Agents

| Agent | When to use | Risk level |
|---|---|---|
| architecture-auditor | Before new module, before merge | Low |
| test-guardian | After implementation, before commit | Low |
| security-guardian | Any module with external action, tokens, OAuth | High |
| documentation-scribe | End of phase, end of squad | Low |

## App Factory Agents (G14)

| Agent | When to use | Risk level |
|---|---|---|
| app-factory-architect | After PRD approved, before code generation (G14) | Low |
| app-factory-builder | After blueprint approved, full app generation (G14) | Medium |

## Usage notes
- Invoke via Agent tool with subagent_type
- Each subagent is read-only by default
- Audit agents never modify code
- CCOS executor/refactor agents podem escrever codigo dentro de escopo travado
- App Factory agents (G14) generate code only after operator approval
- agent-qa nunca mergea sem autorizacao explicita de Lucas

# Subagent Registry

| Agent | When to use | Risk level |
|---|---|---|
| architecture-auditor | Before new module, before merge | Low |
| test-guardian | After implementation, before commit | Low |
| security-guardian | Any module with external action, tokens, OAuth | High |
| documentation-scribe | End of phase, end of squad | Low |
| app-factory-architect | After PRD approved, before code generation (G14) | Low |
| app-factory-builder | After blueprint approved, full app generation (G14) | Medium |

## Usage notes
- Invoke via Agent tool with subagent_type
- Each subagent is read-only by default
- Audit agents never modify code
- App Factory agents (G14) generate code only after operator approval

# Subagent Registry

| Agent | When to use | Risk level |
|---|---|---|
| architecture-auditor | Before new module, before merge | Low |
| test-guardian | After implementation, before commit | Low |
| security-guardian | Any module with external action, tokens, OAuth | High |
| documentation-scribe | End of phase, end of squad | Low |

## Usage notes
- Invoke via Agent tool with subagent_type
- Each subagent is read-only by default
- Audit agents never modify code

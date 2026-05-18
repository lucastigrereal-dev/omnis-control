# W203 — Config Paths Safety Audit
# Status: DONE (2 ISSUES FOUND) | 2026-05-17

## Summary
Audited 9 config files. 1 critical security finding, 1 high path mismatch. No deletions.

---

## Finding 1: CRITICAL — API Key exposed in committed config

**File:** `config/connectors.yaml:82`
**Content:** `"Master key: sk-pub-os-UwN4DEcTMMzB6SxxSaJpaj"`

The LiteLLM master key is hardcoded in a committed YAML file. This key:
- Is visible to anyone with repo access
- Is in plaintext (no env var substitution)
- Controls access to 7 LLM models via OpenRouter

**Risk:** If this key is still active, anyone cloning the repo could use the LLM budget.

**Recommendation:** Rotate the key immediately. Replace with `"Master key: $LITELLM_MASTER_KEY"` or reference from env.

---

## Finding 2: HIGH — `paths.yaml` uses old `~/omnis-control` root

**File:** `config/paths.yaml`
**References (6 paths, all using `~/omnis-control`):**

| Key | Value |
|---|---|
| `paths.claude_skills_path` | `~/omnis-control/skills` |
| `paths.local_search_roots[0]` | `~/omnis-control/skills` |
| `paths.local_search_roots[3]` | `~/omnis-control` |
| `paths.publisher_os_path` | `~/publisher-os` |
| `paths.obsidian_vault_path` | `~/Desktop/ARQUIVOS_MANUS_CLAUDE/OBSIDIAN/ComandoCentral` |
| `paths.jarvis_os_docs_path` | `~/JARVIS_OS` |

Root cause: no `control_root` variable. Each path hardcoded independently.

---

## Finding 3: MEDIUM — External path references in configs

Paths pointing outside the project:

| File | Line | Path | Purpose |
|---|---|---|---|
| `sectors.yaml` | 57 | `~/daily-prophet-hotels` | External system path |
| `sectors.yaml` | 113 | `~/llm-router/` | Skill path reference |
| `connectors.yaml` | 16 | `~/publisher-os/mcp_server.py` | MCP server location |
| `connectors.yaml` | 27 | `~/publisher-os-cockpit` | Cockpit location |
| `connectors.yaml` | 135 | `~/tg-approve/` | Disabled script path |

These are documentation notes, not runtime paths. Low risk.

---

## Clean config files (no path issues)

| File | Status |
|---|---|
| `capabilities.yaml` | Clean — no paths |
| `intents.yaml` | Clean — no paths |
| `meta_accounts.example.yaml` | Clean — template only, gitignored real file |
| `output_generators.yaml` | Clean — no paths |
| `roles.yaml` | Clean — no paths |
| `sectors_registry.yaml` | Clean — no paths |

---

## Config file inventory

```
config/
  paths.yaml              — HIGH: old ~/omnis-control paths
  connectors.yaml         — CRITICAL: exposed API key
  sectors.yaml            — MEDIUM: external path references
  capabilities.yaml       — clean
  intents.yaml            — clean
  meta_accounts.example.yaml — clean (example only)
  output_generators.yaml  — clean
  roles.yaml              — clean
  sectors_registry.yaml   — clean
```

---

## Remediation priority

1. **IMMEDIATE:** Rotate LiteLLM master key (`connectors.yaml:82`)
2. **NEXT:** Add `control_root: ~/omnis-maintenance` to `paths.yaml`
3. **SOON:** Centralize path resolution in one helper module

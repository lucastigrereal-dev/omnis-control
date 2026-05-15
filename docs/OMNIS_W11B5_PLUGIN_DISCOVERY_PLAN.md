# OMNIS W11B5 — Plugin Discovery Plan

**Date:** 2026-05-15

## Discovery phases

### Phase 1: Local filesystem scan
- Scan `.claude/plugins/`, `~/.claude/plugins/`, project-level `plugins/`
- Look for `plugin.json` or `manifest.json` files
- Validate JSON schema against PluginManifest model

### Phase 2: Registry enumeration
- Read installed plugin registry (file-backed index)
- Compare with discovered manifests for install/uninstall drift
- Mark stale entries as UNINSTALLED

### Phase 3: Permission evaluation
- Run PluginPermissionGate.evaluate_manifest() for each discovered manifest
- Categorize: SAFE, NEEDS_REVIEW, BLOCKED
- Forbidden permissions (SECRETS, SHELL) → auto-block

### Phase 4: MCP server discovery
- Scan MCP descriptors from plugin manifests
- Validate transport format (stdio, sse, http)
- Flag unknown transports for review

### Phase 5: Settings resolution
- Load plugin settings from file-backed registry
- Resolve secrets references (mark as pending, don't read values)
- Apply defaults from manifest

## Discovery rules
1. Never auto-enable plugins with SECRETS or SHELL permissions
2. Never read `.env` or secrets files during discovery
3. All MCP servers default to enabled=False
4. Dry-run mode: never actually start MCP servers
5. Blocked plugins stay DISABLED even if manifest is present

# CLI Modularization Plan — R0-lite

## Current State

`src/cli.py` — 1.599 lines, 17 commands, 1 file, 7 Typer apps.

### Command Groups (Current)

| Group | Commands | Lines Est. | Typer App |
|-------|----------|-----------|-----------|
| Diagnostics | `status`, `skills`, `skill-info`, `run-skill`, `doctor`, `report` | ~350 | `app` |
| Publisher | `publisher-health` | ~80 | `app` |
| Docker | `docker-status` | ~80 | `app` |
| Memory | `memory-status` | ~80 | `app` |
| Obsidian | `obsidian-status` | ~80 | `app` |
| Video Pipeline | `video-status` | ~80 | `app` |
| Video Assets | `video-assets` (5 subcommands) | ~200 | `video_app` |
| Content Queue | `queue` (8 subcommands), `accounts` (4 subcommands) | ~280 | `queue_app`, `accounts_app` |
| Captions | `captions` (7 subcommands) | ~180 | `captions_app` |
| Approvals | `approvals` (5 subcommands) | ~120 | `approvals_app` |
| Templates | `templates` (2 subcommands) | ~50 | `templates_app` |

### Pain Points

1. **1.599 lines in a single file** — 33.5% of all src LOC
2. **Mixed concerns** — diagnostics, business logic, and data access all in one file
3. **Duplicated patterns** — `os.path.expanduser("~/omnis-control/...")` repeated ~30x
4. **Growing** — each new phase adds 1-2 new Typer apps + subcommands
5. **Hidden coupling** — CLI imports directly from `src/content_queue`, `src/caption_approval`, etc.

---

## Proposed Future Structure

```
src/
├── cli.py                          # Root app + imports (delegates to groups)
├── cli_commands/                   # Extracted command groups
│   ├── __init__.py                 # Future: app registration
│   ├── diagnostics.py              # status, skills, doctor, report
│   ├── video_assets_cmd.py         # video-assets, video-status
│   ├── content_queue_cmd.py        # queue, accounts
│   ├── caption_approval_cmd.py     # captions, approvals, templates
│   ├── publisher_cmd.py            # publisher-health
│   ├── docker_cmd.py               # docker-status
│   ├── memory_cmd.py               # memory-status
│   ├── obsidian_cmd.py             # obsidian-status
│   ├── argos_drafts_cmd.py         # argos-drafts (Fase 2E)
│   └── integrations_cmd.py         # integrations (Fase 3A, future)
```

### Group Definitions

| Future Group | Commands | When |
|-------------|----------|------|
| `diagnostics.py` | `status`, `skills`, `skill-info`, `run-skill`, `doctor`, `report` | R1 |
| `video_assets_cmd.py` | `video-status`, `video-assets` | R1 |
| `content_queue_cmd.py` | `queue`, `accounts` | R1 |
| `caption_approval_cmd.py` | `captions`, `approvals`, `templates` | R1 |
| `publisher_cmd.py` | `publisher-health` | R1 |
| `docker_cmd.py` | `docker-status` | R1 |
| `memory_cmd.py` | `memory-status` | R1 |
| `obsidian_cmd.py` | `obsidian-status` | R1 |
| `argos_drafts_cmd.py` | `argos-drafts` | Now (Fase 2E) |
| `integrations_cmd.py` | `integrations` | Future (Fase 3A+) |

---

## Migration Strategy (3 Steps)

### Step 1: R0-lite (NOW)
- Create `src/cli_commands/__init__.py` (empty, docstring only)
- Create `src/cli_commands/argos_drafts_cmd.py` for new Fase 2E commands
- All existing commands stay in `cli.py`
- **No renames, no extractions, no behavior change**

### Step 2: R1 (Future — after 2E/S0/3A)
- Extract each group into its own file
- Each file exports a Typer app
- `cli.py` imports and adds each app as a subcommand
- One group per PR / per phase
- Test each extraction independently

Migration pattern for R1:
```python
# cli.py after R1
from src.cli_commands.diagnostics import diagnostics_app
app.add_typer(diagnostics_app, name="diagnostics")
```

### Step 3: R2 (Optional — far future)
- Dynamic discovery via entry_points or plugin system
- Zero-touch registration for new command groups

---

## Rules (R0-lite)

- **Zero** behavior changes
- **Zero** command renames (`omnis queue list` remains `omnis queue list`)
- **Zero** extraction of existing commands
- New commands for new phases can go in `cli_commands/` or stay in `cli.py`
- Tests must pass before and after

## Current file: `src/cli.py` (1.599 lines)

```text
src/cli.py
├── imports                                           ~20 lines
├── constants (paths)                                 ~15 lines
├── app = typer.Typer() (+ 6 sub-apps)               ~10 lines
├── 6 diagnostics commands                            ~350 lines
├── video-app + 5 subcommands                        ~200 lines
├── accounts-app + 4 subcommands                     ~120 lines
├── queue-app + 8 subcommands                        ~260 lines
├── captions-app + 7 subcommands                     ~180 lines
├── approvals-app + 5 subcommands                    ~120 lines
├── templates-app + 2 subcommands                    ~50 lines
├── publisher/docker/memory/obsidian                 ~200 lines
├── report generation helper                         ~60 lines
└── main block                                       ~10 lines
```

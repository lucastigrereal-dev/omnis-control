# P26 — APP FACTORY SUPREME SKELETON

> **Data:** 2026-05-14
> **Status:** SKELETON COMPLETE

---

## FILES

```
src/app_factory_supreme/
├── __init__.py            # Public exports (17 symbols)
├── models.py              # AppBuild, ModuleBuild, BuildStatus constants
├── errors.py              # AppFactorySupremeError + 6 subclasses
├── pipeline.py            # BuildPipeline — orchestrator
├── code_generator.py      # CodeGenerator — bridge to P22 Forge
├── verifier.py            # BuildVerifier — tests + security scan
├── packager.py            # AppPackager — README + Dockerfile
└── cli.py                 # CLI: build, plan, status, list, rollback

tests/app_factory_supreme/
├── test_models.py         # 19 testes
├── test_pipeline.py       # 11 testes
├── test_code_generator.py # 4 testes
├── test_verifier.py       # 4 testes
├── test_packager.py       # 3 testes
└── test_e2e_app_factory.py # 12 testes

docs/app_factory_supreme/
└── P26_APP_FACTORY_SUPREME_SKELETON.md
```

---

## CONTRACTS

### AppBuild
- `build_id` prefix: `apb_`
- Status: planned → blueprinting → generating → testing → scanning → packaging → complete
- `overall_pass_rate` — modules_passing / module_count
- 3 approval flags: blueprint_approved, security_approved, package_approved
- Factory: `AppBuild.new(idea_id, title)`

### ModuleBuild
- `module_name` required
- Tracks: files_generated, tests_pass, policy_scan_pass
- Factory: `ModuleBuild.new(module_name)`

### BuildPipeline
- `dry_run=True` default
- `build(idea)` — full pipeline (dry: plans only)
- `plan(title)` — blueprint only
- `rollback(build)` — marks as rolled_back

### CLI
- `app-factory build --title "..."` — full build
- `app-factory plan --title "..."` — plan only
- `app-factory status <id>` — show status
- `app-factory list` — list builds
- `app-factory rollback <id>` — rollback

---

## DEPENDENCIES
- Builds on src/app_factory/ (existing models)
- Bridge to P22 CapabilityForge (code_generator.py)
- Zero toques em módulos existentes

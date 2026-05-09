# P5.4 — E2E Executive Decision Flow

**Tests:** 11  
**Status:** COMPLETE  

## Flows validated

### Flow 1: Marketing Campaign (no approval)
```
"carrossel campanha instagram post"
→ sector=marketing ✅
→ capabilities=[offline_package_carousel, campaign_package, ...] ✅
→ approval_required=False ✅
→ execute → status=dry_run ✅
→ manifest: sector=marketing, status=dry_run ✅
```

### Flow 2: App Factory (high risk, approval required)
```
"cria app sistema api software"
→ capabilities=[app_factory_spec], risk=high ✅
→ approval_required=True ✅
→ execute (no approval) → status=blocked_pending_approval, auto-creates req ✅
→ approve req → execute again → status=dry_run ✅
→ reject req → execute again → status=blocked ✅
```

### Flow 3: Finance Gap Workflow
```
"roi faturamento receita financeiro"
→ sector=finance, capabilities=[], gap detected ✅
→ save gap → request_approval_for_gap → approval created ✅
→ approve → mark_gap_planned → gap.status=planned ✅
```

### Security invariants
- No network calls ✅
- No secret env reads ✅
- no_secrets_in_manifest() passes ✅

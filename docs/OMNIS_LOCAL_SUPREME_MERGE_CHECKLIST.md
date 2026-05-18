# OMNIS Local Supreme — Merge Checklist
**Data:** 2026-05-18 | **Branch:** feature/omnis-5waves-runtime-supreme → master

## Commits Incluídos (post-master)

```
c7cda05 feat(omnis): run week 2 local autonomous operation
77167a0 feat(omnis): add read-only disk safety audit
811778b feat(omnis): add memory reuse stress test
914bba7 feat(omnis): install skill system v1.0 — 18 skills + wave orchestrator
c995b59 feat(omnis): add local video studio real MVP
bf4dec3 feat(omnis): add local cockpit output viewer
e78059c feat(omnis): harden output factory mission packaging
7ebe52d docs(omnis): consolidate local supreme operating docs
e9f83d9 docs(omnis): audit final gaps after G33
73a6046 feat(omnis): weekly production ritual — WeeklyPackOrchestrator
de2742a feat(omnis): carousel preview HTML — navigable slide viewer
65bfbf9 feat(omnis): local commands CLI
f15041f docs(omnis): post-supreme consolidation
cbd273f feat(omnis): complete local supreme autonomous operation
```

## Checklist de Código

- [x] `src/cli_local.py` — CLI local, 10 comandos
- [x] `src/output_factory/` — 7 módulos, 7 testes
- [x] `src/preview/carousel_preview.py` — 10 testes
- [x] `src/weekly/weekly_pack.py` — 25 testes + learning context
- [x] `src/video_studio/` expandido — 18 testes
- [x] `src/memory/learning_reuse.py` + `learning_sources.py` — 11 testes
- [x] `src/computer_ops/disk_safety_audit.py` — 21 testes
- [x] `src/reports/output_viewer_data.py` — 6 testes

## Checklist de Testes

- [x] 446/446 novos testes passando
- [x] 8 falhas pré-existentes isoladas (não causadas por esta branch)
- [x] Nenhuma regressão confirmada

## Checklist de Documentação

- [x] OUTPUT_INDEX
- [x] CAPABILITY_CATALOG
- [x] COMO_USAR
- [x] OPERATOR_PROMPT
- [x] ASSET_PROMOTION_DECISIONS
- [x] HUMAN_QA_TEMPLATE
- [x] RELEASE_NOTES
- [x] RC_REPORT
- [x] MERGE_CHECKLIST (este arquivo)

## Checklist de Cockpit

- [x] cockpit/index.html
- [x] cockpit/outputs.html + outputs_data.js
- [x] cockpit/carousel_preview.html (10 slides)
- [x] cockpit/approvals.html
- [x] cockpit/missions_data.js + ops_data.js

## Checklist de Missões

- [x] MIS-002 a MIS-006 com 06_exports/ completos (manifest/checksum/zip/index/report)
- [x] missions/memory_reuse_stress_test/ (A/B comprovado)
- [x] missions/A Gente Viaja Brasil_weekly_20260518/ (Week 2)
- [x] missions/_learnings.jsonl

## Riscos

| Risco | Nível | Ação |
|---|---|---|
| 2 erros coleção pré-existentes (caption_approval_v2, creative_production_v2) | Baixo | Registrado, fora do escopo desta branch |
| Video render real exige ffmpeg | Baixo | Fallback para dry-run implementado |
| Weekly content precisa revisão humana | Baixo | By design — sistema gera, humano revisa |
| Disk audit categorização conservadora | Baixo | Operador revisa antes de qualquer limpeza |

## O Que NÃO Está Nesta Branch

- Meta OAuth / publicação real
- WhatsApp / CRM remoto
- Deploy / Publer / Metricool
- Whisper real instalado
- Canva PNG export

## Como Testar Antes de Merge

```sh
# Suite nova
python -m pytest tests/cli/ tests/preview/ tests/weekly/ tests/output_factory/ \
  tests/memory/ tests/computer_ops/ tests/video_studio/ tests/reports/ \
  --import-mode=importlib -p no:warnings -q

# CLI rápido
python -m src.cli local status
python -m src.cli local campaign --profile "@oinatalrn" --theme "praia" --objective "collab"

# Cockpit
# Abrir cockpit/index.html no browser
```

## Recomendação Final

**MERGE APROVADO** — após Lucas revisar este checklist e autorizar push.

```sh
# Quando autorizado:
git push origin feature/omnis-5waves-runtime-supreme
# Depois abrir PR para master
```

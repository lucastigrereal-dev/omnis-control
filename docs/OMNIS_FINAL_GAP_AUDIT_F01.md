# OMNIS Final Gap Audit — F01
**Data:** 2026-05-18 | **Branch:** feature/omnis-5waves-runtime-supreme

## FEITO ✅

### G33 — Local Commands CLI
- `src/cli_local.py` + grupo `omnis local` registrado em `src/cli.py`
- Comandos: campaign, carousel, reels, app, forge, cockpit, status
- 10/10 testes em `tests/cli/test_local_commands.py`
- Commit: 65bfbf9

### G33 — Carousel Preview HTML
- `src/preview/carousel_preview.py` — `CarouselPreviewGenerator`
- `cockpit/carousel_preview.html` — 10 slides, navegação prev/next, print-friendly
- 10/10 testes em `tests/preview/`
- Commit: de2742a

### G33 — Weekly Production Ritual
- `src/weekly/weekly_pack.py` — `WeeklyPackOrchestrator`
- 9/9 testes em `tests/weekly/`
- Commit: 73a6046

### Local Supreme — Documentação (já existente)
- docs/OMNIS_LOCAL_SUPREME_OUTPUT_INDEX.md ✅
- docs/OMNIS_CAPABILITY_CATALOG.md ✅
- docs/COMO_USAR_OMNIS_LOCAL_SUPREME.md ✅
- docs/OMNIS_LOCAL_SUPREME_OPERATOR_PROMPT.md ✅
- docs/OMNIS_ASSET_PROMOTION_DECISIONS.md ✅
- docs/OMNIS_LOCAL_SUPREME_HUMAN_QA_TEMPLATE.md ✅
- docs/OMNIS_LOCAL_SUPREME_RELEASE_NOTES.md ✅

### Módulos src/ existentes
- `src/video_studio/` — modelos, assets, captions, transcription, cut_plan, package, export_queue (PARCIAL — sem ingest/srt/render_ffmpeg)
- `src/memory/` — learning_writer, context_builder, akasha_reader, embeddings (PARCIAL — sem learning_reuse)
- `src/computer_ops/` — models, service (PARCIAL — sem disk_safety_audit)

---

## PARCIAL ⚠️

| Item | Estado | O que falta |
|---|---|---|
| Output Factory | MISSING | src/output_factory/ inexistente — package_manifest.json existe nas missões mas sem gerador padronizado |
| Video Studio | PARCIAL | src/video_studio/ existe sem: ingest.py, srt_generator.py, render_ffmpeg.py, audio_extract.py |
| Memory Reuse | PARCIAL | src/memory/ existe sem: learning_reuse.py, learning_sources.py |
| Disk Safety Audit | PARCIAL | src/computer_ops/ existe sem: disk_safety_audit.py |
| Cockpit Output Viewer | PARCIAL | cockpit/outputs.html existe mas sem outputs_data.js dinâmico nem filtros |

---

## FALTA ❌

| Item | Wave | Prioridade |
|---|---|---|
| src/output_factory/ (manifest/checksum/zip/index) | F04 | P0 |
| Video Studio: ingest + SRT + render_ffmpeg | F06 | P1 |
| Memory Reuse comprovado A/B | F07 | P1 |
| Disk Safety Audit script | F08 | P1 |
| Cockpit Output Viewer com filtros | F05 — já existe parcialmente | P1 |
| Week 2 Operation | F09 | P2 |
| Release Candidate + merge checklist | F10 | P0 |

---

## Comandos Validados ✅

```
omnis local campaign   — OK
omnis local carousel   — OK
omnis local reels      — OK
omnis local app        — OK
omnis local forge      — OK
omnis local cockpit    — OK
omnis local status     — OK
```

## Arquivos Confirmados ✅

```
cockpit/carousel_preview.html        — 10 slides, navegável
missions/MIS-20260518-002 a 006      — outputs reais
missions/_learnings.jsonl            — learnings registrados
src/cli_local.py                     — CLI local
src/preview/carousel_preview.py      — gerador HTML
src/weekly/weekly_pack.py            — ritual semanal
```

## Riscos

| Risco | Impacto | Mitigação |
|---|---|---|
| Output Factory ausente | Output Factory Hardening não tem base | Criar do zero em F04 |
| Video Studio incompleto | Render MP4 pode falhar se ffmpeg ausente | Fallback obrigatório para dry-run |
| Memory reuse não comprovado | F07 pode revelar que sistema não reutiliza realmente | Aceitar "não comprovado" como estado legítimo |

## Próximos Passos (ordem)

1. F02 — Atualizar docs existentes com comandos G33
2. F03 — Confirmar QA + asset promotion já criados
3. F04 — Criar src/output_factory/ do zero
4. F05 — Completar cockpit output viewer
5. F06 — Completar video_studio (ingest/srt/render)
6. F07 — Memory reuse A/B test
7. F08 — Disk safety audit script
8. F09 — Week 2 operation
9. F10 — RC + merge checklist

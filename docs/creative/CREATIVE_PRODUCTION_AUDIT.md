# Creative Production OS — Auditoria de Estado Atual

**Data:** 2026-05-06
**Auditor:** Claude Code

---

## 1. Módulos Python Existentes

| Arquivo | Responsabilidade | Status |
|---------|-----------------|--------|
| `models.py` | CreativeBrief, ProductionItem, CreativeReview (dataclasses) | ✅ Estável |
| `briefs.py` | CRUD de briefs + JSONL persistence + validação de caption | ✅ Estável |
| `production_queue.py` | Fila de produção + stats | ✅ Estável |
| `exporter.py` | Export package com 10 arquivos textuais | ✅ Funcional, precisa expandir |
| `review.py` | Approval gate (approve/reject/is_ready_for_argos) | ✅ Estável |

## 2. Modelos/Dataclasses

| Modelo | Campos | Uso |
|--------|--------|-----|
| CreativeBrief | creative_brief_id, queue_id, account_handle, format, objective, visual_direction, caption_draft_id, script, shot_list, design_notes, editing_notes, asset_requirements, tool_suggestions, status, warnings, timestamps | Brief criativo |
| ProductionItem | production_id, queue_id, creative_brief_id, asset_type, tool_target, status, asset_path, asset_id, review_notes, timestamps | Fila de produção |
| CreativeReview | review_id, creative_brief_id, reviewer, status, notes, timestamps | Registro de revisão |

## 3. Storage Atual

| Fonte | Path | Formato |
|-------|------|---------|
| Creative Briefs | `data/creative_briefs.jsonl` | JSONL append-only |
| Review Log | `data/creative_review_log.jsonl` | JSONL append-only |
| Production Queue | `data/production_queue.jsonl` | JSONL append-only |
| Export Packages | `data/exports/creative_packages/` | Diretório com arquivos .md/.txt/.json |

## 4. Comandos CLI Existentes

**Nenhum.** Não há comandos `creative` no `omnis.py`. O módulo só é acessível via Python direto.

## 5. Testes Existentes

| Arquivo | Testes | Cobertura |
|---------|--------|-----------|
| `tests/test_creative_production.py` | 18 testes | models, briefs CRUD, queue, exporter, review |

## 6. Lacunas para Export Package COMPLETO

| Funcionalidade | Status | Necessário |
|---------------|--------|------------|
| 10 arquivos textuais (.md/.txt/.json) | ✅ Implementado | — |
| `preview.html` (preview visual HTML) | ❌ Ausente | Renderização HTML inline |
| `mock_image.png` (placeholder 1080x1080) | ❌ Ausente | Geração via Pillow |
| `WARNINGS.md` (avisos de campos ausentes) | ❌ Ausente | Gerado quando dados faltam |
| CLI commands | ❌ Ausente | `omnis.py creative ...` |

## 7. Riscos Identificados

- Exporter usa `brief.script` para `caption.txt` — pode não ser a legenda final aprovada
- Export package ID usa timestamp `{queue_id}_{ts}` — não é determinístico
- Sem validação de que o brief está aprovado antes de exportar
- Sem preview visual do pacote gerado
- Sem teste de quebra se JSONL estiver vazio

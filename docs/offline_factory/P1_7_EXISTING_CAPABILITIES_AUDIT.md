# P1.7 — Existing Capabilities Audit

**Data:** 2026-05-08

---

## Modulos Existentes

| Modulo | Arquivos | Funcao |
|---|---|---|
| creative_production | 8 py | Briefs, export (13 artefatos), HTML render, mock image |
| video_assets | 6 py | Registry, scanner, queue, models |
| caption_approval | 5 py | Drafts, templates, approvals, models |
| content_queue | accounts.py | Account registry (2 contas) |
| publisher | 4 py | Worker, statemachine, pipeline |

## O que ja exporta arquivo

`creative_production/exporter.py` → `generate_export_package()`:
13 artefatos: brief.md, caption.txt, hashtags.txt, script.md, shot_list.md, design_notes.md, editing_notes.md, asset_requirements.json, tool_suggestions.md, production_checklist.md, preview.html, mock_image.png, WARNINGS.md

## O que ja renderiza HTML

`creative_production/html_renderer.py` → `render_preview_html()`

## O que ja gera mock image

`creative_production/mock_image_generator.py` → `generate_mock_image()` via Pillow

## CLI existente

- `creative status` — status do modulo
- `creative list` — lista briefs
- `creative show` — detalhes de um brief
- `creative export-package` — gera pacote (13 artefatos)
- `captions list` — 42 drafts
- `queue list` — 42 itens na fila
- `video-assets list` — 0 assets
- `oauth *` — probe, validate, readiness, accounts, account-readiness
- `post preflight` — 8 checks
- `tools health-report` — 19 ferramentas
- `metrics today` — runs do dia

## O que falta para pacote de carrossel

1. **Slides outline** — estrutura de slides numerados
2. **Visual brief** — direcao visual por slide
3. **SEO metadata** — metadados exportaveis
4. **Publishing checklist** — especifico para carrossel
5. **Manifest JSON** — indice de todos os arquivos

## O que falta para pacote de Reels

1. **Script com timestamps** — texto + marcacoes de tempo
2. **Voiceover guide** — tom, velocidade, pausas
3. **Shot list detalhada** — angulos, transicoes, duracao
4. **Audio notes** — trilha, efeitos sonoros
5. **Caption sync** — legenda sincronizada com video

## O que falta para campanha de 10 posts

1. **Orquestracao multi-slot** — gerar varios pacotes em lote
2. **Calendario editorial** — visao semanal/mensal
3. **Relatorio de campanha** — sumario de todos os pacotes

## Modulos a REAPROVEITAR

- creative_production/exporter.py (core do export)
- creative_production/html_renderer.py (preview HTML)
- creative_production/mock_image_generator.py (mock image)
- caption_approval/models.py (CaptionDraft)
- caption_approval/drafts.py (get_draft)
- content_queue/accounts.py (AccountRegistry)

## O que NAO recriar

- NAO criar novo exporter — estender o existente
- NAO criar novo HTML renderer — reusar
- NAO criar novo mock generator — reusar
- NAO criar novo registry de contas — reusar

---

**Estrategia: offline_factory = camada de orquestracao + tipos de pacote + manifesto + CLI unificada.**

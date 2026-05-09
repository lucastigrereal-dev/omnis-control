# Catalogo de Entregaveis Offline

**Versao:** P1.8 | **Data:** 2026-05-09

Tudo que o OMNIS consegue gerar localmente, sem OAuth, sem Meta, sem conta conectada.

---

## Entregaveis Implementados

| Tipo | Comando | Arquivos Gerados | Status Possiveis | Depende De |
|---|---|---|---|---|
| Carrossel | `offline package-carousel <queue_id>` | caption.md, seo_metadata.json, visual_brief.md, slides_outline.md, publishing_checklist.md, README.md, manifest.json | blocked / partial / ready | caption aprovada + asset (optional) |
| Reels Script | `offline package-reels <queue_id>` | caption.md, script.md, shot_list.md, voiceover.md, editing_notes.md, publishing_checklist.md, README.md, manifest.json | blocked / ready | caption aprovada |
| Post Simples | `offline package-post <queue_id>` | caption.md, hashtags.md, cta.md, publishing_checklist.md, README.md, manifest.json | blocked / partial / ready | caption aprovada + asset (optional) |
| Validacao | `offline validate <package_id>` | (score + relatorio no terminal) | score 0-100 | pacote existente em disco |
| ZIP Export | `offline zip <package_id>` | exports/offline_factory_zips/<package_id>.zip | ok / erro | pacote existente em disco |

---

## Comandos de Listagem e Inspecao

| Comando | Descricao |
|---|---|
| `offline list` | Lista todos os pacotes em exports/offline_factory/ |
| `offline show <package_id>` | Detalhes completos de um pacote |
| `offline validate <package_id>` | Score de integridade 0-100 |
| `offline zip <package_id>` | Gera ZIP para entrega manual |

---

## Status dos Pacotes

| Status | Significado |
|---|---|
| `blocked` | Caption ausente — nao e possivel gerar o pacote |
| `partial` | Caption presente, asset ausente — pacote incompleto mas utilizavel |
| `ready` | Caption + asset presentes — pacote pronto para publicacao manual |
| `exported` | Pacote zipado e enviado |

---

## Entregaveis Futuros (nao implementados)

| Tipo | Fase | Descricao |
|---|---|---|
| Asset Assignment | P1.9 | Atribuir video/imagem ao slot, elevando partial -> ready |
| HTML Preview | P2.0 | Render visual do pacote em browser |
| Video Edit Plan | P2.1 | Plano de edicao com timeline para ffmpeg |
| Campaign 10 Posts | P2.2 | Pacote de campanha com 10 posts em batch |
| Manual Tracker | P2.3 | Registrar publicacao manual de volta no sistema |
| Client Delivery ZIP | P2.4 | ZIP formatado para envio a cliente |
| Quality Score | P2.5 | Score de qualidade do conteudo |

---

## Saida de Arquivos

```text
exports/
  offline_factory/
    carousel_<queue_id>_<timestamp>/
      caption.md
      seo_metadata.json
      visual_brief.md
      slides_outline.md
      publishing_checklist.md
      README.md
      manifest.json
    reels_<queue_id>_<timestamp>/
      ...
    post_<queue_id>_<timestamp>/
      ...
  offline_factory_zips/
    <package_id>.zip
```

Todos os arquivos sao gitignored. Nao sobem pro GitHub.

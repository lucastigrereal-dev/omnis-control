# OMNIS State After P1.7 — Offline Delivery Factory

**Data:** 2026-05-09
**Branch:** master
**Commit:** (ver apos commit da P1.7)
**Testes:** 788 (base P1.6A) + 63 (P1.7) = ~851

---

## O que P1.7 entregou

1. **Offline Delivery Factory** — modulo `src/offline_factory/`
2. **Pacote de Carrossel** — 6 arquivos: caption, seo_metadata, visual_brief, slides_outline, publishing_checklist, manifest
3. **Pacote de Reels Script** — 7 arquivos: caption, script, shot_list, voiceover, editing_notes, publishing_checklist, manifest
4. **Manifesto JSON** — indice completo com package_id, status, files, warnings, blockers, next_actions
5. **CLI `offline`** — 4 comandos: package-carousel, package-reels, list, show
6. **Status automatico** — blocked (sem caption) / partial (sem asset) / ready (completo)
7. **63 novos testes** — models, manifest, packager, CLI
8. **Blueprint video pipeline** — plano para ffmpeg + Whisper (nao implementado)
9. **GO/NO-GO claro** — producao offline=GO, OAuth=NO-GO, post real=NO-GO

---

## Arquitetura de Modulos

```
src/offline_factory/
  models.py      — DeliveryPackage, PackageType, PackageStatus
  manifest.py    — generate_manifest(), read_manifest()
  packager.py    — create_carousel_package(), create_reels_script_package(), list_packages()
  errors.py      — OfflineFactoryError e subclasses
  __init__.py    — exports publicos
```

---

## Saida de Pacotes

```
exports/offline_factory/<package_id>/
  (gitignored — nao sobe pro GitHub)
```

---

## Bloqueios Ativos

- **OAuth Meta** — 4 vars pendentes no .env (META_APP_SECRET, INSTAGRAM_BUSINESS_ACCOUNT_ID, FACEBOOK_PAGE_ID, META_GRAPH_VERSION)
- **Post real** — bloqueado ate OAuth completo + revisao humana

---

## Proxima Fase Recomendada

**P1.6 (Manual Credential Validation Gate):**

Lucas preenche manualmente no `.env`:
1. `META_APP_SECRET` — em developers.facebook.com/apps/1434393165369254
2. `META_GRAPH_VERSION=v20.0`
3. `INSTAGRAM_BUSINESS_ACCOUNT_ID=<valor>`
4. `FACEBOOK_PAGE_ID=<valor>`

Depois rodar:
```bash
python jarvis.py oauth probe
python jarvis.py oauth accounts
python jarvis.py oauth account-readiness @afamiliatigrereal
```

Nenhum codigo novo necessario para P1.6 — e tarefa manual.

---

## Comandos Uteis

```bash
python jarvis.py offline --help
python jarvis.py offline package-carousel 0b79aa1c
python jarvis.py offline list
python jarvis.py offline show carousel_0b79aa1c
python jarvis.py post preflight
python jarvis.py oauth probe
python -m pytest tests/offline_factory/ -v
python -m pytest tests/ -q
```

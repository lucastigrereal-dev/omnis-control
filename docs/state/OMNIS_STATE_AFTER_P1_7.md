# OMNIS State After P1.7b — Offline Delivery Factory + Pillow Fix

**Data:** 2026-05-09
**Branch:** master
**Commits:** P1.7 (f5b947b) + P1.7b (pendente commit)
**Testes:** 788 (base P1.6A) + 68 (P1.7) = ~856

---

## O que P1.7 entregou

1. **Offline Delivery Factory** — modulo `src/offline_factory/`
2. **Pacote de Carrossel** — 6 arquivos: caption, seo_metadata, visual_brief, slides_outline, publishing_checklist, manifest
3. **Pacote de Reels Script** — 7 arquivos: caption, script, shot_list, voiceover, editing_notes, publishing_checklist, manifest
4. **Manifesto JSON** — indice completo com package_id, status, files, warnings, blockers, next_actions
5. **CLI `offline`** — 4 comandos: package-carousel, package-reels, list, show
6. **Status automatico** — blocked (sem caption) / partial (sem asset) / ready (completo)
7. **68 novos testes** — models, manifest, packager, CLI
8. **Blueprint video pipeline** — plano para ffmpeg + Whisper (nao implementado)
9. **GO/NO-GO claro** — producao offline=GO, OAuth=NO-GO, post real=NO-GO

---

## O que P1.7b entregou

1. **Pillow 12.2.0 instalado** — elimina bloqueio pre-existente `ModuleNotFoundError: No module named 'PIL'`
2. **`pyproject.toml`** — `"Pillow>=10.0.0"` formalizado em `dependencies`
3. **`_load_caption` corrigido** — `DraftsManager().list_all()` com prefixo match (`startswith`)
4. **Unicode fix CLI** — `->` em vez de `->` para compatibilidade Windows cp1252
5. **Smoke real executado** — `carousel_0b79aa1c_20260509_082453`, status=partial, @lucastigrereal, 6 arquivos
6. **Docs atualizados** — smoke doc, handoff, state

---

## Smoke Package Gerado

| Campo | Valor |
|---|---|
| Package ID | carousel_0b79aa1c_20260509_082453 |
| Status | partial |
| Conta | @lucastigrereal |
| Caption ID | 1d482d8231e3 |
| Arquivos | 6 |
| Warning | Nenhum asset atribuido ao slot |

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
- **Asset slot vazio** — pacotes ficam `partial` ate P1.8 ser implementada

---

## Proximas Fases

| Fase | Descricao | Prioridade |
|---|---|---|
| P1.8 | Asset Assignment Center — atribuir video/imagem ao slot | Alta |
| P1.9 | Campaign Package — 10 posts em batch | Media |
| P2.0 | Real Render Engine — ffmpeg + Whisper | Media |
| P1.6 | Manual OAuth Gate — Lucas preenche credenciais Meta | Manual |

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

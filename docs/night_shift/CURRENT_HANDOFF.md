# CURRENT HANDOFF — P1.7 → P1.6

**Data:** 2026-05-09 | **Turno:** Diurno | **Operador:** Lucas

---

## O que P1.7 entregou

1. **Offline Delivery Factory** — `src/offline_factory/` completo
2. **Pacotes locais** — carrossel (6 arquivos) + reels script (7 arquivos) + manifest.json
3. **CLI `offline`** — package-carousel, package-reels, list, show
4. **Status automatico** — blocked / partial / ready sem chamar Meta
5. **63 novos testes** — models, manifest, packager, CLI
6. **Documentacao** — 4 docs + report + go-no-go + state

---

## Comandos Novos (P1.7)

```bash
python jarvis.py offline --help
python jarvis.py offline package-carousel 0b79aa1c
python jarvis.py offline package-carousel 0b79aa1c --slides 7
python jarvis.py offline package-reels 0b79aa1c
python jarvis.py offline list
python jarvis.py offline show <package_id_prefix>
```

---

## Estado dos Repos

| Repo | Branch | Commit | Push? |
|---|---|---|---|
| omnis-control | master | (P1.7 commit) | NAO |
| publisher-os | argos-evolucao-passo-0 | cf4b8d7 | NAO |

---

## Bloqueios Ativos (sem alteracao)

- **@lucastigrereal**: CRITICAL — hard block para OAuth
- **@afamiliatigrereal**: MEDIUM — candidata recomendada

---

## Para retomar (P1.6)

Lucas precisa fazer MANUALMENTE no `.env` de publisher-os:

1. `META_APP_SECRET=<valor>` — em developers.facebook.com/apps/1434393165369254
2. `META_GRAPH_VERSION=v20.0`
3. `INSTAGRAM_BUSINESS_ACCOUNT_ID=<valor>` — no Meta Business Suite
4. `FACEBOOK_PAGE_ID=<valor>` — na pagina do Facebook

Depois verificar com:
```bash
python jarvis.py oauth probe
python jarvis.py oauth accounts
python jarvis.py oauth account-readiness @afamiliatigrereal
```

**Nenhum codigo novo necessario para P1.6.**

---

## Comandos Uteis

```bash
python -m pytest tests/offline_factory/ -v
python -m pytest tests/ -q
python jarvis.py offline package-carousel 0b79aa1c
python jarvis.py post preflight
python jarvis.py oauth probe
python jarvis.py oauth validate
python jarvis.py oauth accounts
python jarvis.py oauth account-readiness @afamiliatigrereal
```

---

**Handoff limpo. P1.7 entregue. Proximo: P1.6 quando Lucas destravar credenciais Meta.**

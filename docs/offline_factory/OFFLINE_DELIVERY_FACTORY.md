# Offline Delivery Factory — P1.7

**O que faz:** Gera pacotes de conteudo offline (arquivos locais) a partir de itens da fila.
**O que NAO faz:** Nunca chama Meta. Nunca publica. Nunca agenda. Nunca modifica o .env.

---

## Comandos

```bash
python jarvis.py offline --help
python jarvis.py offline package-carousel <queue_id>
python jarvis.py offline package-carousel <queue_id> --slides 7
python jarvis.py offline package-carousel <queue_id> --json
python jarvis.py offline package-reels <queue_id>
python jarvis.py offline package-reels <queue_id> --json
python jarvis.py offline list
python jarvis.py offline list --json
python jarvis.py offline show <package_id>
python jarvis.py offline show <package_id_prefix>
python jarvis.py offline show <package_id> --json
```

---

## Estrutura de um Pacote de Carrossel

```
exports/offline_factory/carousel_<queue_id>_<timestamp>/
  caption.md              — legenda aprovada (ou placeholder)
  seo_metadata.json       — metadados SEO: title, description, hashtags
  visual_brief.md         — direcao visual por perfil/nicho
  slides_outline.md       — estrutura de slides numerados (hook → corpo → CTA)
  publishing_checklist.md — checklist de publicacao especifico para carrossel
  README.md               — sumario: status, arquivos, warnings, blockers
  manifest.json           — indice completo com tamanhos e metadados
```

## Estrutura de um Pacote de Reels Script

```
exports/offline_factory/reels_<queue_id>_<timestamp>/
  caption.md              — legenda aprovada (ou placeholder)
  script.md               — roteiro: hook (0-3s), corpo (3-25s), CTA (25-30s)
  shot_list.md            — tabela de cenas: tipo, descricao, duracao, transicao
  voiceover.md            — guia de voz: tom, velocidade, pausas
  editing_notes.md        — sequencia de edicao + software sugerido
  publishing_checklist.md — checklist especifico para Reels
  README.md               — sumario do pacote
  manifest.json           — indice completo
```

---

## Status do Pacote

| Status | Significado |
|--------|-------------|
| `blocked` | Caption ausente — aprovar legenda antes |
| `partial` | Caption presente mas falta asset, CTA ou hashtags |
| `ready` | Caption + asset + CTA + hashtags — pronto para revisao humana |
| `draft` | Criado mas incompleto |
| `exported` | Exportado para producao |

---

## Fluxo de uso

```
1. python jarvis.py queue list              — ver itens na fila
2. python jarvis.py captions list           — ver legendas disponiveis
3. python jarvis.py offline package-carousel <queue_id>
4. Revisar arquivos em exports/offline_factory/<package_id>/
5. Abrir README.md para ver status, warnings e next actions
6. Resolver blockers (aprovar legenda, atribuir asset)
7. python jarvis.py post preflight          — verificar readiness para OAuth
```

---

## Limitacoes Atuais (P1.7)

- Nenhum asset visual e atribuido automaticamente (sempre `partial` sem asset manual)
- Video rendering nao implementado (ver VIDEO_EDITING_PIPELINE_PLAN.md)
- Pacotes sao gerados sempre com timestamp novo — nao ha deduplicacao por queue_id
- `exports/offline_factory/` esta no .gitignore — nao sobe pro GitHub

# Wave G33 — Local UX Sprint
**Data:** 2026-05-18
**Branch base:** feature/omnis-5waves-runtime-supreme
**Objetivo:** Transformar OMNIS Local Supreme em produto operável com comandos simples, preview visual e ritual semanal.

## Sumário
3 fases independentes executáveis em paralelo ou sequência.
Nenhuma fase toca os mesmos arquivos.
Sem integrações externas. Sem push. Sem deploy.

---

## Squad A — Local Commands CLI

**Branch:** feature/omnis-5waves-runtime-supreme (mesma, não precisa worktree)
**Fase:** W-G1

### Escopo permitido
- `src/cli_local.py` (novo)
- `src/cli.py` (adicionar grupo `local`)
- `tests/cli/test_local_commands.py` (novo)

### Escopo proibido
- `src/executors/`
- `src/reports/`
- `missions/`
- `cockpit/`

### Entregáveis
- `omnis local campaign --profile TEXT --theme TEXT --objective TEXT`
- `omnis local carousel --profile TEXT --theme TEXT`
- `omnis local reels --profile TEXT --theme TEXT`
- `omnis local app --name TEXT --domain TEXT`
- `omnis local forge --skill-name TEXT --description TEXT`
- `omnis local cockpit` — exibe caminho cockpit/index.html
- `omnis local status` — resume missions/ dir
- dry_run=True universal
- Cada comando gera mission stub (mission_contract.json + 01_mission_brief.md)
- ≥5 testes passando

### Critério de aceite
```
python -m pytest tests/cli/ --import-mode=importlib -p no:warnings -v
→ PASS
```

---

## Squad B — Carousel Preview HTML

**Branch:** feature/omnis-g33-carousel-preview (novo worktree se paralelo)
**Fase:** W-G2

### Escopo permitido
- `src/preview/carousel_preview.py` (novo)
- `cockpit/carousel_preview.html` (novo)
- `cockpit/carousel_styles.css` (novo se necessário)
- `tests/preview/test_carousel_preview.py` (novo)

### Escopo proibido
- `src/cli.py`
- `missions/`
- Qualquer arquivo de missão existente

### Entregáveis
- Parser de `missions/<MIS>/05_outputs/estrutura_slide_a_slide.md` → `slides_data.json`
- `carousel_preview.html` com navegação prev/next
- Versão print-friendly
- Sem Canva API, sem backend, sem externo
- ≥3 testes

### Critério de aceite
```
python -m pytest tests/preview/ --import-mode=importlib -p no:warnings -v
→ PASS
Abrir cockpit/carousel_preview.html → slides navegáveis
```

---

## Squad C — Weekly Production Ritual

**Branch:** feature/omnis-g33-weekly-ritual (novo worktree se paralelo)
**Fase:** W-G3

### Escopo permitido
- `src/weekly/weekly_pack.py` (novo)
- `src/weekly/__init__.py` (novo)
- `tests/weekly/test_weekly_pack.py` (novo)
- docs/WEEKLY_PRODUCTION_RITUAL_REPORT.md (novo)

### Escopo proibido
- `src/cli.py` (Squad A cuida)
- `missions/` existente (apenas criar novos)
- Qualquer integração externa

### Entregáveis
- `WeeklyPackOrchestrator` — recebe projeto, nicho, objetivo, cidade, canal
- Gera: 7 posts, 7 stories, 5 roteiros Reels, 1 carrossel, 1 proposta, 1 learning update
- `final_package_manifest.json` + estrutura de pasta
- dry_run=True padrão
- ≥5 testes

### Critério de aceite
```
python -m pytest tests/weekly/ --import-mode=importlib -p no:warnings -v
→ PASS
WeeklyPackOrchestrator(dry_run=True).run(...) → manifest JSON válido
```

---

## Ordem de Merge

1. Squad A (W-G1) → rodar suite completa
2. Squad B (W-G2) → rodar suite completa
3. Squad C (W-G3) → rodar suite completa
4. Full suite final → confirmar 0 regressões nos módulos novos

---

## Testes de Regressão (após cada merge)

```sh
python -m pytest tests/ --import-mode=importlib -p no:warnings -q \
  --ignore=tests/caption_approval_v2 \
  --ignore=tests/creative_production_v2
```
Alvo: 0 novas falhas além das 8 pré-existentes.

---

## Riscos

| Risco | Probabilidade | Mitigação |
|---|---|---|
| cli.py conflicts (Squad A + C ambos modificam) | Média | Squad A entrega primeiro; Squad C só adiciona `local weekly-pack` depois |
| Carousel parser quebra em missão sem estrutura_slide_a_slide | Baixa | Graceful fallback: usa placeholder slides |
| Weekly pack gera muito volume | Baixa | dry_run=True + limite configurável de outputs |

---

## Handoff Prompts

### Squad A
```
Implementar grupo CLI `omnis local` em src/cli_local.py e registrar em src/cli.py.
Comandos: campaign, carousel, reels, app, forge, cockpit, status.
dry_run=True universal. Gerar mission stub em missions/. Testes em tests/cli/.
```

### Squad B
```
Implementar src/preview/carousel_preview.py que parseia
missions/<MIS>/05_outputs/estrutura_slide_a_slide.md →
slides_data.json → cockpit/carousel_preview.html navegável.
Testes em tests/preview/. Sem APIs externas.
```

### Squad C
```
Implementar src/weekly/weekly_pack.py com WeeklyPackOrchestrator.
Input: projeto, nicho, objetivo, cidade, canal.
Output: 7 posts + 7 stories + 5 reels + 1 carrossel + 1 proposta + manifest.
dry_run=True padrão. Testes em tests/weekly/.
```

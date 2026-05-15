# WAVE 009 — Recovery Prompts System

## Objetivo
Criar sistema de prompts de recuperacao: para cada wave, gerar prompt que permite retomar execucao exatamente de onde parou. Garantir que interrupcoes nao causem perda de contexto.

## Setor principal
Operacoes & Organizacao (Setor 7)

## Skills ativadas
writing-plans, sc:document, humanizer, jarvis-memory-write

## Dependencias
W008 (progress tracking)

## Arquivos permitidos
`docs/supreme_210/prompts/`, `docs/supreme_210/`

## Arquivos proibidos
`src/`, `tests/`, `.env`

## Risco
**LOW** — Apenas documentacao

## Testes obrigatorios
Cada prompt gerado deve conter: wave, bloco, contexto suficiente para retomar

## Rollback
N/A

---

## Blocos

### B1 — Prompt template
Definir template padrao de prompt de retomada: wave, bloco, estado, contexto, comandos.

### B2 — Recovery prompt generator
Script que gera prompt de retomada a partir do estado atual do progress tracking.

### B3 — Blocker prompt template
Template para quando wave esta BLOCKED: motivo, o que precisa, opcoes.

### B4 — Session resume prompt
Template para retomar sessao inteira: ultimas N waves, status, proximo passo.

### B5 — Context snapshot
O que incluir no prompt para que o executor entenda o momento sem reler tudo.

### B6 — Prompt index
Criar `prompts/INDEX.md` com todos os prompts gerados, organizados por wave.

### B7 — W001-W005 recovery prompts
Gerar prompts de retomada para as primeiras 5 waves.

### B8 — W006-W010 recovery prompts
Gerar prompts de retomada para W006-W010.

### B9 — Auto-prompt hook
Integrar com progress tracker: ao marcar wave como BLOCKED, gerar prompt automaticamente.

### B10 — Wave validation and report
Consolidar, gerar `reports/WAVE_009_REPORT.md`.

---

**Status:** PLANNED

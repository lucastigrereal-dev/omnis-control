# HANDOFF — WAVE 1: Agência Camada 3 — Carrossel + Thumbnail

**Data:** 2026-05-25
**Commit:** `272b5cb`
**Módulo:** `src/agencia/carrossel.py`
**Testes:** `tests/agencia/test_carrossel.py` — 27/27 passed
**Prova:** 7 arquivos reais em `output/agencia/oinatalrn/2026-05-25/`

## O que foi entregue

`CarrosselGenerator` — geração local de carrossel PNG + thumbnail PNG via PIL/Pillow.

### Estrutura de slides
```
slide_00_capa    → título grande + @perfil
slide_01..N_slide → conteúdo (uma bullet por slide)
slide_final_cta  → "Curtiu? Veja mais no link da bio ↗"
thumbnail        → 1280x720 com título + @perfil
```

### Uso
```python
from src.agencia.carrossel import CarrosselGenerator
from pathlib import Path

gen = CarrosselGenerator(dry_run=False)
result = gen.generate(
    title="Hotel Vista Mar",
    slides=["Piscina privativa", "Café da manhã gourmet", "Vista pro mar"],
    perfil="oinatalrn",
    output_dir=Path("output/agencia/oinatalrn/2026-05-25"),
)
print(result.summary())
```

### dry_run
- `dry_run=True`: manifesto JSON gerado, zero PNG criado
- `dry_run=False`: PNGs reais + manifesto

### Paletas por perfil
| Perfil | Fundo | Accent |
|---|---|---|
| lucastigrereal | #1a1a2e | #f5a623 |
| oinatalrn | #0d3b66 | #ffd700 |
| agenteviajabrasil | #0a5c36 | #f5a623 |
| afamiliatigrereal | #4a1942 | #ff69b4 |
| oquecomernatalrn | #8b1a1a | #ffd700 |
| natalaivoueu | #1a3c5e | #00bfff |

### Anti-teatro confirmado
```
Título passado:    ANTI_TEATRO_WAVE1_CHECKSUM
Título no disco:   ANTI_TEATRO_WAVE1_CHECKSUM
Match: True
```

## KRATOS pode exibir
- `GET /agencia/carrossel/{session_id}` → serve manifesto JSON com paths dos slides
- Cards de preview de carrossel (futura rota)

## Próxima integração
- Conectar ao `AgenciaPipeline.run()` — após gerar clipes, chamar `CarrosselGenerator.generate(title=hook, slides=[...], ...)`
- Decidir: texto dos slides vem dos hooks detectados ou de input manual do Lucas

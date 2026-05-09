# P1.7 — Smoke Test: queue_id 0b79aa1c

**Data:** 2026-05-09
**Queue ID:** 0b79aa1c
**Draft ID:** 1d482d82

---

## Resultado: BLOQUEADO (pre-existente)

O smoke `python jarvis.py offline package-carousel 0b79aa1c` nao pode ser executado
porque `PIL` (Pillow) nao esta instalado no `.venv`.

```
ModuleNotFoundError: No module named 'PIL'
```

A cadeia de imports e:
```
jarvis.py
  → src/cli.py
  → src/cli_commands/creative_cmd.py
  → src/creative_production/exporter.py
  → src/creative_production/mock_image_generator.py
  → from PIL import Image, ImageDraw, ImageFont  ← FALHA AQUI
```

Este bloqueio e **pre-existente** (existia antes da P1.7).
Todos os outros comandos CLI (`python jarvis.py status`, `doctor`, etc.)
tambem falham pelo mesmo motivo.

---

## O que funcionou

Os testes P1.7 passam 100% (68/68) porque importam diretamente:
- `from src.offline_factory import create_carousel_package`
- `from src.cli_commands.offline_factory_cmd import offline_app`

A offline_factory NAO depende de PIL. O bloqueio e no creative_cmd.py.

---

## Como resolver (futuro)

```bash
cd C:\Users\lucas\omnis-control
.venv\Scripts\pip install Pillow
python jarvis.py offline package-carousel 0b79aa1c
```

Ou tornar PIL opcional em `mock_image_generator.py`:
```python
try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
```

---

## Status dos Testes

```
tests/offline_factory/: 68/68 PASS ✅
jarvis.py (CLI real): BLOQUEADO por PIL (pre-existente) ❌
```

# P1.7b — Smoke Test: queue_id 0b79aa1c

**Data:** 2026-05-09
**Queue ID:** 0b79aa1c
**Draft ID:** 1d482d8231e3

---

## Resultado: SUCESSO (partial — esperado)

```
python jarvis.py offline package-carousel 0b79aa1c
```

Pacote gerado com status `partial` — correto, pois nenhum asset visual foi atribuido ao slot.

---

## Pacote Gerado

| Campo | Valor |
|---|---|
| Package ID | carousel_0b79aa1c_20260509_082453 |
| Tipo | carousel_package |
| Conta | @lucastigrereal |
| Queue ID | 0b79aa1c |
| Caption ID | 1d482d8231e3 |
| Status | partial |
| Gerado em | 2026-05-09T11:24:53Z |

---

## Arquivos (6)

| Arquivo | Tamanho |
|---|---|
| caption.md | 336 bytes |
| seo_metadata.json | 675 bytes |
| visual_brief.md | 696 bytes |
| slides_outline.md | 683 bytes |
| publishing_checklist.md | 500 bytes |
| README.md | 606 bytes |
| manifest.json | (indice) |

---

## Warning (esperado)

```
! Nenhum asset atribuido ao slot — pacote parcial
```

Status `partial` e o comportamento correto quando nao ha asset. O pacote fica pronto para receber o video/imagem na P1.8 (Asset Assignment Center).

---

## Fix P1.7b incluido neste smoke

- **Pillow 12.2.0 instalado** — resolve pre-existente `ModuleNotFoundError: No module named 'PIL'`
- **`pyproject.toml`** — `"Pillow>=10.0.0"` adicionado em `dependencies`
- **`_load_caption` corrigido** — usa `DraftsManager().list_all()` com prefixo match (`startswith`)
- **Unicode fix** — `->` em vez de `->` no CLI (Windows cp1252)

---

## Status dos Testes

```
tests/offline_factory/: 68/68 PASS
jarvis.py (CLI real):   FUNCIONAL (smoke OK)
```

---

## Proxima fase

**P1.8 Asset Assignment Center** — permite atribuir video/imagem ao slot, elevando status de `partial` para `ready`.

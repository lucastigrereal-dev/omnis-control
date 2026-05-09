# Quality Layer

**Modulo:** `src/quality_layer/`
**Fase:** P2.1
**Status:** Ativo

---

## Responsabilidade

Score 0-100 para pacotes offline.
Criterio: 90+ = ready_for_human_review | 70-89 = needs_adjustment | <70 = blocked

---

## Checks

| Check | Peso | Descricao |
|---|---|---|
| manifest_exists | critical (20) | Manifest.json presente |
| manifest_valid_json | critical (20) | JSON valido |
| no_secret_patterns | critical (20) | Sem secrets |
| manifest_has_package_id | high (10) | Campo package_id presente |
| manifest_has_status | high (10) | Campo status presente |
| caption_exists | high (10) | caption.md presente |
| caption_not_empty | high (10) | caption.md nao vazio |
| checklist_exists | medium (5) | publishing_checklist.md |
| package_status_consistent | medium (5) | Status valido |
| render_html_exists | medium (5) | preview.html renderizado |
| asset_present_or_warned | medium (5) | Asset referenciado |

---

## CLI

```bash
python jarvis.py quality package <id>
python jarvis.py quality package <id> --json
```

---

## Regras

- Nunca chama Meta
- Score puramente operacional (sem IA subjetiva)
- Patchavel em testes

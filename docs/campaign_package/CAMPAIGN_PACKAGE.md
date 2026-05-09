# Campaign Package

**Modulo:** `src/campaign_package/`
**Fase:** P2.2
**Status:** Ativo

---

## Responsabilidade

Gera pacote de campanha local com N posts (padrao: 10).
Sem OAuth. Sem Meta. Sem publicacao.

---

## Estrutura de saida

```
exports/campaigns/<campaign_id>/
  campaign_manifest.json
  calendar.csv
  README.md
  publishing_checklist.md
  posts/
    post_01/README.md
    post_02/README.md
    ...
    post_10/README.md
```

---

## CLI

```bash
python jarvis.py campaign create --name "Natal 2026" --count 10
python jarvis.py campaign list
python jarvis.py campaign show <campaign_id>
python jarvis.py campaign validate <campaign_id>
python jarvis.py campaign zip <campaign_id>
```

---

## Regras

- Max 50 posts por campanha
- Nunca chama Meta
- Nunca publica
- Sem secrets em arquivos de saida

# Client Delivery

**Modulo:** `src/client_delivery/`
**Fase:** P2.4
**Status:** Ativo

---

## Responsabilidade

Transforma pacote ou campanha em entrega comercial organizada.
Pronta para mandar para humano/cliente.
Sem OAuth. Sem Meta. Sem publicacao automatica.

---

## Estrutura de saida

```
exports/client_delivery/<delivery_id>/
  README_CLIENTE.md
  RESUMO_EXECUTIVO.md
  delivery_manifest.json
  content/  (copia do source package ou campaign)

exports/client_delivery_zips/<delivery_id>.zip
```

---

## CLI

```bash
python jarvis.py delivery create --from-package <package_id>
python jarvis.py delivery create --from-campaign <campaign_id>
python jarvis.py delivery list
python jarvis.py delivery show <delivery_id>
python jarvis.py delivery zip <delivery_id>
```

---

## Regras

- Nunca chama Meta
- Nunca publica
- Sem secrets nos arquivos de saida
- Fonte deve existir (package ou campaign)

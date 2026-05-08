# P1.5 — Meta Config Alignment

**Data:** 2026-05-08

---

## Fonte Canonica

```
C:\Users\lucas\publisher-os\.env
```

Este e o unico arquivo de configuracao Meta reconhecido pelo sistema.

---

## Variaveis por Fase

### Fase OAuth Setup (necessarias para iniciar fluxo OAuth)

| Variavel | Status Atual | Notas |
|---|---|---|
| `META_APP_ID` | `present` | ID `1434393165369254` |
| `META_APP_SECRET` | `empty` | Pegar no Meta Developers |
| `META_REDIRECT_URI` | `present` | `http://localhost:8000/api/v1/argos/oauth/callback` |
| `META_GRAPH_VERSION` | `missing` | Adicionar `v20.0` ou `v21.0` |

### Fase Publicacao (necessarias para publicar conteudo)

| Variavel | Status Atual | Notas |
|---|---|---|
| `INSTAGRAM_BUSINESS_ACCOUNT_ID` | `empty` | Atualmente usando nome antigo `INSTAGRAM_BUSINESS_ID` |
| `FACEBOOK_PAGE_ID` | `missing` | Opcional para MVP |
| `META_ACCESS_TOKEN` | `missing` | Sera gerado pelo fluxo OAuth |

---

## Aliases Temporarios (depreciar no futuro)

| Alias | Canonico | Status |
|---|---|---|
| `INSTAGRAM_BUSINESS_ID` | `INSTAGRAM_BUSINESS_ACCOUNT_ID` | Encontrado no .env, vazio |
| `META_SECRET` | `META_APP_SECRET` | Para compatibilidade |
| `CALLBACK_URL` | `META_REDIRECT_URI` | Para compatibilidade |

O `env_probe.py` reconhece esses aliases e reporta `alias_present` quando encontra um.

---

## Regras

1. **NAO COPIAR** valores entre `omnis-control/.env` e `publisher-os/.env`.
2. **NAO COMMITAR** `.env`.
3. **NAO IMPRIMIR** valores de META_APP_SECRET, token ou credenciais.
4. **NAO UNIFICAR** os .env agora.
5. `omnis-control/.env` = config local OMNIS (dev).
6. `publisher-os/.env` = credenciais operacionais Publisher/Meta.

---

## Como o OMNIS le estas variaveis

O `env_probe.py`:
1. Le `~/publisher-os/.env` linha por linha
2. Classifica cada variavel como `present`, `missing`, `empty`, `invalid_format`, ou `alias_present`
3. **NUNCA** armazena ou retorna os valores
4. So reporta status

Comandos:
```bash
python jarvis.py oauth probe       # Status seguro
python jarvis.py oauth validate    # Probe + readiness + GO/NO-GO
```

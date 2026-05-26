# HANDOFF — Aurora Frente 1: Notion REST Real

**Data:** 2026-05-25
**Commit:** `0ab4498`
**Módulo:** `src/aurora/context_engine.py` — `_fetch_notion()`
**Testes:** `tests/aurora/test_context_engine.py` — 34/34 passed

---

## O que foi feito

Substituiu o stub `_fetch_notion` por implementação real via `urllib.request` (zero dependências extras).

### Implementação

```python
payload = json.dumps({"query": query, "page_size": min(max_results, 20)})
req = urllib.request.Request(
    "https://api.notion.com/v1/search",
    data=payload.encode("utf-8"),
    headers={
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    },
    method="POST",
)
with urllib.request.urlopen(req, timeout=8) as resp:
    data = json.loads(resp.read())
```

### Extração de título

O formato do título varia entre `page` e `database` no Notion:
- **Page:** em `properties.<qualquer prop>.type == "title"` → `prop.title[].plain_text`
- **Database:** em `item.title[].plain_text` (campo top-level)

O código tenta as duas formas — se nenhuma funcionar, usa `[{type} sem título]`.

### Graceful degradation

- `NOTION_TOKEN` ausente → retorna `[]` imediatamente
- `HTTPError` (401 Unauthorized, 403, etc.) → capturado → retorna `[]`
- Qualquer exceção de rede → capturado → retorna `[]`
- API retorna 0 resultados → retorna `[]` sem crash

---

## Estado atual

**Token:** válido — `ntn_f937391284091...` (não commitar)
**Resultado:** API retorna `{"results": []}` — **0 páginas acessíveis**

### Por que 0 resultados?

O Notion exige que cada página/database seja **explicitamente compartilhada** com a integração.
A integração foi criada mas nenhuma página foi compartilhada com ela ainda.

---

## Como fazer o Notion funcionar

### 1. Setar o token como variável de ambiente

```powershell
$env:NOTION_TOKEN = "ntn_f937391284091..."
```

**NUNCA commitar o token.** Mover para `.env` (não lido pelo agente).

### 2. Compartilhar páginas no Notion UI

Para cada página/database que a Aurora deve ler:

1. Abrir a página no Notion
2. Clicar em **Share** (canto superior direito)
3. No campo de busca, digitar o nome da integração OMNIS
4. Clicar em **Invite**

Sem isso, a API retorna `{"results": []}` mesmo com token válido.

### 3. Testar após compartilhar

```python
import os
os.environ["NOTION_TOKEN"] = "ntn_f937391284091..."
from src.aurora.context_engine import ContextEngine
engine = ContextEngine(data_dir=Path("data"))
ctx = engine.build(query="hoteis publicidade")
print(ctx.sources_available)  # deve incluir "notion"
print([r for r in ctx.results if r.source == "notion"])
```

---

## Testes cobertos

| Teste | Cenário |
|---|---|
| `TestNotionAusente::test_notion_ausente_nao_ativado` | Env ausente → notion não em sources_available |
| `TestNotionAusente::test_notion_token_presente_ativa_fonte` | Token presente, API retorna 401 → captura interna → notion em sources_available |
| `TestFetchNotionSemToken` | Token ausente → retorna [] |
| `TestFetchNotionTokenInvalido` | HTTPError 401 → captura → retorna [] |
| `TestFetchNotionRetornaResultados` | Mock API com 1 page → ContextResult com source="notion" |
| `TestBuildComNotionDisponivel` | Mock urllib → notion em sources_available com resultado |

---

## Próxima ação

1. Lucas compartilha as páginas relevantes com a integração OMNIS no Notion UI
2. Setar `NOTION_TOKEN` permanentemente (via `.env`)
3. Rodar `engine.build(query="leads hoteis")` e confirmar resultados reais
4. Decidir quais databases/páginas são relevantes para o contexto da Aurora (leads, pipeline, projetos)

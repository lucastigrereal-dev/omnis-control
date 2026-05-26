# HANDOFF — Aurora Frente 2: Akasha (pgvector) Real

**Data:** 2026-05-25
**Commit:** `0ab4498`
**Módulo:** `src/aurora/context_engine.py` — `_fetch_akasha()`
**Testes:** `tests/aurora/test_context_engine.py` — 34/34 passed

---

## O que foi feito

Substituiu o stub `_fetch_akasha` por implementação real via `psycopg2`.

### Estratégia de busca

**Estratégia 1 — FTS (tsvector):**
```sql
SELECT dc.chunk_text, d.domain, d.file_name, d.file_type, dc.section_title,
       ts_rank(dc.tsv, plainto_tsquery('simple', %(q)s)) AS rank
FROM document_chunks dc
JOIN documents d ON dc.document_id = d.id
WHERE dc.tsv @@ plainto_tsquery('simple', %(q)s)
ORDER BY rank DESC
LIMIT %(limit)s
```

**Estratégia 2 — ILIKE fallback** (só se FTS retornar 0):
```sql
SELECT dc.chunk_text, d.domain, d.file_name, d.file_type, dc.section_title
FROM document_chunks dc
JOIN documents d ON dc.document_id = d.id
WHERE dc.chunk_text ILIKE %(pattern)s
LIMIT %(limit)s
```

### Conexão

```python
conn = psycopg2.connect(db_url, connect_timeout=3)
cur = conn.cursor()
cur.execute("SET statement_timeout = 5000")  # 5s por query
```

`connect_timeout=3` evita bloquear o `ThreadPoolExecutor` por mais de 3s na conexão.
`SET statement_timeout = 5000` — forma correta no psycopg2 2.9.11 (`set_session` não funciona com `options=`).

### Graceful degradation

- `AKASHA_DB_URL` ausente → retorna `[]` imediatamente (source não é ativada)
- `psycopg2` não instalado → retorna `[]` com log.warning
- `OperationalError` (banco fora do ar, senha errada) → capturado internamente → retorna `[]`
- FTS falha (tabela não existe, etc.) → capturado internamente, tenta ILIKE
- ILIKE falha → retorna `[]` com o que conseguiu
- `finally` sempre fecha conexão

**Consequência importante:** quando `_fetch_akasha` captura exceção internamente e retorna `[]`,
o `build()` considera que a fonte rodou com sucesso → `akasha` vai para `sources_available` (não `sources_failed`).
Apenas um `FuturesTimeoutError` ou exceção não capturada chegaria a `sources_failed`.

---

## Schema Akasha descoberto

Container: `akasha-postgres` — UP e HEALTHY em `:5432`
Credenciais: `postgresql://akasha:akasha123@localhost:5432/akasha`

**Tabela `documents`:**
- `id` (PK)
- `domain` — categoria do documento
- `file_name`
- `file_type`

**Tabela `document_chunks`:**
- `id` (PK)
- `document_id` (FK → documents.id)
- `chunk_text` — texto do chunk
- `section_title` — título da seção
- `tsv` — coluna `tsvector` indexada para FTS

---

## Estado atual do banco

O Akasha **está UP e conectável** mas contém **0 documentos** — sem ingestion ainda.
Qualquer query retorna 0 resultados (graceful — retorna `[]` sem crash).

Para popular: rodar pipeline de ingestion de documentos no Akasha.
Isso é onda separada (Wave P47 — decidir Docker + pipeline).

---

## Como ativar

```powershell
$env:AKASHA_DB_URL = "postgresql://akasha:akasha123@localhost:5432/akasha"
```

Com essa variável presente, `_fetch_akasha` é incluída no `build()`.
Sem ela, a fonte é silenciosamente ignorada.

---

## R01 — Credencial inline

A senha `akasha123` está hardcoded no connection string acima.
**Ação futura (Lucas):** trocar a senha e mover para `.env` → `os.getenv("AKASHA_DB_URL")`.
O código já usa `os.environ.get("AKASHA_DB_URL")` — só a variável de ambiente precisa mudar.

---

## Testes cobertos

| Teste | Cenário |
|---|---|
| `TestFetchAkashaSemEnv` | AKASHA_DB_URL ausente → retorna [] |
| `TestFetchAkashaEnvInvalido` | URL inválida → OperationalError → retorna [] |
| `TestBuildComAkashaDisponivel` | Mock psycopg2 retorna rows → ContextResult correto |
| `TestBuildComAkashaIndisponivel` | Mock connect lança erro → akasha em sources_available (captura interna) |
| `TestAkashaAusente` (2 testes) | Env ausente → akasha não em sources_failed nem sources_available |

---

## Próxima ação

Para a Aurora começar a receber contexto real do Akasha:
1. Criar pipeline de ingestion de documentos no Akasha (Wave P47 — aguarda decisão Lucas)
2. Setar `AKASHA_DB_URL` permanentemente (via `.env` após rotação de senha)
3. Testar com query real: `engine.build(query="hotel publicidade")`

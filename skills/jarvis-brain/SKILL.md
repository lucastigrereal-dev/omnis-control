---
name: jarvis-brain
description: |
  Agrega contexto antes de qualquer ação relevante. Consulta em paralelo:
  Akasha (busca_hibrida — semântico), Mem0+Kuzu (grafo relacional),
  Obsidian (biblioteca_sabedoria — declarativo), Docker state (operacional).
  SEMPRE chamada antes de jarvis-delegate.
trigger:
  - antes de qualquer skill setorial
  - usuário pede "lembra de" / "histórico de" / "o que sabemos sobre"
  - "busca [tema]"
  - "o que sei sobre X"
  - "contexto de [setor/projeto]"
  - "retoma [projeto]"
  - "onde parei em X"
sector: cross-cutting
risk: low
model: sonnet
approval_required: []
status: active
version: 1.0
absorbs:
  - knowledge-retriever  # depreciada
  - context-restorer     # depreciada
queries:
  - source: akasha
    method: busca_hibrida(query, top_k=10)
  - source: mem0
    method: graph_query(entities, relationships)
  - source: obsidian
    method: ripgrep --type md --max-count 5
  - source: docker
    method: docker ps + docker stats --no-stream
cost_estimate: "$0.002/run"
verification_criteria:
  - Cita fonte explicitamente por bloco
  - Similaridades < 0.50 não exibidas
  - Output ≤ 250 palavras
  - Síntese final em 1-2 frases acionáveis
---

# Skill: jarvis-brain

Motor de contexto do Jarvis. Merge de `knowledge-retriever` + `context-restorer` + nova camada Mem0+Kuzu.

## Quando usar

"lembra de X" / "histórico de Y" / "busca [tema]" / "o que sei sobre Z" / "retoma [projeto]" / **sempre antes de jarvis-delegate**

## Input

`query` — pergunta, tema, nome de projeto, ou intenção de ação

## Processo

### 1. Akasha — busca_hibrida (semântico + lexical)

```python
import requests, psycopg2

DB = {"host":"localhost","port":5432,"user":"akasha","password":"akasha123","database":"akasha"}
OLLAMA = "http://localhost:11434/api/embeddings"

def buscar_akasha(query: str, top_k: int = 10) -> list:
    r = requests.post(OLLAMA, json={"model":"nomic-embed-text","prompt":query}, timeout=30)
    emb = r.json().get("embedding")
    if not emb:
        return [{"erro": "Ollama offline"}]

    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    # Usa busca_hibrida() — pgvector (50%) + tsvector português (50%)
    cur.execute("""
        SELECT id, titulo, summary, score
        FROM busca_hibrida(%s, %s::vector, %s)
        WHERE score > 0.50
    """, (query, str(emb), top_k))

    rows = cur.fetchall()
    cur.close(); conn.close()

    return [{"id": r[0], "titulo": r[1], "summary": r[2], "score": float(r[3])} for r in rows]
```

### 2. Mem0 + Kuzu — grafo relacional

```python
import os
from intelligence.memory.mem0_graph_config import get_mem0_instance

def buscar_mem0(query: str, category: str = "decisions") -> list:
    # Mem0 container: publisher-os-publisher-core-1
    # Qdrant: localhost:6333, coleção jarvis_memory_v2
    try:
        mem = get_mem0_instance(with_graph=True)
        results = mem.search(query=query, user_id=f"jarvis_{category}", limit=5)
        return results.get("results", results) if isinstance(results, dict) else results
    except Exception as e:
        return [{"erro": f"Mem0 indisponível: {e}"}]
```

Categorias disponíveis: `hooks`, `golden_hours`, `sdr_results`, `viral_patterns`, `decisions`

### 3. Obsidian — grep declarativo

```bash
QUERY="[QUERY]"
BASE=~/Desktop/OBSIDIAN/ComandoCentral

# Busca em 00_Contexto (estratégia e decisões)
grep -ri "$QUERY" "$BASE/00_Contexto/" --include="*.md" -l 2>/dev/null | head -5

# Trechos relevantes (máx 3 por arquivo)
grep -ri "$QUERY" "$BASE/00_Contexto/" --include="*.md" -m 3 2>/dev/null | head -10

# biblioteca_sabedoria SQL
docker exec akasha-postgres psql -U akasha -d biblioteca_sabedoria -c \
  "SELECT l.titulo, i.insight FROM insights i JOIN livros l ON i.livro_id=l.id WHERE i.insight ILIKE '%$QUERY%' LIMIT 3;" 2>/dev/null
```

### 4. Docker state (se query é sobre projeto/sistema)

```bash
# Só executa se query menciona projeto técnico
docker ps --format "{{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | grep -iE "(publisher|akasha|qdrant|litellm|ollama)"

# Último commit dos projetos relevantes
PROJECT=$(echo "[QUERY]" | grep -oE "publisher-os|daily-prophet|instagram-publisher" | head -1)
[ -n "$PROJECT" ] && git -C ~/$PROJECT log --oneline -3 2>/dev/null
git -C ~/$PROJECT status --short 2>/dev/null | head -5
```

### 5. Arquivos de estado do projeto (se restaurando contexto)

```bash
for f in TODO.md CONTINUE.md STATUS.md .planning/state.md NEXT_STEPS.md; do
  [ -f ~/$PROJECT/$f ] && echo "=== $f ===" && head -15 ~/$PROJECT/$f
done
grep -ri "$PROJECT" ~/.claude/projects/*/memory/ --include="*.md" 2>/dev/null | head -8
```

## Output format

```
## Contexto: [QUERY]

**Akasha** (conversas e projetos):
- [score: 0.XX] [título] — [summary em 1 linha]

**Mem0/Kuzu** (grafo relacional — decisões/SDR/hooks):
- [categoria] [conteúdo em 1 linha]

**Obsidian** (estratégia declarativa):
- [arquivo]: [trecho em 1-2 linhas]

**Docker** (estado operacional):
- [container]: [status]
- Último commit: [hash] [mensagem]

**Síntese:** [1-2 frases com o mais relevante para a ação]
```

## Regras

- Máximo 250 palavras no output
- Score < 0.50: não exibir
- Se nada encontrado em fonte: omitir bloco da fonte (não mostrar "vazio")
- Se Ollama offline: continuar com Obsidian + Docker (degradação graciosa)
- Síntese final é obrigatória — sempre termina o output
- Se contexto é de projeto: incluir bloco Docker com último commit e arquivos pendentes

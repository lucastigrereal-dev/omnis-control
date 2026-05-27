# HANDOFF W17 — Obsidian Indexer + Search

**Branch:** feature/omnis-w11-w20
**Commit:** feat(W17): obsidian indexer script + search integration
**Status:** COMPLETO — 25/25 testes verdes

---

## Arquivos criados

| Arquivo | Função |
|---|---|
| `scripts/index_obsidian.py` | Script de indexação overnight |
| `scripts/__init__.py` | Package init |
| `src/memory/obsidian_search.py` | Busca semântica nas notas indexadas |
| `tests/scripts/test_index_obsidian.py` | 15 testes do indexer |
| `tests/memory/test_obsidian_search.py` | 10 testes do search |

---

## Como rodar overnight (quando Qdrant estiver up)

```sh
# Opção 1: vault padrão (C:/Users/lucas/Obsidian)
python scripts/index_obsidian.py

# Opção 2: vault customizado via env var
set OBSIDIAN_VAULT_PATH=D:/MeuVault
python scripts/index_obsidian.py

# Opção 3: dry-run (conta notas sem indexar)
python -c "
from pathlib import Path
from scripts.index_obsidian import index_vault
print(index_vault(dry_run=True))
"
```

## Como usar o search

```python
from src.memory.obsidian_search import search_obsidian

results = search_obsidian("viagem natal praia", top_k=5)
for r in results:
    print(r["path"], r["score"])
    print(r["excerpt"])
```

---

## Comportamento com Qdrant off

- `index_vault()` → `indexed=0, errors=0` (graceful, não levanta exceção)
- `search_obsidian()` → `[]` (lista vazia)

---

## Variáveis de ambiente

| Variável | Default | Uso |
|---|---|---|
| `OBSIDIAN_VAULT_PATH` | `C:/Users/lucas/Obsidian` | Caminho do vault |

---

## Próximo passo

Quando Qdrant estiver up:
1. `python scripts/index_obsidian.py` (deixar rodar overnight)
2. Verificar: `python -c "from src.memory.obsidian_search import search_obsidian; print(search_obsidian('viagem'))"`

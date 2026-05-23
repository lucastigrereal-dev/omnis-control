# D4 — Correções: src/providers/ → realidade do disco
**Wave A | 2026-05-22 | READ-ONLY sobre Downloads — correções anotadas aqui**

## Decisão Arquitetural (Lucas, 2026-05-22)
`src/providers/` **NÃO deve ser criado**.  
A funcionalidade real de roteamento de modelos existe em `src/multi_model_orchestration/router.py`.

---

## Referências a Corrigir nos Documentos Externos

Os arquivos em `C:\Users\lucas\Downloads\` são read-only (referências externas).  
Quando forem atualizados, aplicar as correções abaixo:

### `OMNIS_BLUEPRINT_CANONICO.md` (6 ocorrências)

| O que está escrito | Correção |
|---|---|
| `src/providers/model_router.py` | → `src/multi_model_orchestration/router.py` |
| `src/providers/akasha.py` | → `src/akasha_runtime/` (módulo existente) |
| `src/providers/mem0_provider.py` | → `src/memory_intel/` ou decidir com Lucas |
| `src/providers/semantic_memory.py` | → `src/memory/` (a criar — T-204 pendente) |
| `src/providers/embedding.py` | → `src/akasha_runtime/` ou `src/memory/` |
| `├── src/providers/` (diagrama) | → remover linha ou substituir por `├── src/multi_model_orchestration/` |

### `OMNIS_REFINAMENTO_50.md` (1 ocorrência, provável)
- Mesma correção: `src/providers/model_router.py` → `src/multi_model_orchestration/router.py`

---

## Correções já aplicadas no repo

| Arquivo no repo | Linha | Antes | Depois |
|---|---|---|---|
| `docs/project-os/OMNIS_REFINAMENTO_50_DECISOES.md` | 161 | `src/providers/semantic_memory.py` | Anotado com aviso Wave A — módulo canônico será em `src/memory/` |

---

## Total de referências encontradas e tratadas

| Arquivo | Ocorrências | Ação |
|---|---|---|
| `Downloads/OMNIS_BLUEPRINT_CANONICO.md` | 6 | Anotadas acima (arquivo externo, não editado) |
| `Downloads/OMNIS_REFINAMENTO_50.md` | 1 | Anotada acima (arquivo externo, não editado) |
| `docs/project-os/OMNIS_REFINAMENTO_50_DECISOES.md` | 1 | **CORRIGIDA** — aviso inline adicionado |
| `docs/project-os/MODULES_CLASSIFICATION_PROPOSAL.md` | múltiplas | Análise de conflito (correto — não alterar) |
| `docs/project-os/VERDADE_DISCO.md` | múltiplas | Documentação do conflito (correto — não alterar) |

**Total editado no repo:** 1 referência corrigida com anotação.  
**Total a corrigir em Downloads quando forem revisados:** 7 referências.

---

## Módulo real de roteamento (confirmado no disco)

```
src/multi_model_orchestration/
├── router.py        ← ModelRouter (roteamento de LLM)
├── cost_tracker.py  ← CostTracker (rastreamento de custo)
├── classifier.py    ← classificação de tarefas
├── fallback.py      ← FallbackChain
├── models.py        ← modelos de dados
├── registry.py      ← registro de modelos
├── cli.py           ← interface CLI
├── errors.py        ← erros tipados
└── adapters/
    ├── anthropic_adapter.py
    ├── openai_adapter.py
    ├── ollama_adapter.py
    └── mock_adapter.py
```

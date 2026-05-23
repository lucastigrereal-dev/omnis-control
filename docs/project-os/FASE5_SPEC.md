# Fase 5 — LLM real no CaptionDraftAgent

**Status:** PLANEJADA — aguardando Codex entregar auditoria de src/agentic/ e src/memory/
**Pré-requisito:** CODEX_SRC_CONSOLIDATION_PROPOSAL.md revisado e aprovado

---

## Objetivo

Substituir a geração de texto baseada em template (`_build_caption`) por uma chamada LLM real,
mantendo `dry_run=True` como default seguro e sem quebrar nenhum teste existente.

---

## Contrato da chamada LLM

### Input (o que o agente monta antes de chamar)

```python
@dataclass
class CaptionPromptInput:
    account_handle: str       # "@oinatalrn"
    objective: str            # "alcance" | "conversao" | "autoridade" | "relacionamento"
    format: str               # "feed" | "reels" | "stories" | "carousel"
    context_md: str           # MemoryContext.context_markdown
    similar_captions: list[str]  # até 3 exemplos da memória
    max_chars: int = 2200
```

### Output esperado do LLM

```python
@dataclass
class CaptionLLMOutput:
    hook: str          # primeira linha — gancho
    body: str          # corpo com bullets ou narrativa
    cta: str           # call-to-action final
    hashtags: list[str]  # 5-10 hashtags
    raw: str           # texto completo gerado
    model_used: str    # ex: "gemini/gemini-2.5-flash"
    tokens_used: int
```

---

## Adapter pattern — sem acoplar ao LLM

O agente não chama LLM diretamente. Usa um adapter:

```python
class LLMAdapter(Protocol):
    def generate_caption(self, prompt: CaptionPromptInput) -> CaptionLLMOutput: ...

class MockLLMAdapter:          # usado em testes e dry_run
    def generate_caption(self, prompt) -> CaptionLLMOutput: ...

class LiteLLMAdapter:          # produção — via LiteLLM gateway :4002
    model: str = "gemini/gemini-2.5-flash"
    def generate_caption(self, prompt) -> CaptionLLMOutput: ...
```

`CaptionDraftAgent.__init__` recebe `llm: LLMAdapter | None = None`.
Se `None` e `dry_run=True`: usa `MockLLMAdapter`.
Se `None` e `dry_run=False`: usa `LiteLLMAdapter` com model do env var `OMNIS_LLM_MODEL`.

---

## Mudanças em arquivos existentes

| Arquivo | O que muda |
|---|---|
| `src/agentic/caption_draft_agent.py` | Step 3 chama `llm.generate_caption()` em vez de `_build_caption()` |
| `src/agentic/agent_models.py` | Nenhuma mudança |
| `src/memory/interface.py` | Nenhuma mudança |

### Novos arquivos

| Arquivo | Conteúdo |
|---|---|
| `src/agentic/llm_adapter.py` | Protocol + MockLLMAdapter + LiteLLMAdapter |
| `tests/agentic/test_llm_adapter.py` | Testes do Mock e contrato do Protocol |

---

## Testes

Todos os 14 testes existentes em `test_caption_draft_agent.py` continuam passando sem mudança —
porque `dry_run=True` usa `MockLLMAdapter` por default.

Novos testes:
- `test_llm_adapter.py` — MockLLMAdapter retorna output válido
- `test_caption_draft_agent.py::test_agent_real_uses_llm` — dry_run=False com MockLLMAdapter injetado

---

## Gate de saída

```sh
python -m pytest tests/agentic/ --import-mode=importlib -p no:warnings -q
# >= 30 passed, 0 failed

python -m pytest tests/ --import-mode=importlib -p no:warnings -q
# >= baseline, 0 failed
```

---

## Fora do escopo desta fase

- Integração com Akasha real (já existe via MemoryInterface._real_query)
- Aprovação automática de drafts
- Publicação via Publisher OS
- Multi-turn conversation / agente reflexivo

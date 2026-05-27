# HANDOFF W12 — LiteLLM Gateway

**Branch:** feature/omnis-w11-w20
**Data:** 2026-05-27
**Status:** COMPLETO ✅

## O que foi feito

### B1 — pyproject.toml atualizado
- Adicionadas dependências core: `fastapi>=0.115,<1.0`, `uvicorn>=0.30,<1.0`, `anthropic>=0.40,<1.0`
- Adicionada seção `[project.optional-dependencies]` → `llm-gateway = ["litellm>=1.0,<2.0"]`
- `litellm` declarado como opcional (NÃO instalado ainda — aguarda GO do Lucas)

### B2 — infra/litellm/litellm_config.yaml
- Modelos configurados: `haiku` (claude-haiku-4-5), `sonnet` (claude-sonnet-4-6), `local-fast` (ollama/llama3.2)
- Estratégia: `cost-based-routing` com fallback haiku → local-fast
- Budget: $50/mês

### B3 — infra/litellm/docker-compose.yml
- Container `ghcr.io/berriai/litellm:main` na porta 4000
- Healthcheck configurado
- **NÃO subir sem GO explícito do Lucas**

### B4 — src/agentic/model_validator.py
- `ALLOWED_MODELS = {"haiku", "sonnet", "local-fast", "local-code"}`
- `BLOCKED_MODELS = {"opus", "claude-opus", "claude-opus-4-5", "claude-opus-4-6"}`
- `validate_model(model)` — levanta ValueError para qualquer variante opus
- `is_allowed(model)` — retorna bool

### B5 — tests/test_litellm_config.py
- 14 testes, todos PASSING ✅
- Cobre: deps no pyproject.toml, existência dos arquivos de config, model_validator

## Arquivos criados/modificados
- `pyproject.toml` — M
- `infra/litellm/litellm_config.yaml` — novo
- `infra/litellm/docker-compose.yml` — novo
- `src/agentic/model_validator.py` — novo
- `tests/test_litellm_config.py` — novo

## Nota sobre llm_adapter.py
O `LiteLLMAdapter` existente aponta para `:4002`. O `docker-compose.yml` desta wave expõe a porta `4000`.
Para alinhar, o operador deve definir `LITELLM_BASE_URL=http://localhost:4000` no ambiente ou ajustar conforme a porta real do gateway em produção.

## Próximo passo
- GO do Lucas para subir o container: `cd infra/litellm && docker compose up -d`
- Instalar litellm: `pip install "omnis-control[llm-gateway]"`
- Apontar `LITELLM_BASE_URL` conforme porta escolhida

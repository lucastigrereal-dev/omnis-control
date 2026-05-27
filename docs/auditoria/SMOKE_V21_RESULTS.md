# Smoke v2.1 Results — Quality-First
**Data:** 2026-05-27 19:58 BRT | **Branch:** `feature/omnis-w11-w20`

---

## ✅ Infraestrutura

| Serviço | Status |
|---------|--------|
| Docker Desktop | ✅ UP |
| LiteLLM container `:4001` | ✅ UP (health: starting → running) |
| LiteLLM config carregado | ✅ 6 modelos no model_list |

---

## ❌ T1-T6 — Modelos Premium (BLOQUEADO: auth)

**Erro uniforme:** `401 Unauthorized` → `https://ollama.com/api/generate`

| Modelo | Resultado | Causa |
|--------|-----------|-------|
| ollama-fast (glm-5.1:cloud) | ❌ 401 | OLLAMA_API_KEY ausente |
| ollama-code (kimi-k2.6:cloud) | ❌ 401 | OLLAMA_API_KEY ausente |
| ollama-build (minimax-m2.7:cloud) | ❌ 401 | OLLAMA_API_KEY ausente |
| ollama-smart (deepseek-v4-pro:cloud) | ❌ 401 | OLLAMA_API_KEY ausente |
| ollama-longctx (minimax-m2.7:cloud) | ❌ 401 | OLLAMA_API_KEY ausente |
| ollama-backup (qwen3.5:397b:cloud) | ❌ 401 | OLLAMA_API_KEY ausente |

**Root cause:** `api_base: https://ollama.com` é a API web Ollama Pro Cloud.
Diferente da v2.0 (`host.docker.internal:11434` = Ollama local, sem auth),
a v2.1 cloud exige Bearer token da conta Ollama Pro.

**Fix necessário:** Adicionar ao `.env`:
```
OLLAMA_API_KEY=<token da conta ollama.com>
```
E ao `litellm_config.yaml`, em cada model:
```yaml
api_key: os.environ/OLLAMA_API_KEY
```

---

## ✅ T7-T9 — Bloqueios (PASS)

| Modelo proibido | HTTP | Esperado |
|----------------|------|----------|
| claude-opus-4-6 | 400 | 4xx ✅ |
| gpt-5 | 400 | 4xx ✅ |
| fallback-cheap (comentado) | 400 | 4xx ✅ |

**3/3 bloqueios funcionando corretamente.**

---

## Próximos Passos

1. Lucas obtém `OLLAMA_API_KEY` em https://ollama.com/settings (seção API Keys)
2. Adiciona ao `.env`: `OLLAMA_API_KEY=<token>`
3. Atualizar `litellm_config.yaml` com `api_key: os.environ/OLLAMA_API_KEY` em cada modelo
4. `docker compose -f infra/litellm/docker-compose.yml --env-file .env up -d`
5. Re-rodar T1-T6 → esperado: 6/6 OK

*Gerado por OMNIS Control — Smoke v2.1 · 2026-05-27*

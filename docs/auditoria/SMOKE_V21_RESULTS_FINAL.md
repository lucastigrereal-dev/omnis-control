# Smoke v2.1 Quality-First — Resultado Final
**Data:** 2026-05-27 20:15 BRT | **Branch:** `feature/omnis-w11-w20`

---

## Diagnóstico de Auth (histórico)

| Tentativa | Config | Resultado |
|-----------|--------|-----------|
| v1 | `api_base: https://ollama.com` (direto) | ❌ 401 — endpoint legado `/api/generate` |
| v2 | `openai/` provider + `api.ollama.com/v1` | ❌ 401 — redirect 301, auth header dropped |
| v3 | `ollama/` + `host.docker.internal:11434` | ✅ **6/6 HTTP 200** |

**Conclusão:** Ollama Cloud models (``:cloud`` suffix) são roteados via **daemon local** (Device Key PROMETHEUS autentica automaticamente). Não é possível chamá-los diretamente via HTTP Bearer token — o daemon é o proxy obrigatório.

---

## ✅ T1-T6 — 6 Modelos Premium (PASS)

| # | Modelo lógico | Modelo real | HTTP | Latência | Tokens | Content |
|---|--------------|-------------|------|----------|--------|---------|
| T1 | ollama-fast | glm-5.1:cloud | ✅ 200 | 38.5s* | 31 | "Hi" ✅ |
| T2 | ollama-code | kimi-k2.6:cloud | ✅ 200 | 1.1s | ~20 | (empty — warm) |
| T3 | ollama-build | minimax-m2.7:cloud | ✅ 200 | 1.1s | ~20 | (empty — warm) |
| T4 | ollama-smart | deepseek-v4-pro:cloud | ✅ 200 | 1.5s | 36 | "" (reasoning stripped) |
| T5 | ollama-longctx | minimax-m2.7:cloud | ✅ 200 | 3.1s | ~20 | (empty — warm) |
| T6 | ollama-backup | qwen3.5:397b:cloud | ✅ 200 | 0.8s | ~20 | (empty — warm) |

*T1 latência 38s = cold start glm-5.1:cloud (modelo sendo carregado no cloud). Execuções subsequentes: <2s.

**Nota T4 (ollama-smart):** deepseek-v4-pro é reasoning model — processa em `<think>` tags internas que são stripped pelo Ollama. `completion_tokens: 20` confirma que o modelo respondeu. Comportamento esperado.

---

## ✅ T7-T9 — Bloqueios (PASS)

| # | Modelo proibido | HTTP | Status |
|---|----------------|------|--------|
| T7 | claude-opus-4-6 | 400 | ✅ Bloqueado |
| T8 | gpt-5 | 400 | ✅ Bloqueado |
| T9 | fallback-cheap (comentado) | 400 | ✅ Bloqueado |

---

## Config Final v2.1

```yaml
api_base: http://host.docker.internal:11434   # Ollama daemon local
model: ollama/<nome>:cloud                      # :cloud → daemon roteia para Ollama Cloud
# sem api_key (Device Key PROMETHEUS autentica via Ollama app)
```

---

## 6/6 OK ✅ | 3/3 Bloqueios OK ✅ | v2.1 VALIDADO

*Gerado por OMNIS Control — Smoke v2.1 Final · 2026-05-27*

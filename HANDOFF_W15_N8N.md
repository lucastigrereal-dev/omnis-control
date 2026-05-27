# HANDOFF W15 — n8n Integration Bridge

**Branch:** feature/omnis-w11-w20
**Commit:** feat(W15): n8n bridge — docker config + webhook receiver + trigger client
**Status:** GREEN — 13/13 tests passing

---

## O que foi feito

### Arquivos criados/modificados

| Arquivo | Ação | Descrição |
|---|---|---|
| `infra/n8n/docker-compose.yml` | CRIADO | Config Docker para n8n (porta 5678, healthcheck) |
| `src/integrations/n8n_client.py` | MODIFICADO | Adicionados métodos webhook com graceful degradation |
| `src/api/routers/webhooks.py` | CRIADO | Receptor de eventos n8n → OMNIS |
| `src/api/main.py` | MODIFICADO | Incluído webhooks_router em /webhooks |
| `tests/integrations/test_n8n.py` | CRIADO | 9 testes (graceful + webhook routes) |

---

## N8NClient — novas capacidades

```python
client = N8NClient()  # usa N8N_BASE_URL ou N8N_URL env var

# Graceful degradation (retorna {"status": "unavailable"} se n8n off)
client.trigger_workflow("meu-webhook", {"dado": "valor"})

# Domain-level triggers
client.trigger_content_production("viagem para Natal", "@oinatalrn")
client.trigger_lead_processing("Quero collab!", "instagram")
client.trigger_sprint_creation([{"titulo": "Ideia 1"}, {"titulo": "Ideia 2"}])

# Health
client.health_check()  # True/False
```

---

## Webhook endpoints disponíveis

| Endpoint | Método | Descrição |
|---|---|---|
| `/webhooks/n8n/nova-ideia` | POST | n8n envia nova ideia de conteúdo |
| `/webhooks/n8n/novo-lead` | POST | n8n envia novo lead para qualificação |
| `/webhooks/n8n/publicacao-ok` | POST | n8n confirma publicação realizada |
| `/webhooks/n8n/metricas` | POST | n8n envia métricas semanais |

---

## Resultados dos testes

```
tests/integrations/test_n8n.py::test_n8n_client_graceful         PASSED
tests/integrations/test_n8n.py::test_health_check_false           PASSED
tests/integrations/test_n8n.py::test_trigger_lead                 PASSED
tests/integrations/test_n8n.py::test_trigger_content              PASSED
tests/integrations/test_n8n.py::test_trigger_sprint               PASSED
tests/integrations/test_n8n.py::test_webhook_nova_ideia           PASSED
tests/integrations/test_n8n.py::test_webhook_novo_lead            PASSED
tests/integrations/test_n8n.py::test_webhook_publicacao_ok        PASSED
tests/integrations/test_n8n.py::test_webhook_metricas             PASSED
tests/integrations/test_n8n_client.py (4 existing tests)          PASSED
13 passed in 0.44s
```

---

## Notas para W16+

- `docker-compose.yml` criado mas NÃO subir container sem GO explícito
- Webhook `/n8n/nova-ideia` está pronto para integração com Marketing Sector (W16)
- `N8N_BASE_URL` env var tem prioridade sobre `N8N_URL` para backward compat
- CORS atualizado para aceitar POST (necessário para webhooks)

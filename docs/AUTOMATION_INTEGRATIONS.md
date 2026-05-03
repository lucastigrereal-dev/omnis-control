# Automation & Integration Registry — OMNIS Fase 3A

## Proposta

Camada de conectores entre OMNIS e sistemas externos. Cada conector tem:
status (available/unavailable/pending/planned), tipo (http/postgres/redis/oauth2/mcp/bot),
e um `next_step` claro para ativação.

## Visão Geral

```
OMNIS CLI ←→ Connector Layer ←→ Sistemas Externos
                      │
           ┌──────────┼──────────┐
           ▼          ▼          ▼
     Publisher OS   Akasha    Instagram
     (MCP/HTTP)   (pgvector)  (Graph API)
           │          │          │
           ▼          ▼          ▼
        Ollama     Qdrant    Meta OAuth
       LiteLLM     Obsidian   (pending)
        n8n
```

## Conectores P0 (prioridade máxima)

| Conector | Tipo | Status | Próximo Passo |
|----------|------|--------|---------------|
| Publisher OS MCP | mcp | ✅ available | Conectar via MCP config |
| Publisher OS API | http | ✅ available | — |
| Akasha PostgreSQL | postgres | ✅ available | Criar user read-only |
| Instagram Graph API | oauth2 | ⏳ pending | Configurar META_APP_SECRET |

## Conectores P1 (suporte operacional)

| Conector | Tipo | Status | Próximo Passo |
|----------|------|--------|---------------|
| Qdrant | http | ❌ unavailable | Restartar container |
| Ollama | http | ✅ available | — |
| LiteLLM | http | ✅ available | Criar key dedicada OMNIS |
| Supabase DB | postgres | ✅ available | — |
| Redis | redis | ✅ available | — |
| n8n | http | ❓ unknown | Verificar container |

## Conectores P2 (futuros)

| Conector | Tipo | Status | Próximo Passo |
|----------|------|--------|---------------|
| WhatsApp Bridge | api | 📋 planned | Definir provider |
| Telegram Bot | bot | 📋 planned | Reativar tg-approve |
| Mercado Pago/Stripe | api | 📋 planned | Definir provider |
| Supabase Hotels | postgres | ✅ available | Criar access layer |
| GitHub API | api | ✅ available | Criar token dedicado |

## Setores vs Conectores

Cada setor OMNIS usa um subconjunto dos conectores:

- **marketing_enterprise:** Publisher OS MCP + API + Instagram Graph API
- **sales_revenue:** WhatsApp Bridge + GitHub + Supabase Hotels
- **memory_knowledge:** Akasha PostgreSQL + Qdrant + Ollama
- **automation_integrations:** n8n + LiteLLM + Redis
- **finance_capital:** Mercado Pago + Supabase Hotels
- **mission_control:** Telegram Bot + GitHub
- **runtime_agentic:** Ollama + LiteLLM + Publisher OS MCP

## Fonte da Verdade

**`config/connectors.yaml`** é a fonte da verdade. Este documento é resumo legível.

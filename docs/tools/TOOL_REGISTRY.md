# TOOL REGISTRY — P0.8

**Data:** 2026-05-07
**Objetivo:** Saber quais ferramentas existem, status real, sem mentir.

## Por que depois de Mission Runtime?

P0.5 criou o MissionContract. P0.6 conectou ao pipeline local. P0.7 deu durabilidade (checkpoint/pause/resume/retry).

Mas toda missão precisa de ferramentas para executar. Antes de uma missão tentar publicar, precisa saber: o Instagram está disponível? É dry-run ou real? Está bloqueado por credencial?

O Tool Registry responde essas perguntas antes que o OMNIS tente agir no escuro.

## Status de ferramenta

| Status | Significado | Exemplo |
|---|---|---|
| `not_configured` | Ferramenta conhecida mas sem config | Publer, Metricool |
| `manual` | Operação manual (humano no loop) | Canva, Perplexity |
| `read_only` | Só leitura, nunca altera | Obsidian, Akasha |
| `dry_run` | Executa mas não publica de verdade | publisher_local_dry_run |
| `semi_automatic` | Automático com confirmação humana | — (futuro) |
| `automatic` | 100% automático, sem intervenção | — (nada ainda) |
| `blocked` | Existe mas não pode ser usada | Instagram Graph API |
| `deprecated` | Substituída/abandonada | — |

## Categorias

14 categorias: publishing, memory, automation, design, crm, finance, development, research, storage, communication, infrastructure, llm, browser, security.

## Ferramentas iniciais (19)

| Tool ID | Categoria | Status |
|---|---|---|
| instagram_graph_api | publishing | blocked |
| publisher_local_dry_run | publishing | dry_run |
| publisher_os_argos | publishing | dry_run |
| publer | publishing | not_configured |
| metricool | publishing | not_configured |
| n8n | automation | manual |
| akasha_postgres | memory | read_only |
| qdrant | memory | read_only |
| obsidian_vault | research | read_only |
| github | development | manual |
| canva | design | manual |
| gmail | communication | not_configured |
| google_drive | storage | not_configured |
| claude_code | llm | manual |
| openai_api | llm | not_configured |
| gemini_api | llm | not_configured |
| perplexity | research | manual |
| docker | infrastructure | read_only |
| local_filesystem | storage | read_only |

## Comandos CLI

```bash
python jarvis.py tools discover             # descobre e popula registry (read-only)
python jarvis.py tools list                  # lista todas
python jarvis.py tools list --status blocked # filtra por status
python jarvis.py tools list --category llm   # filtra por categoria
python jarvis.py tools show instagram_graph_api  # detalhes
python jarvis.py tools status                # resumo (por status + categoria)
python jarvis.py tools update-status docker manual  # altera status + log
```

Todos aceitam `--json` para output estruturado.

## Segurança

- **NUNCA armazena valor de secret** — `required_credentials` guarda nomes (ex: `META_APP_SECRET`), nunca tokens
- **Blocklist ativa**: strings que parecem tokens (EA*, sk-*, ghp_*, etc.) são rejeitadas na validação
- **Discovery read-only**: usa checkers existentes, não lê `.env`, não chama API externa

## Limitações

- Registry local (JSONL) — sem banco, sem API
- Discovery manual (não contínuo) — precisa rodar `tools discover` explicitamente
- Healthcheck é sugestão de comando, não é executado automaticamente
- Sem auto-remediation — não tenta consertar ferramenta quebrada

## Próximos passos

1. **Metrics Spine** — medir uso real de ferramentas
2. **OAuth Meta** — destravar Instagram
3. **DISK-1** — 1 post real controlado
4. **Auto-discovery** — healthcheck periódico

# P0.8 — TOOL REGISTRY AUDIT

**Data:** 2026-05-07
**Base:** cbffe14 (P0.7)

## 1. Ferramentas detectadas pelo sistema

| Ferramenta | Checker | Status detectado |
|---|---|---|
| Docker (18 containers) | `docker_check.py` | 18 running, 2 unhealthy |
| Publisher OS (:8000) | `publisher_check.py` | port_open_no_response (nem sempre responde) |
| Akasha (PostgreSQL) | `memory_check.py` | container_found |
| Qdrant (:6333) | `memory_check.py` | accessible, collections |
| Obsidian vault | `obsidian_check.py` | vault_found, ~7.792 .md |
| Skills (~/.claude/skills) | `skills_check.py` | 17 skills, executaveis + docs |
| Disco | `disk_check.py` | severidade ok/warning/critical |
| Video pipeline | `video_pipeline_check.py` | classificacao operational/partial |
| Sectors | `sectors_check.py` | 11 setores mapeados |
| Daily Prophet | `daily_prophet_check.py` | missing_env/not_found |
| Content Queue | `doctor` inline | accounts + queue stats |
| Caption Approval | `doctor` inline | drafts by status |

## 2. Checkers reutilizaveis

- `docker_check.py` → pode confirmar se akasha/qdrant/n8n containers estao rodando
- `publisher_check.py` → health do Publisher OS
- `memory_check.py` → Qdrant collections + Akasha status
- `obsidian_check.py` → vault path + .md count
- `disk_check.py` → espaco livre

Todos sao read-only e seguros para discovery.

## 3. Fontes seguras read-only

- `paths.yaml` → paths e URLs de servicos locais
- Checkers existentes (todos read-only)
- `akasha_reader.py` → leitura do PostgreSQL
- `metaapi_dryrun.py` → mock da Meta API (nunca chama API real)
- Output de `docker ps` (subprocess, nao altera nada)

## 4. Ferramentas que existem mas nao estao conectadas

- **Instagram Graph API**: sem OAuth/token → `blocked`
- **Publer**: mencionado em docs, sem integracao → `not_configured`
- **Metricool**: mencionado em docs, sem integracao → `not_configured`
- **n8n**: URL configurada (:5678), mas sem workflows validados → `manual`
- **Google Drive**: scanner de video cita "drive", sem token → `not_configured`
- **Gmail**: nao implementado → `not_configured`
- **Canva**: manual (exporta, nao conecta API) → `manual`
- **OpenAI API**: via LiteLLM, sem key direta → `not_configured`
- **Gemini API**: via LiteLLM/OpenRouter → `not_configured`
- **Perplexity**: manual (copia/cola) → `manual`

## 5. Ferramentas bloqueadas por credencial

| Ferramenta | Credencial faltante |
|---|---|
| Instagram Graph API | META_APP_SECRET, INSTAGRAM_ACCESS_TOKEN |
| Publer | PUBLER_API_KEY |
| Metricool | METRICOOL_TOKEN |
| Google Drive | GOOGLE_DRIVE_CREDENTIALS |
| Gmail | GMAIL_OAUTH |

## 6. Ferramentas dry-run

- `publisher_local_dry_run` → `metaapi_dryrun.py`
- `publisher_os_argos` → cria drafts locais, nao publica

## 7. Riscos de seguranca

- **NUNCA ler .env** — discovery nao pode acessar credenciais
- **NUNCA chamar API externa** — Instagram/Meta bloqueados
- **NUNCA executar Docker destrutivo** — `docker ps` read-only
- `required_credentials` guarda nomes, nunca valores
- Blocklist para secrets no CLI input

## 8. Plano de implementacao minimo

1. `src/tool_registry/models.py` — enums + ToolRecord (Pydantic v2)
2. `src/tool_registry/errors.py` — excecoes customizadas
3. `src/tool_registry/registry.py` — ToolRegistry com storage JSONL
4. `src/tool_registry/discovery.py` — discover_known_tools() read-only
5. `src/cli_commands/tools_cmd.py` — 6 comandos CLI
6. Registrar em `src/cli.py` (1 linha)
7. `tests/tool_registry/` — 20 testes
8. `docs/tools/` — documentacao

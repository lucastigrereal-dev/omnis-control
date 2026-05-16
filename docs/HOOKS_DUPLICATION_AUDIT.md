# HOOKS DUPLICATION AUDIT

**Date:** 2026-05-16
**Auditor:** agent-qa + docs-release (OMNIS CCOS)
**Status:** AUDITADO — nenhuma exclusao ou renomeacao executada

---

## Hooks no repositorio

### Grupo A — Rastreados no HEAD (snake_case, antigos)

| Hook | Path | Funcao | Referenciado em settings.json? |
|---|---|---|---|
| `import_guard.ps1` | `.claude/hooks/import_guard.ps1` | Scan de padroes proibidos em arquivos fonte | NAO |
| `pre_tool_use_guard.ps1` | `.claude/hooks/pre_tool_use_guard.ps1` | Bloqueia comandos perigosos e paths proibidos | NAO |
| `session_logger.ps1` | `.claude/hooks/session_logger.ps1` | Loga eventos de sessao (start/stop) | NAO |

### Grupo B — Novos (kebab-case, bootstrap CCOS)

| Hook | Path | Funcao | Referenciado em settings.json? |
|---|---|---|---|
| `pre-tool-guard.ps1` | `.claude/hooks/pre-tool-guard.ps1` | Bloqueia padroes perigosos pre-execucao | SIM — PreToolUse |
| `post-tool-log.ps1` | `.claude/hooks/post-tool-log.ps1` | Loga eventos pos-execucao | SIM — PostToolUse |
| `session-stop-report.ps1` | `.claude/hooks/session-stop-report.ps1` | Gera report ao final da sessao | SIM — Stop |
| `subagent-stop-report.ps1` | `.claude/hooks/subagent-stop-report.ps1` | Loga eventos de subagentes | SIM — SubagentStop |

---

## Matriz de sobreposicao

| Funcao | Hook antigo | Hook novo | Sobrepoe? |
|---|---|---|---|
| Bloqueio de comandos perigosos | `pre_tool_use_guard.ps1` | `pre-tool-guard.ps1` | SIM — mesma funcao |
| Bloqueio de paths proibidos | `pre_tool_use_guard.ps1` | `pre-tool-guard.ps1` | SIM — mesma funcao |
| Log de eventos de sessao | `session_logger.ps1` | `session-stop-report.ps1` | PARCIAL — antigo loga start/stop, novo so stop |
| Log de eventos de ferramenta | — | `post-tool-log.ps1` | NOVO — nao existia antes |
| Log de eventos de subagente | — | `subagent-stop-report.ps1` | NOVO — nao existia antes |
| Scan de secrets em arquivos | `import_guard.ps1` | `omnis-secret-scan.ps1` (script) | PARCIAL — antigo e hook, novo e script |

---

## Comparacao detalhada

### pre_tool_use_guard.ps1 vs pre-tool-guard.ps1

| Aspecto | Antigo (snake_case) | Novo (kebab-case) |
|---|---|---|
| Interface | Parametros nomeados `$tool_name, $tool_input` | Le STDIN `[Console]::In.ReadToEnd()` |
| Padroes bloqueados | 7 comandos + 7 paths | 6 comandos + 6 paths |
| docker rm/rri | Sim | Nao |
| .env (como substring) | Regex: `\.env` | Literal: `.env` |
| Logging | Nao | Sim — escreve em reports/ccos/ |
| Exit code bloqueio | 1 | 2 |

**Veredito:** O novo cobre a mesma funcao com interface diferente (STDIN vs parametros). O antigo tem patterns adicionais (`docker rm`, `docker rmi`, `credentials.json`, `data/.*\.jsonl`). O novo adiciona logging.

### session_logger.ps1 vs session-stop-report.ps1

| Aspecto | Antigo | Novo |
|---|---|---|
| Eventos | start e stop | so stop |
| Formato saida | Markdown append em arquivo diario | Markdown em arquivo timestamped |
| Diretorio saida | `docs/reports/sessions/` | `reports/ccos/` |
| Parametros | `$event_type, $session_id` | STDIN |
| Conteudo | Session, branch, commit | Branch, git status, reminders |

**Veredito:** O novo cobre parcialmente. Falta o log de start de sessao. Mas o escopo e diferente — o novo foca em report de estado final, nao em diario cronologico.

### import_guard.ps1

| Aspecto | Valor |
|---|---|
| Funcao | Scan de arquivos fonte por secrets/chamadas reais |
| Parametro | `$file_path` (opcional, default = todos src/**.py) |
| Padroes | 12 (secret, token, api_key, password, OAuthReal, publish_real, send_real, deploy_real, os.environ, openai, requests.post, requests.get) |
| Sobrepoe com novo? | NAO — nenhum hook novo faz scan de arquivos fonte |

**Veredito:** Funcao util que nao foi substituida. O script `omnis-secret-scan.ps1` cobre parcialmente com menos patterns. `import_guard.ps1` poderia ser convertido em hook ou script mantendo sua cobertura.

---

## Estado atual do settings.json

Apenas os hooks novos (Grupo B) estao configurados. Os hooks antigos (Grupo A) estao no disco mas NAO serao executados porque:

1. `settings.json` so referencia os paths do Grupo B
2. O mecanismo de hooks do Claude Code so executa hooks listados em `settings.json`

**Conclusao:** Os 3 hooks antigos sao codigo morto operacional — existem no disco, rastreados no git, mas nunca disparados.

---

## Recomendacao

| Acao | Prioridade |
|---|---|
| Consolidar `pre_tool_use_guard.ps1` + `pre-tool-guard.ps1` em um unico hook com o melhor dos dois | MEDIA |
| Adicionar patterns do antigo (`docker rm`, `docker rmi`, `credentials.json`) ao novo | ALTA |
| Decidir se `import_guard.ps1` vira hook ou permanece script | BAIXA |
| Remover hooks antigos apos confirmar que novos cobrem 100% | MEDIA |
| Manter `session_logger.ps1` se log de start for desejado | BAIXA |

**Nao deletar nem renomear nada ainda.** Aguardar aprovacao de Lucas.

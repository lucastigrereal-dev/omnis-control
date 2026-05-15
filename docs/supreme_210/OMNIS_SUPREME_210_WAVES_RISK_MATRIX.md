# OMNIS SUPREME 210 WAVES — Risk Matrix

**Date:** 2026-05-15

---

## Niveis de risco

| Nivel | Auto-Execute | Requer Token | Requer Human | Exemplo |
|---|---|---|---|---|
| LOW | Yes | No | No | Criar doc, modelo dataclass, teste |
| MEDIUM | Dry-run only | Optional | No | Criar CLI command, refactor interno |
| HIGH | No | Yes | Yes | Conectar banco real, MCP spawn |
| CRITICAL | Never | Yes | Yes | Deploy, publish, delete, push |

## Risco por grupo

| Grupo | Waves | Risco base | Maior risco individual |
|---|---|---|---|
| 01 — Foundation | W001-W010 | LOW | MEDIUM (merge plan) |
| 02 — Mission OS | W011-W020 | LOW | LOW |
| 03 — Memory/Akasha | W021-W030 | MEDIUM | HIGH (real DB connection) |
| 04 — Observability | W031-W040 | LOW | LOW |
| 05 — Skill Execution | W041-W050 | LOW | MEDIUM (permission gate) |
| 06 — Capability Forge | W051-W060 | LOW | MEDIUM (code generation) |
| 07 — Squad Composer | W061-W070 | LOW | LOW |
| 08 — Execution Graph | W071-W080 | LOW | MEDIUM (rollback logic) |
| 09 — Publisher/ARGOS | W081-W090 | MEDIUM | HIGH (publish path) |
| 10 — Content Factory | W091-W100 | LOW | MEDIUM (brand voice) |
| 11 — Video Studio | W101-W110 | LOW | MEDIUM (file processing) |
| 12 — Sales/CRM | W111-W120 | LOW | MEDIUM (lead data) |
| 13 — Commercial/SDR | W121-W130 | LOW | MEDIUM (outreach) |
| 14 — App Factory | W131-W140 | LOW | MEDIUM (code generation) |
| 15 — Automation/n8n | W141-W150 | MEDIUM | HIGH (webhook exposure) |
| 16 — MCP/Plugin | W151-W160 | MEDIUM | HIGH (process spawn) |
| 17 — Remote Control | W161-W170 | MEDIUM | HIGH (real Telegram) |
| 18 — KRATOS Bridge | W171-W180 | LOW | LOW |
| 19 — Production Hardening | W181-W190 | LOW | MEDIUM (resource limits) |
| 20 — First Real Missions | W191-W200 | HIGH | CRITICAL (real action) |
| 21 — Supreme RC | W201-W210 | MEDIUM | HIGH (final gate) |

## Matriz de acao permitida por risco

| Acao | LOW | MEDIUM | HIGH | CRITICAL |
|---|---|---|---|---|
| Ler arquivo | AUTO | AUTO | AUTO | AUTO |
| Criar arquivo | AUTO | AUTO | TOKEN | BLOCK |
| Editar arquivo | AUTO | AUTO | TOKEN | BLOCK |
| Rodar pytest | AUTO | AUTO | AUTO | AUTO |
| git add | AUTO | AUTO | TOKEN | BLOCK |
| git commit | AUTO | AUTO | TOKEN | BLOCK |
| git push | TOKEN | TOKEN | BLOCK | BLOCK |
| git merge | TOKEN | TOKEN | BLOCK | BLOCK |
| Conectar DB real | TOKEN | BLOCK | BLOCK | BLOCK |
| Chamar API externa | TOKEN | BLOCK | BLOCK | BLOCK |
| Spawn processo | TOKEN | BLOCK | BLOCK | BLOCK |
| Enviar mensagem | TOKEN | BLOCK | BLOCK | BLOCK |
| Publicar conteudo | TOKEN | BLOCK | BLOCK | BLOCK |
| Deploy | BLOCK | BLOCK | BLOCK | BLOCK |
| Apagar arquivo | TOKEN | BLOCK | BLOCK | BLOCK |
| Executar shell | TOKEN | BLOCK | BLOCK | BLOCK |

## Gates automaticos

### Boundary checks (todo bloco)
- Arquivo fora de `src/`, `tests/`, `docs/`? → REVISAR
- Leitura de `.env` ou `secrets/`? → BLOCK
- Import de modulo externo nao aprovado? → BLOCK
- Shell exec ou subprocess? → BLOCK

### Security checks (blocos MEDIUM+)
- Token ou credential hardcoded? → BLOCK
- API key em log ou stdout? → BLOCK
- dry_run=False sem aprovacao? → BLOCK

### Git checks (pre-commit)
- Working tree tem arquivos fora do escopo? → NAO COMMITAR
- Branch nao e a esperada? → PARAR
- Ha conflitos nao resolvidos? → PARAR

## Escalacao

1. Bloco LOW falha → debug, max 3 tentativas
2. Bloco MEDIUM falha → relatorio, decidir se pula ou para
3. Bloco HIGH bloqueado → parar wave, gerar blocker doc
4. Bloco CRITICAL tocado → parar tudo, notificar

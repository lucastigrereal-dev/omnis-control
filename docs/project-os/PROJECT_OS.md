# OMNIS Project OS

## Identidade
OMNIS Control é o motor executor e orquestrador operacional local-first.
**OMNIS executa. KRATOS observa. Aurora interpreta.**

## Diferenças críticas

| Sistema | Função | Path |
|---|---|---|
| OMNIS Control | Motor executor, orquestrador | C:\Users\lucas\omnis-control |
| KRATOS | Cockpit visual, frontend | C:\Users\lucas\kratos-mission-control (NÃO TOCAR) |
| Aurora | Intérprete, orientação | Claude Code + prompts |
| Akasha | Memória vetorial | pgvector :5432 |

## Roadmaps

| Roadmap | Escopo | Status |
|---|---|---|
| Supreme 210 | G01-G13 done, G14 App Factory W131-W140 | active |
| CCOS | P37-P42 RuntimeBridge | verify |
| Project OS | Governança operacional | bootstrap |

## Stack
Python 3.12, pytest, dataclasses (zero Pydantic exceto missions), Typer CLI, Rich console
In-memory first, mock adapters, file-backed JSONL persistence
Git worktrees for parallel development

## Authority Model
Ver CLAUDE.md — Authority Model section.

## Critérios de Pronto
- Testes passam no módulo
- Commit seletivo feito
- Wave registry atualizado
- Current state atualizado
- Nenhum segredo no diff
- Nenhum arquivo KRATOS tocado

## Critérios de Parada
- P0 detectado (segredo, risco de perda de dados)
- Conflito de merge não trivial
- Teste novo quebrando
- Working tree sujo com arquivos não classificados
- Roadmap conflitante sem decisão do Lucas

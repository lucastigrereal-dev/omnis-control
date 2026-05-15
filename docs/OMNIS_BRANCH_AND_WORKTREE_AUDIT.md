# OMNIS P46 — Branch & Worktree Audit

**Date:** 2026-05-15
**Auditor:** Claude Opus 4.7 (P46 Merge Readiness)

## Branch atual

| Field | Value |
|---|---|
| Branch | `feature/omnis-5waves-runtime-supreme` |
| HEAD | `8c32ecf` |
| HEAD message | `docs(omnis): w12b1-b10 add governance policy, consolidated security review, architecture review, test coverage, dryrun/external write/secrets audits, merge readiness, wave 13 plan, 5 waves final report` |
| master HEAD | `c136065` |
| master message | `docs(omnis): add wave 7b merge report` |
| Ahead of master | 37 commits |
| Behind master | 0 commits |
| Fast-forward possible | YES |

## Worktrees ativos

| Path | Branch | HEAD |
|---|---|---|
| C:/Users/lucas/omnis-control | `feature/omnis-5waves-runtime-supreme` | `8c32ecf` |
| .claude/worktrees/p23-autonomous-execution | `parallel/p23-autonomous-execution` | `3507331` |
| .claude/worktrees/p24-live-cockpit | `parallel/p24-live-cockpit` | `97616dc` |
| .claude/worktrees/p25-p29-sequential-supreme | `parallel/p25-p29-sequential-supreme` | `0183528` |
| C:/Users/lucas/omnis-p20-omnis-supreme (external) | `parallel/p20-omnis-supreme` | `88ef666` |

**Total:** 5 worktrees (1 main + 3 internal + 1 external)

## Branches locais

| Branch | HEAD | Notes |
|---|---|---|
| `auto-pilot/janitorial-20260506_234924` | `427e182` | Snapshot, legado |
| `feature/omnis-5waves-runtime-supreme` | `8c32ecf` | **ATIVA — esta sessao** |
| `feature/omnis-wave-7a-control-tower` | `01fef94` | Merged segundo relatorio |
| `feature/omnis-wave-7b-runtime-bridge` | `a3a3e8d` | Merged segundo relatorio |
| `fix/bug1-id-prefix-matching` | `3edb623` | Bug fix branch |
| `fix/cli-creative-status-regression` | `e6001f3` | Bug fix branch |
| `master` | `c136065` | Baseline |
| `parallel/p20-omnis-supreme` | `88ef666` | Worktree ativo |
| `parallel/p21-memory-intel` | `7e82006` | Skeleton |
| `parallel/p22-capability-forge-real` | `5c6869c` | Skeleton |
| `parallel/p23-autonomous-execution` | `3507331` | Worktree ativo |
| `parallel/p24-live-cockpit` | `97616dc` | Worktree ativo |
| `parallel/p25-p29-sequential-supreme` | `0183528` | Worktree ativo |
| `recovery/stash-fase1-creative-production` | `38cc7bd` | Recovery, legado |

## Branches remotas (origin)

| Branch | HEAD |
|---|---|
| `origin/master` | `c136065` |
| `origin/recovery/stash-fase1-creative-production` | `d2d103c` |
| `origin/sprint/aba-*` (9 branches) | Various |

## Branches merged (segundo relatorios)

- `feature/omnis-wave-7a-control-tower` → merged
- `feature/omnis-wave-7b-runtime-bridge` → merged
- P21-P45 parallel branches → merged localmente

## Branches que parecem legado

| Branch | Motivo |
|---|---|
| `auto-pilot/janitorial-20260506_234924` | Snapshot automatico de 10 dias atras |
| `recovery/stash-fase1-creative-production` | Recovery branch antiga |
| `fix/bug1-id-prefix-matching` | Bug fix — pode precisar de cherry-pick ou merge |
| `fix/cli-creative-status-regression` | Bug fix — pode precisar de cherry-pick ou merge |

## Divergencia com master

```
0 commits behind, 37 commits ahead — fast-forward merge limpo.
```

## Recomendacao de limpeza futura

**NAO EXECUTAR AGORA.** Apos merge, considerar:
1. Remover worktrees concluidos (p23, p24, p25-p29) se ja merged
2. Remover branches skeleton (p21, p22) se conteudo ja esta na principal
3. Avaliar fix branches — cherry-pick para master se correcoes forem relevantes
4. Remover branches remotas aba-* que ja foram merged
5. Manter `recovery/` branches como backup historico

**Cuidado:** Nunca apagar branches sem confirmar que conteudo foi integrado.

# OMNIS State — After P1.5

**Data:** 2026-05-08 | **Ultima fase concluida:** P1.5

---

## Estrutura Atual

```
omnis-control/
  src/
    cli.py                          # CLI principal (Typer)
    cli_commands/
      oauth_cmd.py                  # oauth probe, validate, readiness, start
      post_cmd.py                   # post preflight, package
      tools_cmd.py                  # tools health-report, list, check
      metrics_cmd.py                # metrics today, status, mission, tools, export
    oauth_readiness/
      env_probe.py                  # Safe .env reader (nunca armazena valores)
      checklist.py                  # Dynamic readiness checks (15 atuais)
      checker.py                    # Report aggregator + GO/NO-GO
    post_preflight/
      preflight.py                  # 8 checks de pre-publicacao
    metrics/
      models.py, store.py, recorder.py, aggregations.py
    tool_registry/
      registry.py, loader.py, health_checker.py
    observability/
      record_metric(), LocalTracer
  tests/
    oauth_readiness/                # 65 testes
    post_preflight/                 # 25 testes
    metrics/                        # testes de metrics
    tool_registry/                  # testes de registry
  docs/
    oauth/                          # 12 docs (P1.4 + P1.5)
    publishing/                     # 2 docs (contract + asset gate)
    state/                          # 5 snapshots
    metrics/                        # docs de metrics
    night_shift/                    # handoff docs
  data/
    metrics_spine/                  # JSONL metrics store
```

---

## Capacidades Ativas

| Capacidade | Status | Testes |
|---|---|---|
| OAuth Env Probe | 7 vars mapeadas, aliases | 24 |
| OAuth Readiness | 15 checks dinamicos | 65 |
| OAuth Callback Route | HTTP 200 (dry-run) | 6 |
| Post Preflight | 8 checks pre-pub | 25 |
| Tool Registry | 19 tools, health checks | 35+ |
| Metrics Spine | JSONL store + CLI | ~420 |
| CLI (Typer + Rich) | 4 subcommands | integrados |
| Health Report | 19 tools | funcional |

---

## Estado dos Gates

| Gate | Veredito | Dependencia |
|---|---|---|
| OAuth Real | NO-GO | META_APP_SECRET vazio |
| Primeiro Post Real | NO-GO | OAuth + asset ausente |
| Callback Route | GO | HTTP 200 implementado |
| Config Alignment | GO | Documentado |
| Env Probe | GO | 2+3 vars mapeadas |

---

## Publisher OS

| Campo | Valor |
|---|---|
| Branch | argos-evolucao-passo-0 |
| Commit | cf4b8d7 |
| Health | healthy |
| Callback | HTTP 200 dry-run |
| Working tree | dirty (arquivos pre-existentes) |

---

## Proxima Fase: P1.6

OAuth Manual Credentials Gate — requer Lucas preencher credenciais Meta manualmente antes de qualquer acao automatizada.

---

**Fim do snapshot.**

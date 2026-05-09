# P2.1 — Quality Layer Report

**Data:** 2026-05-09 | **Status:** CONCLUIDA

## Entregaveis

| Arquivo | Descricao |
|---|---|
| `src/quality_layer/checks.py` | 11 checks com pesos (critical/high/medium) |
| `src/quality_layer/service.py` | score_package() |
| `src/quality_layer/models.py` | QualityResult, QualityGrade |
| `src/cli_commands/quality_cmd.py` | CLI: quality package [--json] |

## Testes

| Suite | Testes |
|---|---|
| quality_layer | 31 PASS |
| render_engine | 38 PASS |
| asset_assignment | 23 PASS |
| offline_factory | 117 PASS |
| **TOTAL** | **209 PASS** |

## Fix aplicado

Typer single-command apps invocam sem nome de subcommand.
Solucao: `@quality_app.callback()` forca routing multi-comando correto.

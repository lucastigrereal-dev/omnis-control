# HANDOFF W10 — MissionGraph Health Monitor

**Wave:** D1-W10  
**Branch:** feature/omnis-5waves-runtime-supreme  
**Commit:** ed17012  
**Status:** ✅ GREEN

## O que foi feito

Wave final do pipeline D1. O `mission_graph` agora expõe um health report que pode ser consumido pelo sistema de health_score.

## Arquivos criados / modificados

| Arquivo | Ação | Descrição |
|---|---|---|
| `src/mission_graph/health.py` | CRIADO | `MissionGraphHealthReport` + `MissionGraphHealthMonitor` |
| `src/mission_graph/__init__.py` | MODIFICADO | Exports dos novos tipos |
| `tests/mission_graph/test_health.py` | CRIADO | 5 testes cobrindo todos os cenários |

## API pública

```python
from src.mission_graph import MissionGraphHealthMonitor, MissionGraphHealthReport

monitor = MissionGraphHealthMonitor(output_base="output/mission_graph")
report = monitor.collect()          # MissionGraphHealthReport
report.healthy                      # True se success_rate >= 0.7 ou total == 0
report.success_rate                 # 0.0–1.0
report.avg_cost_usd                 # custo médio por run
report.to_dict()                    # dict serializável para health_score
report.summary()                    # string one-liner

path = monitor.write_health_json()  # grava output/mission_graph/_health.json
```

## Como funciona

`MissionGraphHealthMonitor.collect()` varre `output/mission_graph/*/state.json` (gravados pelo `finalize_node` em cada run) e agrega:

- `total_runs` — número de runs encontradas
- `success_count` / `failure_count` — contagem por status
- `success_rate` — success / total (0.0 se sem runs)
- `total_cost_usd` / `avg_cost_usd` — custo acumulado e médio
- `total_tokens` — tokens acumulados
- `last_run_at` / `last_run_status` — dados da run mais recente (por timestamp)
- `healthy` — True se success_rate >= 0.7 OU sem runs ainda

## Testes

```
tests/mission_graph/test_health.py — 5/5 PASS
tests/mission_graph/ — 96/96 PASS (91 baseline + 5 novos)
tests/agencia/ + tests/publisher/ — 296/296 PASS
```

## Próximos passos

Ver `HANDOFF_D1_COMPLETO.md` para roadmap de integração.

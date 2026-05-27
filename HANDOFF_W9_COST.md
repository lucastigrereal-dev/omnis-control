# HANDOFF W9 — cost_tracker no grafo (D1-W9)

## Status
COMPLETO ✅ | Commit: `3ab3ecd`

## O que foi feito

### 1. MissionGraphState (src/mission_graph/mission_state.py)
- Adicionado `cost_usd: float` — custo total estimado em USD na run
- Adicionado `token_count: int` — tokens usados estimados
- `initial_state()` inicializa ambos: `cost_usd=0.0`, `token_count=0`

### 2. execute_node (src/mission_graph/nodes/execute_node.py)
- Constantes: `COST_PER_STEP_USD = 0.001` e `TOKENS_PER_STEP = 100`
- Cada chamada acumula custo: `cost_usd += 0.001`, `token_count += 100`
- Funciona tanto no caminho normal quanto no caminho de retry

### 3. finalize_node (src/mission_graph/nodes/finalize_node.py)
- `_write_state_json` inclui `cost_usd` e `token_count` no payload JSON
- Bloco CostTracker integrado (graceful degradation):
  - Registra operação `"mission_graph/{mission_id}"` no log `logs/cost_tracker.jsonl`
  - Se CostTracker indisponível → continua silenciosamente

### 4. Testes (tests/mission_graph/test_cost_tracker.py)
5 testes novos:
- `test_cost_zero_em_estado_inicial` — initial_state() tem cost_usd=0.0
- `test_cost_aumenta_por_step` — execute_node retorna cost_usd > 0
- `test_token_count_positivo` — execute_node retorna token_count > 0
- `test_custo_proporcional_steps` — 3 steps → 3x custo (mock de acumulação)
- `test_cost_no_state_json` — state.json contém "cost_usd" e "token_count"

## Integração com CostTracker existente
- `src/agencia/cost_tracker.py` rastreia operações locais (custo BRL sempre 0)
- Integração via context manager: `CostTracker(f"mission_graph/{mission_id}", dry_run=False)`
- Não existe método `.record(mission_id=..., cost_usd=..., tokens=...)` — API usa context manager
- Degradação graciosa: try/except garante que falha não quebra o grafo

## Resultado final
| Suite | Antes | Depois |
|---|---|---|
| mission_graph | 86 | 91 (+5) |
| agencia + publisher | 296 | 296 |

## Próxima Wave
W10 — a definir (ver MASTER_PLAN_D1_WAVES.md ou aguardar GO do Lucas)

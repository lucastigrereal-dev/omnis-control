# CODEX Audit — Onda 8 (P1/P2/P3)

Data: 2026-05-23  
Branch: `feature/omnis-5waves-runtime-supreme`  
Commits auditados: `9379965`, `cff067b`, `46406d3`

## 1) Segurança

## Resultado geral
- Sem novo P0 confirmado nos commits da Onda 8.
- Protocol formal `LegoCog` e ponte `SkillRunnerBridge` estão operacionais em modo dry-run e com testes verdes.

## Achados principais

1. **P1 funcional (propagação de contexto incompleta no caminho real):**  
   Em `run_full_pipeline_real()` (`src/execution_graph/mission_bridge.py`), o `run_context` recebido é usado para `graph_run_id`, mas **não é injetado ao `SkillRunnerBridge`**:
   - linha atual: `bridge = SkillRunnerBridge(dry_run=dry_run, adapter=adapter)`
   - esperado para rastreabilidade fim-a-fim: incluir `run_context=run_context`.

2. **Sem regressão de segurança direta nos Legos com `LegoCog.run()`:**
   - CodeExecutor mantém proteção anti-RCE no fallback local.
   - ChannelMessenger mantém credenciais via env + gate de broadcast.
   - Video/Browser/Research wrappers convertem spec sem uso de `eval/exec`.

## 2) Cobertura adicionada (mecânica)

Novos testes desta auditoria:
- `tests/agentic/test_skill_runner_bridge_lego.py`
  - `test_try_lego_passes_run_id_into_legocog_spec` (confirma que `run_id` chega no `LegoCogSpec`)
- `tests/execution_graph/test_mission_bridge_run_context.py`
  - `test_run_full_pipeline_real_passes_run_context_to_bridge` (**xfail**)

Motivo do `xfail`:
- Registrar explicitamente a lacuna atual sem quebrar a suíte.
- Facilitar remoção do `xfail` assim que a frente de construção fizer o ajuste.

## 3) Regressão

## Testes focados executados
- `tests/legos/test_protocol.py` → 18 passed
- `tests/mission_orchestrator/test_run_context_propagation.py` → 10 passed
- `tests/agentic/test_skill_runner_bridge_lego.py` → 14 passed
- `tests/execution_graph/test_mission_bridge_run_context.py` → 1 xfailed
- conjunto focado combinado → 42 passed, 1 xfailed

## 4) Recomendação para frente de construção

1. Ajustar `run_full_pipeline_real()` para repassar contexto:
   - de: `SkillRunnerBridge(dry_run=dry_run, adapter=adapter)`
   - para: `SkillRunnerBridge(dry_run=dry_run, adapter=adapter, run_context=run_context)`
2. Após correção, remover `xfail` e validar teste como obrigatório.


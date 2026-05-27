# HANDOFF D1-W4 — plan_node com decomposição de steps

**Branch:** feature/omnis-5waves-runtime-supreme
**Commit:** 97ea80d
**Data:** 2026-05-26
**Status:** VERDE ✅ (44 passed mission_graph, 296 passed agencia+publisher)

---

## O que foi feito

### 1. MissionGraphState — novo campo `steps`
- Arquivo: `src/mission_graph/mission_state.py`
- Campo adicionado: `steps: list[dict]` — lista de steps planejados
- `initial_state()` agora inicializa `steps=[]`

### 2. plan_node — novo nó de planejamento
- Arquivo: `src/mission_graph/nodes/plan_node.py`
- Lógica principal: chama `TaskDecomposition.create_default(mission_id)` de `src/missions/task_decomposition.py`
- Retorna steps com campos: `name`, `type`, `description`, `order`, `depends_on`
- Fallback automático se import falhar: 3 steps genéricos (`validate_input`, `execute_main`, `finalize_output`)

### 3. Grafo atualizado
- Arquivo: `src/mission_graph/mission_graph.py`
- Fluxo anterior: `validate → execute → checkpoint → finalize`
- Fluxo novo: `validate → plan → execute → checkpoint → finalize`
- `plan` tem aresta simples para `execute` (sem condicional)

### 4. Exportação
- Arquivo: `src/mission_graph/nodes/__init__.py`
- `plan_node` adicionado ao `__all__`

### 5. Testes
- Arquivo: `tests/mission_graph/test_plan_node.py`
- 5 testes:
  - `test_plan_node_retorna_steps` — steps é lista não-vazia
  - `test_plan_node_steps_tem_name` — cada step tem chave `name`
  - `test_plan_node_fallback` — sem task_decomposition → 3 steps genéricos
  - `test_steps_no_state` — `initial_state()` começa vazio, plan_node preenche
  - `test_grafo_com_plan_completa` — `run_mission_graph("m_plan", use_langgraph=True)` → status `"completed"`

---

## Arquivos não tocados (conforme regra)
- `src/missions/` — apenas lido
- `src/agentic/` — intocado
- `src/execution_graph/` — intocado

---

## Próximo passo (aguarda GO)
Wave 5: integrar `steps` no `execute_node` para iterar sobre o plano gerado pelo `plan_node`.

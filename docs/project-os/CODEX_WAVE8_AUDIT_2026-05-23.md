# CODEX Audit — Onda 8 (P0/P1/P2)

Data: 2026-05-23  
Branch: `feature/omnis-5waves-runtime-supreme`  
Commits auditados: `9379965`, `cff067b`, `46406d3`, `938eaf7`, `8321ee5`, `5a024ef`, `bac05ca`

## 1) Segurança

## Veredito executivo
- **RCE do CodeExecutor via ponte Graph→Lego: CURADO** no caminho auditado.
- **Sem novo P0** encontrado nos commits da Onda 8 auditados.
- Existe **1 gap P1** de enforcement do gate em caminho secundário (detalhado abaixo).

## Achados por prioridade

1. **P1 — caminho de escape do freio em API interna específica**  
   `run_graph_from_orchestrator()` em `src/execution_graph/mission_bridge.py` chama `run_graph_dry()` direto e não aplica `approval_center.gate` antes da execução do grafo.  
   Impacto: quem usar esse entrypoint diretamente pode executar dry-run mesmo com `approval_required=True` e sem `approval_id`.  
   Status: registrado por teste `xfail` (sem alterar comportamento).

2. **RCE curado continua curado pela nova ponte (`SkillRunnerBridge` → `LegoRegistry`)**  
   A execução real de lego de código continua bloqueando payload malicioso:
   - `CodeExecutorLego` usa subprocess com argv (sem interpolação de `goal` em código).
   - payload com quebra de linha/operadores perigosos continua barrado por `_has_unsafe_goal_payload`.
   - teste novo comprova o bloqueio **via `run_graph_real()`**, não só via chamada direta do lego.

3. **Gate unificado (`approval_center/gate.py`) cobre os status canônicos do freio**  
   Cobertura confirmada para: `not_required`, `blocked_pending_approval`, `approved`, `rejected`, `pending`.  
   Adaptadores `mission_orchestrator.approval_gate` e `execution_graph.approval_bridge` delegam para o gate compartilhado.

4. **ChannelMessengerLego (WhatsApp/Telegram)**  
   - Credenciais por `os.getenv` (sem hardcode).
   - Não executa código de input externo.
   - Gate existente para termos de broadcast/massa.  
   Observação de política (P2): envio 1:1 sem broadcast não exige approval; decisão de produto/governança.

5. **ResearchConductorLego (STORM)**  
   - Query de busca é URL-encoded.
   - Endpoint do backend vem de `SEARXNG_URL` (config de operador).  
   Risco residual baixo/moderado: sem allowlist explícita de host para ambientes multi-tenant.

## 2) Contrato LegoCog (P1)

- Todos os 5 Legos registrados em `src/legos/registry.py` implementam o contrato `LegoCog`:
  - `BrowserExecutorLego`
  - `CodeExecutorLego`
  - `VideoProcessorLego`
  - `ResearchConductorLego`
  - `ChannelMessengerLego`
- Evidência: `tests/legos/test_protocol.py` valida `isinstance(lego, LegoCog)` para os cinco.

## 3) Context Flow (P4)

- O output do passo N entra no `context_store` e é propagado para `entry.result_hint` no passo N+1.
- O fluxo atual não sanitiza semanticamente texto de contexto (apenas valida mínimo de presença/tamanho).
- **Não foi encontrado sink de execução direta desse contexto no caminho auditado** (entra como dica textual em payload, não como código executável).
- Risco residual: envenenamento semântico de contexto (qualidade/decisão), não RCE.
- Teste de caracterização adicionado confirma que contexto malicioso não sobrescreve `goal` do passo seguinte.

## 4) Cobertura adicionada (mecânica, reversível)

### Novos testes desta rodada
- `tests/execution_graph/test_lego_bridge_security.py`
  - `test_run_graph_real_blocks_unsafe_goal_payload_via_lego_bridge`  
    Prova que payload malicioso continua bloqueado quando chega pelo caminho Graph→Bridge→Lego.
- `tests/execution_graph/test_gate_escape_path.py`
  - `test_run_graph_from_orchestrator_should_block_when_approval_required` (**xfail**)  
    Documenta o escape path do gate sem quebrar a suíte.
- `tests/execution_graph/test_context_poisoning_guard.py`
  - `test_upstream_context_does_not_override_next_step_goal`  
    Prova que output malicioso do passo N permanece em `upstream_context` e não vira `goal` executável no passo N+1.

### Testes já adicionados na auditoria anterior da onda
- `tests/agentic/test_skill_runner_bridge_lego.py`
  - `test_try_lego_passes_run_id_into_legocog_spec`
  - `test_try_lego_passes_upstream_context_into_payload`
- `tests/execution_graph/test_mission_bridge_run_context.py`
  - `test_run_full_pipeline_real_passes_run_context_to_bridge` (**xfail**)
- `tests/approval_center/test_shared_gate.py`
  - `test_gate_pending_request_returns_blocked`

## 5) Regressão

### Focados (segurança/onda 8)
- `tests/execution_graph/test_lego_bridge_security.py`
- `tests/execution_graph/test_gate_escape_path.py`
- `tests/approval_center/test_shared_gate.py`  
Resultado: **12 passed, 1 xfailed**

- `tests/execution_graph/test_context_poisoning_guard.py`
- `tests/execution_graph/test_lego_bridge_security.py`
- `tests/execution_graph/test_context_flow.py`  
Resultado: **15 passed**

- `tests/agentic/test_skill_runner_bridge_lego.py`
- `tests/execution_graph/test_context_flow.py`
- `tests/legos/test_code_executor_lego.py`
- `tests/legos/test_channel_messenger_lego.py`
- `tests/legos/test_protocol.py`
- `tests/legos/test_research_conductor_lego.py`  
Resultado: **135 passed**

### Suite completa
- `python -m pytest tests/ --import-mode=importlib -p no:warnings -q`
- Resultado: **8902 passed, 4 skipped, 4 xfailed**

## 6) Recomendação para frente de construção

1. **Fechar escape path do gate (P1):**  
   em `run_graph_from_orchestrator()`, aplicar gate shared (`approval_center.gate`) antes de executar `run_graph_dry`.
2. **Fechar propagação de run_context no caminho real (P1 já mapeado):**  
   injetar `run_context` em `SkillRunnerBridge` em `run_full_pipeline_real()`.
3. Após correções da frente de construção, remover os `xfail` correspondentes e promover para teste obrigatório.

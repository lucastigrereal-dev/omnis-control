# CODEX Audit — Onda 4A/4B/5 (ResearchConductor, ChannelMessenger, LegoRegistry)

Data: 2026-05-23  
Branch: `feature/omnis-5waves-runtime-supreme`  
Escopo auditado (commitado): `6b1dcd4`, `3a71dfe`, `cf6cfd2`

## 1) Segurança

## Resultado geral
- Sem novo P0 confirmado nos módulos da Onda 4/5.
- Nenhuma credencial hardcoded encontrada nos arquivos novos de `research_conductor`, `channel_messenger` e `registry`.
- Risco médio pré-existente permanece fora deste escopo: DSN com `password=postgres` em `src/memory_unification/memory_router.py` (já registrado em ondas anteriores; não alterado por esta auditoria).

## Achados
1. **P1 (arquitetural, não mecânico)** — `src/legos/research_conductor_lego.py`
   - Chamada de LLM via `litellm.completion(...)` direta no módulo do lego, sem passar pelo router canônico de modelos.
   - Risco: drift de governança de roteamento/custos entre legos.
   - Ação do auditor: **só sinalização** (muda contrato/comportamento, fica para frente de construção).

2. **P2 (input boundary)** — `src/legos/research_conductor_lego.py`
   - `spec.output_dir` é aceito e usado para persistência sem normalização canônica.
   - Risco: escrita fora de diretório esperado se input vier de fonte não confiável.
   - Ação do auditor: **só sinalização** (mudança de comportamento; decisão da frente de construção).

3. **P2 (SSRF/config misuse potencial)** — `src/legos/channel_messenger_lego.py`
   - `WA_API_URL` é configurável por env.
   - Risco: URL interna indevida caso ambiente seja comprometido.
   - Mitigação atual: depende de hardening de ambiente; sem ação mecânica segura local sem mudar comportamento.

## 2) Cobertura de testes (adicionado por Codex)

Foram adicionados testes de caracterização para branches de erro/concorrência que não estavam cobertos:

- `tests/legos/test_research_conductor_lego.py`
  - `test_execute_returns_timeout_when_research_semaphore_busy`
  - `test_execute_returns_error_when_pipeline_raises`

- `tests/legos/test_channel_messenger_lego.py`
  - `test_telegram_no_chat_id_returns_error`
  - `test_send_returns_timeout_when_dispatch_semaphore_busy`

Objetivo: travar comportamento atual em cenários de falha, sem alterar código de produção.

## 3) Limpeza cirúrgica

- Nenhuma mudança em produção nesta rodada.
- Apenas testes mecânicos/reversíveis.

## 4) Regressão

## Testes focados
- `tests/legos/test_research_conductor_lego.py` → **28 passed**
- `tests/legos/test_channel_messenger_lego.py` → **32 passed**
- `tests/legos/` → **149 passed**

## Suite completa
- `python -m pytest tests/ --import-mode=importlib -p no:warnings -q`
- Resultado: **8744 passed, 4 skipped, 0 failed**

Baseline preservado e ampliado.

## 5) Recomendação para frente de construção (Claude Code)

1. Unificar estratégia de roteamento LLM do `ResearchConductorLego` com o router canônico do projeto (sem quebrar compatibilidade local-first).
2. Definir boundary de escrita para `output_dir` (allowlist base dir + normalização de path).
3. Avaliar allowlist de host em `WA_API_URL` para evitar misuse em ambiente comprometido.


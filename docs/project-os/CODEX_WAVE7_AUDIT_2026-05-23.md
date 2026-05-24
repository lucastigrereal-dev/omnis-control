# CODEX Audit — Onda 7 / Onda 7-OTel

Data: 2026-05-23  
Branch: `feature/omnis-5waves-runtime-supreme`  
Commits auditados: `5b273e3`, `6843ccf`

## 1) Segurança

## Resultado geral
- Sem novo P0/P1 de injeção direta ou segredo hardcoded nos arquivos auditados.
- `LiteLLMAdapter` mantém chamadas HTTP via `urllib` sem `eval/exec/subprocess`.

## Achados
1. **P1 Operacional (regressão funcional):**
   - `scripts/omnis_service.py` instancia `SchedulerService(dry_run=_DRY_RUN)`.
   - A assinatura atual de `SchedulerService.__init__` não expõe `dry_run`.
   - Efeito prático: o ciclo pode falhar por incompatibilidade de assinatura e seguir em loop apenas logando erro.

2. **P2 de boundary/configuração:**
   - `LITELLM_BASE_URL` é aceito sem validação adicional de host/scheme.
   - Risco de misuse via ambiente comprometido; não é RCE direto no código auditado.

## 2) Cobertura adicionada (mecânica)

Arquivos de teste alterados:
- `tests/scripts/test_omnis_service.py`
  - `test_scheduler_constructor_signature_compatible_with_service_call` (xfail)
- `tests/utils/test_llm_tracer.py`
  - `test_exporter_none_has_no_in_memory_exporter`
  - `test_otlp_env_without_exporter_dependency_does_not_crash`

Motivo:
- Tornar explícita a regressão de compatibilidade no daemon sem quebrar a suíte.
- Cobrir branches do tracer (`none` e OTLP sem dependência instalada).

## 3) Regressão

## Testes focados
- `tests/agentic/test_batch_runner_run_context.py` → 5 passed
- `tests/agentic/test_llm_adapter_retry.py` → 9 passed
- `tests/utils/test_run_context.py` → 19 passed
- `tests/utils/test_llm_tracer.py` → 10 passed
- `tests/scripts/test_omnis_service.py` → 7 passed, 1 xfailed

## Suite completa
- `python -m pytest tests/ --import-mode=importlib -p no:warnings -q`
- Resultado: **8780 passed, 4 skipped, 1 xfailed, 0 failed**

## 4) Recomendação para frente de construção

1. Corrigir incompatibilidade entre `omnis_service` e `SchedulerService`:
   - ou remover `dry_run` do construtor no script e aplicar `dry_run` via factory/config,
   - ou aceitar explicitamente `dry_run` no `SchedulerService` (com uso real no fluxo).
2. Após correção, remover `xfail` e exigir teste compatível passando.


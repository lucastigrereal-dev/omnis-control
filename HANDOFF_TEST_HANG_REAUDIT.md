# HANDOFF — Reaudit de testes pendurados no omnis-control

Data: 2026-05-25
Repo: `C:\Users\lucas\omnis-control`

## Pedido

Investigar a suite pytest que pendura por muito tempo, identificar teste culpado com timeout curto, diagnosticar a causa, corrigir se for simples/seguro e provar que nao pendura mais.

## Ambiente real encontrado

- `pytest` global falhou antes da coleta com `ImportError: cannot import name 'Config' from '_pytest.config'`.
- `.venv\Scripts\python.exe -m pytest` tambem falhou por instalacao incompleta de dependencias internas de pytest/pygments.
- Para conseguir auditar sem instalar pacote externo, foi usado pytest local copiado para `.test_pytest/` e `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`.
- `pytest-timeout` nao estava disponivel de forma saudavel; a deteccao foi feita com timeout externo por processo.

## Culpa confirmada e corrigida

Teste que prendia:

`tests/legos/test_video_processor_lego.py::test_transcribe_real_returns_semaphore_timeout_when_busy`

Diagnostico:

- O teste segura `_VIDEO_SEMAPHORE`.
- Em seguida chama `lego.execute(... dry_run=False)` esperando `video_semaphore_timeout`.
- O codigo de producao fazia `_VIDEO_SEMAPHORE.acquire(timeout=120)`.
- Resultado: o teste aguardava ate 120 segundos para validar um caminho de erro simples.
- Nao era CRM, Akasha ou rede externa. Era timeout interno de semaforo alto demais para teste unitario.

Correcao aplicada:

- `src/legos/video_processor_lego.py`
  - criado `_VIDEO_SEMAPHORE_TIMEOUT_SECONDS = float(os.getenv("VIDEO_SEMAPHORE_TIMEOUT_SECONDS", "120"))`
  - `_transcribe()` agora usa esse valor no `acquire`.
  - default de producao continua 120s.

- `tests/legos/test_video_processor_lego.py`
  - o teste usa `monkeypatch` para reduzir `_VIDEO_SEMAPHORE_TIMEOUT_SECONDS` para `0.1`.
  - o teste continua validando o mesmo comportamento: retorno `video_semaphore_timeout`.
  - nao foi deletado nem enfraquecido.

## Prova da correcao pontual

Comando:

```powershell
$env:PYTHONPATH=(Resolve-Path '.test_pytest').Path
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest -q -p no:cacheprovider --tb=short tests\legos\test_video_processor_lego.py::test_transcribe_real_returns_semaphore_timeout_when_busy
```

Saida:

```text
.                                                                        [100%]
1 passed in 0.24s
```

## Prova do arquivo afetado

Comando:

```powershell
$env:PYTHONPATH=(Resolve-Path '.test_pytest').Path
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest -q -p no:cacheprovider --tb=short tests\legos\test_video_processor_lego.py
```

Saida relevante:

```text
......F..E...EE.........E..                                              [100%]
1 failed, 22 passed, 4 errors in 1.65s
```

Veredito:

- O arquivo nao pendurou mais.
- O teste corrigido passou.
- Falhas restantes neste arquivo nao sao o hang corrigido:
  - `test_health_check_true_when_whisper_and_ffmpeg_available` falha porque `health_check()` retorna `False` neste ambiente.
  - erros com `tmp_path`/`basetemp` ocorreram por permissao negada no ambiente de sandbox.

## Varredura arquivo-a-arquivo

Foi executado scan dos 685 arquivos `tests/**/test_*.py`, com timeout externo de 60s por arquivo.

Resumo bruto:

```text
files=685 elapsed=1075.51s
timeouts=5
TIMEOUT_FILE: tests\oauth_readiness\test_oauth_readiness_checker.py 60.01
TIMEOUT_FILE: tests\oauth_readiness\test_oauth_readiness_cli.py 60.01
TIMEOUT_FILE: tests\test_e2e.py 60.01
TIMEOUT_FILE: tests\test_event_listener.py 60.02
TIMEOUT_FILE: tests\workflows\test_content_brief_e2e.py 60.02
slow=9
failures=277
```

## Novos culpados especificos encontrados

### OAuth readiness

Arquivos:

- `tests/oauth_readiness/test_oauth_readiness_checker.py`
- `tests/oauth_readiness/test_oauth_readiness_cli.py`

Resultado por teste:

```text
test_checker_returns_report ~9.85s
test_checker_infra_checks_exist ~8.93s
test_checker_env_var_checks_exist ~8.94s
test_checker_produces_aggregated_counts ~8.90s
test_checker_has_checked_at_timestamp ~8.94s
test_checker_produces_next_action ~8.91s
test_checker_overall_status_is_valid ~8.95s
test_checker_checks_are_valid ~8.91s
test_env_probe_never_leaks_values ~8.96s

test_readiness_runs ~9.36s
test_readiness_json ~9.50s
test_readiness_json_has_core_checks ~9.30s
test_readiness_json_has_env_vars ~9.29s
test_checklist_runs ~9.35s
test_checklist_mentions_probe ~9.30s
test_start_blocks_without_readiness ~9.31s
test_start_never_executes_real_oauth ~9.33s
```

Diagnostico provavel:

- Cada teste chama o readiness real.
- O checklist executa checks reais de infra (`docker`, Redis, Supabase, Publisher OS, rede).
- Ha timeouts internos de ate 10s/5s por chamada.
- O problema nao e um unico teste infinito; e repeticao de checks externos lentos sem mock/cache por teste.

### Event listener

Arquivo:

- `tests/test_event_listener.py`

Testes que excederam 12s:

```text
TIMEOUT_TEST tests/test_event_listener.py::TestRedisConnectivity::test_connect_to_redis
TIMEOUT_TEST tests/test_event_listener.py::TestChannelSubscription::test_subscribe_to_channels
TIMEOUT_TEST tests/test_event_listener.py::TestReconnectBehavior::test_reconnect_on_disconnect
```

Diagnostico provavel:

- Testes tentam Redis real em `localhost:6382`.
- `src/event_listener.py` tem `socket_connect_timeout=5`, loop de listen e `_reconnect()` com backoff/sleep.
- Quando Redis esta ausente/lento, a suite espera conexao/reconexao real.
- Correcao segura exigiria mockar Redis nesses testes ou separar testes de integracao com marker/skip por disponibilidade.

### E2E geral

Arquivo:

- `tests/test_e2e.py`

Teste especifico que excedeu 12s:

```text
TIMEOUT_TEST tests/test_e2e.py::TestE2E7Seguranca::test_no_outside_files_modified
```

Observacao:

- O arquivo inteiro tambem passa de 60s por acumulacao de subprocessos reais do CLI.
- Ha varios testes de CLI levando ~5s cada.
- Correção pode envolver timeouts/mocks nos comandos CLI ou separar e2e real de unitario.

### Content brief E2E

Arquivo:

- `tests/workflows/test_content_brief_e2e.py`

Teste especifico:

```text
TIMEOUT_TEST tests/workflows/test_content_brief_e2e.py::test_real_ollama_brief_oinatalrn_carousel
```

Diagnostico:

- O teste marcado `@pytest.mark.real_llm` chama Ollama real (`http://localhost:11434`) com timeout default de 120s.
- Esse e teste de integracao real, nao deveria rodar na suite curta sem disponibilidade confirmada do servico.

## Zona vermelha acionada

Depois da correcao pontual, ainda existem multiplos pontos independentes de lentidao/hang:

- OAuth readiness chama infra real repetidamente.
- Redis event listener tenta Redis real/reconnect.
- E2E geral roda comandos CLI reais.
- Content brief chama Ollama real.

Isso passa do limite de "poucos testes envolvidos". Por isso nao corrigi esses novos grupos nesta rodada.

## Arquivos alterados/criados nesta rodada

Alterados:

- `src/legos/video_processor_lego.py`
- `tests/legos/test_video_processor_lego.py`

Criados para auditoria/execucao local:

- `.test_pytest/`
- `.test_shims/`
- `HANDOFF_TEST_HANG_REAUDIT.md`

Observacao:

- A tentativa de usar `--basetemp` criou diretorios temporarios com permissao problematica no sandbox:
  - `.pytest_tmp/`
  - `tmp_pytest_codex/`
- Nao foram apagados porque a instrucao foi nao apagar nada.

## Veredito

✅ O culpado inicial e simples foi corrigido: `test_transcribe_real_returns_semaphore_timeout_when_busy` nao prende mais.

🔴 A suite completa ainda nao esta limpa: ha pelo menos 5 arquivos que excedem 60s por dependerem de servicos reais/subprocessos/LLM local.

## Proximo passo seguro

Rodada 2 separada, sem misturar com esta correcao:

1. Marcar testes reais de Redis/Ollama/infra com markers claros (`integration`, `real_llm`, `requires_redis`, `requires_docker`).
2. Criar fixtures de disponibilidade com skip rapido.
3. Mockar chamadas de infra nos testes unitarios de OAuth readiness.
4. Definir comando de suite curta, por exemplo: excluir `_archive`, `real_llm` e integracoes reais.
5. So depois rodar suite completa real com servicos ligados e timeout total controlado.

## Divida mapeada (registrada)

Rodada 2: separar testes de infra real (Docker/Redis/Ollama) com markers `requires_docker`/`requires_redis`/`real_llm`, para a suite unitaria nao pendurar.

Prioridade baixa: modulos-alvo ja rodam em 3.5s.

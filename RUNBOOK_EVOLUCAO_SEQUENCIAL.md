# RUNBOOK — Modo Evolução Sequencial

**Versão:** 1.0 | **Criado:** 2026-05-24 | **Modo:** Autônomo sequencial

## Regra única
Verde segue. Vermelho conserta. Catastrófico para e chama.

## Safe Defaults por Workflow

### WF3 — App Factory
| Parâmetro | Valor padrão |
|-----------|-------------|
| `dry_run` | `True` — nunca escreve em disco sem GO explícito |
| `deploy_mode` | `"mock"` — planner em modo dry_run, sem persistência |
| `output_dir` | `output/app_factory/<run_id>/` |
| `approval_required` | `False` — gate passa automaticamente em dry_run |
| `package_export` | in-memory (zip em disco somente com `dry_run=False`) |
| `execution_graph` | validação de topologia apenas — nunca runner real |
| `openhands` | mock sempre — nunca container real |

### Decisões default (das 5 pendentes do plano)
1. **Scaffold location:** `output/app_factory/<run_id>/` — dentro de OMNIS_ROOT
2. **Approval gate behavior:** retorna `error="approval_required"` silencioso (não cria draft)
3. **Deploy mock:** OpenHands mock está fora do pipeline principal (mock passthrough)
4. **ExecutionGraph:** validação de grafo apenas (`_validate_graph_dry()`), runner OFF
5. **Package export:** in-memory para testes; zip em disco somente com `dry_run=False`

## Catraca (`omnis_gate.py`)

Após cada onda, executar:
```sh
python scripts/omnis_gate.py
```

5 checks obrigatórios verdes:
1. Tests de workflows passando
2. Sem segredos em staged files
3. Imports resolvem
4. Arquivos de workflows existem
5. Sem P0 blockers

## STOP RULES absolutas
- RCE (Remote Code Execution) → PARA, chama Lucas
- Secret em produção exposto → PARA, chama Lucas
- Perda de dados confirmada → PARA, chama Lucas
- Deploy real disparado → PARA, chama Lucas
- Envio externo real (email, Slack, API) → PARA, chama Lucas

## Decisão A/B
- Anota em `EVOLUCAO_LOG.md` com `[A/B]`
- Escolhe a opção mais conservadora (menor risco)
- Segue sem esperar GO

## Vermelho na catraca
1. Lê o erro
2. Conserta na source (não bypassa)
3. Roda catraca de novo
4. Só avança se verde

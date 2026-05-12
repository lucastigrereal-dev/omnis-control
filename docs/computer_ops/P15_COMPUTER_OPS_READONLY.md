# P15 Computer Ops Read-Only — Especificacao

**Criado:** 2026-05-12 | **Branch:** parallel/p15-computer-ops-readonly | **Versao:** 1.0.0

## Objetivo

Frente de auditoria read-only do sistema. Modela planos de auditoria, achados (findings), candidatos a limpeza e regras de seguranca — sem nunca executar acoes destrutivas.

## Escopo

### Permitido
- `src/computer_ops/` — Pacote principal
- `tests/computer_ops/` — Testes unitarios
- `docs/computer_ops/` — Documentacao

### Proibido
- `src/mission/`, `src/app_factory/`, `src/automation/`, `src/analytics/`, `src/governance/`, `src/output_generator/`
- `src/cli.py`, `src/core/`
- `data/**`, `exports/**`, `logs/**`
- `.env`, `pyproject.toml`

## Modelos

| Modelo | Descricao |
|---|---|
| `AuditTarget` | Alvo de auditoria (disco, projeto, docker, sistema) |
| `DiskFinding` | Achado de auditoria de disco (uso, % ocupado) |
| `ProjectFinding` | Achado de auditoria de projeto (arquivos, tamanho) |
| `DockerFinding` | Achado de auditoria de recursos Docker |
| `CleanupCandidate` | Candidato a limpeza — classificado, nunca deletado diretamente |
| `ComputerOpsReport` | Relatorio agregador de todos os achados |

## Serviços

| Funcao/Classe | Descricao |
|---|---|
| `ComputerOpsPlanner` | Planejador deterministico de operacoes |
| `build_readonly_audit_plan()` | Constroi plano de auditoria sem executar |
| `classify_cleanup_candidate()` | Classifica candidato aplicando regras de seguranca |
| `generate_safe_cleanup_plan()` | Gera plano de limpeza com quarentena e revisao |

## Regras de Seguranca

1. **Read-only por padrao** — Toda operacao comeca como `dry_run=True`
2. **Quarentena antes de delete** — `CleanupCandidate` nunca aceita `ACTION_DELETE` na criacao
3. **Nenhuma acao destrutiva** — `DESTRUCTIVE_ACTIONS = {ACTION_DELETE}` e sempre bloqueado
4. **Revisao humana obrigatoria** — Candidatos > 1GB ou sem dados de acesso requerem revisao

### Fluxo Seguro de Limpeza

```
IDENTIFIED -> CLASSIFIED -> QUARANTINED -> (aprovacao humana) -> DELETE
                                                              \-> KEEP/ARCHIVE
```

## Estrutura do Pacote

```
src/computer_ops/
├── __init__.py     # API publica, __all__
├── models.py       # 6 dataclasses + constantes
├── service.py      # Planner, funcoes core
├── errors.py       # 10 excecoes hierarquicas

tests/computer_ops/
├── __init__.py
├── conftest.py     # Fixtures compartilhadas
├── test_models.py  # 70+ testes de modelos
├── test_service.py # 20+ testes de servico

docs/computer_ops/
└── P15_COMPUTER_OPS_READONLY.md  # Este arquivo
```

## Constantes

| Grupo | Valores |
|---|---|
| Target Types | `disk`, `project`, `docker`, `system` |
| Severities | `low`, `medium`, `high`, `critical` |
| Actions | `quarantine`, `archive`, `delete` (bloqueado), `keep`, `review` |
| Statuses | `identified`, `classified`, `quarantined`, `archived`, `deleted`, `rejected` |
| Report Statuses | `draft`, `final`, `archived` |

## Testes

```bash
python -m pytest tests/computer_ops/ -q
```

Cobertura:
- Round-trip `to_dict()`/`from_dict()` para todos os modelos
- Valores padrao e fully-populated
- Propriedades calculadas (`is_critical`, `is_warning`, `size_mb`, `is_safe`)
- Regras de seguranca (bloqueio de DELETE, quarentena obrigatoria)
- Filtragem de targets desabilitados
- Parametrizacao de tipos/severidades/acoes validas

## Nao Escopo (para frentes futuras)

- Integracao com CLI (`cli.py`)
- Leitura real de disco (psutil/shutil)
- Conexao real com Docker SDK
- Integracao com Akasha/Gringotts
- Execucao real de quarentena (move/rename)
- Workflows n8n para computer ops

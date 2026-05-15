# OMNIS SUPREME 210 WAVES — Test Strategy

**Date:** 2026-05-15

---

## Baseline

| Metric | Value |
|---|---|
| Full suite baseline | 5,902 passed, 3 skipped |
| Tempo full suite | ~17 min |
| Source modules | 90+ |
| Test files | 465+ |

## Estrategia por tipo de wave

### Waves de codigo (src/ changes)
- **Targeted:** `python -m pytest tests/<module>/ --import-mode=importlib -p no:warnings -v`
- **Pre-commit:** targeted do modulo alterado
- **Post-wave:** targeted + smoke dos modulos adjacentes
- **Post-grupo (10 waves):** full suite `python -m pytest tests/ --import-mode=importlib -p no:warnings -q`

### Waves de documentacao (docs/ only)
- Nao requer pytest
- Validar: arquivos existem, links coerentes, markdown valido

### Waves de CLI (cli_commands/ changes)
- `python -m pytest tests/ -k "cli" --import-mode=importlib -p no:warnings -v`
- Smoke test de help: comandos respondem sem crash

### Waves de seguranca (security boundaries)
- `python -m pytest tests/ -k "security or guard" --import-mode=importlib -p no:warnings -v`
- Import guard scan: `grep -r "secret\|token=\|api_key=\|password=" src/ --include="*.py"`

## Testes minimos por bloco

| Bloco | Teste minimo |
|---|---|
| B1 (Models) | to_dict/from_dict roundtrip |
| B2 (Service) | Unit test do metodo principal |
| B3 (Gate) | Block/unblock scenarios |
| B4 (Executor) | dry_run=True default + dry_run=False behavior |
| B5 (CLI) | --help nao crasha |
| B6 (Events) | Event emit + log contains expected fields |
| B7 (Integration) | Smoke test e2e |
| B8 (Docs) | File exists, frontmatter valid |
| B9 (Edge) | 2+ edge cases cobertos |
| B10 (Validation) | Wave report gerado |

## Comandos padrao

```sh
# Targeted module
python -m pytest tests/<module>/ --import-mode=importlib -p no:warnings -v

# Full suite (post-grupo ou pre-merge)
python -m pytest tests/ --import-mode=importlib -p no:warnings -q

# CLI-only
python -m pytest tests/ -k "cli" --import-mode=importlib -p no:warnings -v

# Single test file
python -m pytest tests/<module>/test_<file>.py --import-mode=importlib -p no:warnings -v

# Import guard scan
grep -r "secret\|token=\|api_key=\|password=\|OAuthReal\|publish_real\|send_real\|deploy_real" src/ --include="*.py"
```

## Quando rodar full suite

- A cada 10 waves concluidas (fim de grupo)
- Antes de qualquer merge
- Quando modulos core sao alterados (control_tower, runtime_orchestrator, omnis_control)
- Antes de push (se autorizado)

## Quando NAO rodar full suite

- Waves docs-only
- Blocos que so adicionam arquivos em docs/supreme_210/
- Testes unitarios isolados que nao tocam shared models

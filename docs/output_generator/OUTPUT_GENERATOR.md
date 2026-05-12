# Output Generator — Deterministic Local Writers

**Modulo:** `src/output_generator/` | **Config:** `config/output_generators.yaml`
**Status:** P10.0 Registry implementado

---

## Conceito

Output Generators sao funcionarios deterministicos locais. NUNCA chamam LLM, NUNCA acessam rede.

Cada generator sabe escrever um tipo de output a partir de um contrato (OutputContract do WorkOrder).

---

## Generators Registrados

| Generator ID | Output Types | Risk | Status |
|---|---|---|---|
| markdown_basic_writer | markdown, mission_report, delivery_package | low | active |
| json_basic_writer | json | low | active |
| spec_basic_writer | technical_spec, app_spec, data_model | medium | active |
| html_preview_writer | html_preview | low | planned |
| zip_package_writer | zip_package | low | planned |

---

## Selecao

`select_generator(output_type)` → `OutputGeneratorSelection`:

- Active generators sao preferidos
- Planned-only retorna `PLANNED_ONLY` (nao usado por padrao)
- Sem match retorna `NO_GENERATOR`

---

## CLI

```
python -m src.cli output-generator list
python -m src.cli output-generator show <id>
python -m src.cli output-generator select <output_type>
```

Flags: `--json` para saida JSON.

---

## Runtime

Outputs gerados vao para `exports/generated_outputs/<output_id>/` (gitignored).

---

## Testes

28 testes em `tests/output_generator/`:
- test_models.py (8) — enums, dataclasses
- test_registry.py (6) — load YAML, get, list, errors
- test_selector.py (5) — active/planned/no_match selection
- test_cli.py (8) — CLI list/show/select commands

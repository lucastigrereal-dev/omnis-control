# CODEX Audit — Onda 6 (CLI Lego)

Data: 2026-05-23  
Branch: `feature/omnis-5waves-runtime-supreme`  
Commit auditado: `b99df17` (`src/cli_lego.py`, integração em `src/cli.py`, testes CLI)

## 1) Segurança

## Resultado geral
- Não foi identificado novo P0/P1 no escopo do commit.
- `cli_lego` não executa shell diretamente e não usa `eval/exec`.
- Fluxos de risco ficam delegados para legos já auditados (`code_executor`, `research_conductor`, `channel_messenger`).

## Achados
1. **P2 (governança de input)** — `src/cli_lego.py`
   - O comando `send` aceita `--channel` livre; canais inválidos só falham em runtime no lego.
   - Não é falha de segurança crítica, mas pode gerar ruído operacional.
   - Ação do auditor: sem alteração de comportamento no core; cobertura adicionada para garantir falha controlada.

2. **P3 (robustez de UX de erro)** — `src/cli_lego.py`
   - Branches de erro em `research --real` e `send --real` não estavam totalmente caracterizados por teste.
   - Ação do auditor: adicionados testes de caracterização para travar comportamento de saída/exit code.

## 2) Cobertura adicionada (mecânica)

Arquivo alterado:
- `tests/cli/test_cli_lego.py`

Novos testes:
- `test_research_real_publish_keyword_exits_1`
- `test_research_real_publish_keyword_json_reports_error`
- `test_send_real_unknown_channel_exits_1`
- `test_send_real_unknown_channel_json_reports_error`

Objetivo:
- Cobrir branches de erro do modo real sem tocar código de produção.

## 3) Regressão

## Teste focado
- `python -m pytest tests/cli/test_cli_lego.py --import-mode=importlib -p no:warnings -q`
- Resultado: **22 passed**

## Suite completa
- `python -m pytest tests/ --import-mode=importlib -p no:warnings -q`
- Resultado: **8748 passed, 4 skipped, 0 failed**

Baseline preservado e melhorado.

## 4) Recomendação para frente de construção

1. Avaliar validação explícita de `--channel` no nível da CLI (Typer choice / enum) para reduzir erro de operador.
2. Manter política de erro estruturado em JSON para automações consumidoras de CLI.


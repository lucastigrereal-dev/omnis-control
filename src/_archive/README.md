# src/_archive — Módulos Arquivados

Módulos movidos aqui são FANTASMA ou LEGADO confirmados:  
— sem imports externos ativos  
— sem testes (FANTASMA) ou com testes mas fora do caminho ativo (LEGADO)  
— zero risco de regredir a suite ao arquivar

**Regras:**
- Nunca deletar daqui sem GO explícito do Lucas
- Para reativar: `git mv src/_archive/X src/X` + reverter README + rodar suite
- Não criar novos módulos aqui — usar apenas para arquivar

---

## Módulos arquivados

| Módulo | Classe | Data | Motivo |
|---|---|---|---|
| `health` | FANTASMA | 2026-05-22 | Tinha pipeline.py mas zero imports externos e zero tests. Health real está em `src/omnis_health/` |
| `omnis_control` | FANTASMA | 2026-05-22 | Tinha cli.py/models.py/queue.py com import quebrado em `__init__.py`. Zero tests, zero imports externos. Nome conflita com o repo raiz |
| `backlog` | LEGADO | 2026-05-22 | Tem browser_executor.py e tests mas zero imports externos. Sem papel ativo no caminho CLI |
| `executors` | LEGADO | 2026-05-22 | Tem `__init__.py`, models.py, runner.py e tests mas zero imports externos no src/ atual |
| `parallel_runner` | LEGADO | 2026-05-22 | Tem models.py, runner.py e tests mas zero imports externos. Substituído funcionalmente por execution_graph |
| `governance_core` | LEGADO | 2026-05-22 | Tem DecisionLog e HumanSlot (código real); zero tests; zero imports externos. Nota: se governance canônica precisar de Human Slot, criar em `src/governance/` — não reativar este |

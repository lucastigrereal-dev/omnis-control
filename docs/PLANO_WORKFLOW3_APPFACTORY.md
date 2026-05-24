# PLANO — Workflow 3: App Factory ponta a ponta

**Status:** RASCUNHO — aguarda GO do Lucas antes de qualquer implementação  
**Data:** 2026-05-24 (noite autônoma, Onda 10)  
**Risco estimado:** 8/10 — NÃO CONSTRUIR sem GO explícito

---

## Por que este plano existe

Os Workflows 1 e 2 foram construídos na noite autônoma (Onda 10). O Workflow 3 (App Factory)  
**não foi construído** porque:
- App Factory gera código e potencialmente dispara scaffolding em disco
- O pipeline tem um passo de deploy mock → nenhum deploy deve acontecer sem GO
- O approval gate precisa ser validado com o Lucas antes de ativar o código gerador

Este documento registra o molde proposto para revisão. **Nada é implementado aqui.**

---

## Molde proposto

```
AppFactoryWorkflow.run(idea_text, dry_run=True)
    │
    ├─ 1. RunContext.new()           → run_id único
    │
    ├─ 2. AppFactoryPlanner.plan()   → AppArtifact (PRD + DB schema + API contracts)
    │        ← Lego existente: src/app_factory/planner.py
    │        ← Requer: dry_run=True até approval gate
    │
    ├─ 3. APPROVAL GATE ─────────────────────────────────────────────────────────
    │        SE dry_run=True  → retorna plano SEM gerar código
    │        SE dry_run=False → exige approval_required=False no AppArtifact
    │        SE approval_required=True → retorna error="approval_required"
    │        ← Mesmo padrão do ResearchConductorLego e VideoEditWorkflow
    │
    ├─ 4. build_planning_pipeline()  → AppFactoryPipelineResult
    │        ← Lego existente: src/app_factory/pipeline.py
    │        ← Scaffolding de arquivos — apenas se dry_run=False + approved
    │
    ├─ 5. ExecutionGraph validation  → dry_run do grafo
    │        ← Infraestrutura existente: src/execution_graph/
    │        ← NÃO executa steps reais — só valida topologia
    │
    ├─ 6. Package export             → zip do app gerado
    │        ← Existente: src/app_factory/package_exporter.py (se existir)
    │
    └─ 7. AkashaSinkAdapter.write()  → evento com run_id, app_name, risco
           ← Mesmo padrão dos Workflows 1 e 2
```

---

## Legos reusados (peças existentes)

| Lego | Localização | Papel no workflow |
|------|-------------|-------------------|
| `AppFactoryPlanner` | `src/app_factory/planner.py` | Gera PRD + schema + API contracts |
| `build_planning_pipeline()` | `src/app_factory/pipeline.py` | Executa pipeline completo de geração |
| `ExecutionGraph` | `src/execution_graph/builder.py` | Valida topologia do grafo de tasks |
| `RunContext` | `src/utils/run_context.py` | run_id + budget enforcement |
| `AkashaSinkAdapter` | `src/akasha_event_sink/adapter.py` | Persiste evento com run_id |

---

## Approval gate — onde fica e como funciona

O gate existe em **2 níveis**:

### Nível 1 — workflow entry (mesmo padrão WF1/WF2)
```python
def run(self, idea_text: str, dry_run: bool = True) -> AppFactoryResult:
    ctx = RunContext.new()
    plan = self._planner.plan(AppIdea(text=idea_text), dry_run=True)  # SEMPRE dry_run=True aqui
    
    if not dry_run:
        if plan.approval_required:
            return AppFactoryResult(
                run_id=ctx.run_id, success=False,
                error="approval_required",
                artifacts={"plan_summary": plan.summary, "approval_required": True},
            )
        # Só chega aqui se dry_run=False E approval_required=False
        pipeline_result = build_planning_pipeline(plan.idea_id, dry_run=False)
    else:
        return AppFactoryResult(run_id=ctx.run_id, success=True, dry_run=True, plan=plan)
```

### Nível 2 — geração de código (deploy mock)
- `build_planning_pipeline(dry_run=False)` cria arquivos em disco
- Nenhum arquivo é criado fora do `OMNIS_ROOT` ou `PUBLISHER_OS_DIR`
- O package export produz um `.zip` — não faz deploy automaticamente

---

## Pontos de risco identificados

| # | Risco | Nível | Mitigação proposta |
|---|-------|-------|-------------------|
| R1 | Pipeline gera código em disco sem dry_run=False aprovado | 8 | Gate duplo: workflow + pipeline |
| R2 | `AppFactoryPlanner.plan()` pode chamar LLM real em modo não-dry | 6 | Forçar `dry_run=True` na chamada do planner até gate |
| R3 | `build_planning_pipeline()` não tem proteção de path por padrão | 7 | Validar `OMNIS_ROOT` antes de chamar |
| R4 | Package export pode produzir zip com credenciais hardcoded | 9 | Scan de segredos no zip antes de salvar |
| R5 | ExecutionGraph pode ter steps que fazem IO real | 5 | Usar `_validate_graph_dry()` apenas, nunca o runner real |
| R6 | AppArtifact pode ter `approval_required=True` não checado | 7 | Assertion explícita no workflow antes de prosseguir |

**Risco global: 8/10 — PARA até GO do Lucas.**

---

## O que precisa de decisão do Lucas antes de construir

1. **Escopo do scaffold:** O workflow gera um app novo em disco ou valida um conceito de app?  
   Se gerar em disco → onde? `output/app_factory/<run_id>/`?

2. **Approval gate behavior:** `dry_run=False` + `approval_required=True` deve:  
   (a) retornar erro silencioso, ou (b) criar um draft para revisão humana?

3. **Deploy mock:** O OpenHands mock step está no pipeline ou fora?  
   Se dentro → requer setup do container OpenHands.

4. **Integração com ExecutionGraph:** Usar o runner real (Onda 8) ou só validar o grafo?

5. **Package export:** Zip em disco ou zip in-memory (para teste)?

---

## Arquivos a criar (quando houver GO)

```
src/workflows/app_factory_workflow.py      ← molde principal
tests/workflows/test_app_factory_e2e.py   ← 30+ testes E2E
```

Nenhum arquivo existente deve ser modificado.

---

## STOP — não implementar

Este documento é um plano de design. A implementação começa **somente após GO explícito do Lucas**  
confirmando as decisões da seção acima.

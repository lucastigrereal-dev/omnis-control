# MERGE_LOCKS — Travas de Merge Ativas
**Atualizado:** 2026-05-22 | Wave A: Verdade do Disco

---

## 🔴 LOCK ATIVO — kratos-0-10-operational-truth

**PROIBIDO** mergear `feature/kratos-0-10-operational-truth` em `feature/omnis-5waves-runtime-supreme`  
**sem antes** passar pela triagem **T-006** das 60 falhas confirmadas.

### Evidência
- Preflight T-000 (2026-05-22) rodado em `feature/kratos-0-10-operational-truth` encontrou:
  - **8786 passed / 60 failed** — 58 falhas não conhecidas, sem ticket
- Branch `feature/omnis-5waves-runtime-supreme` está em **8853 passed / 0 failed**
- Merge sem triagem introduziria 60 regressões na branch principal

### T-006 — Triagem obrigatória antes do merge

| Cluster | Falhas | Decisão necessária |
|---|---|---|
| `capability_forge_real` | 28 | Corrigir antes (núcleo de auto-evolução) |
| `skill_router_bridge` (→ `skills_bridge`) | 9 | Verificar: diretório foi renomeado — revisar se testes ainda falham |
| `observability` | 7 | Corrigir antes (AuditTrail = rastreabilidade) |
| `integration` | 1 | Verificar impacto |
| `omnis_health` | 3 | Ticket já existe (T-105) |
| `checkers` | 4 | Débito aceito com ticket |
| `execution_graph` | 1 | Débito aceito com ticket |
| `e2e/skill_runner` | 4 | Corrigir path (~ vs omnis-control/skills/) |

### Para destravar
1. Rodar `python -m pytest tests/ --import-mode=importlib -p no:warnings -q` na branch `kratos-0-10-operational-truth`
2. Todos os clusters acima classificados como: `corrigir-agora | débito-aceito-com-ticket | descartar`
3. Suite >= 8800 passed, 0 failed inesperado
4. GO explícito de Lucas para o merge

---

## Histórico de locks

| Lock | Branch bloqueada | Data criação | Status |
|---|---|---|---|
| LOCK-001 | `kratos-0-10-operational-truth` | 2026-05-22 | 🔴 ATIVO |

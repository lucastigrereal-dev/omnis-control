---
name: qa-merge-gate
description: Validar branch antes de merge.
---

# qa-merge-gate

## Objetivo
Impedir regressÃ£o.

## Checklist
1. Teste do mÃ³dulo.
2. Suite completa.
3. Scan de secrets/chamadas reais.
4. Handoff report existe.
5. Conflict scan.
6. QA report PASS/FAIL.

## Regra
Sem PASS, sem merge.

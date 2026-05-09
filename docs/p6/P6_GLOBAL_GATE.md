# P6 Global Gate

**Data:** 2026-05-09  
**Branch:** master  
**Commit atual:** 11dd585  
**Suite baseline:** 1559 passed, 4 skipped, 0 failures  

## Objetivo P6

Fechar o loop entre gap detectado e capability planejada:

```
gap → proposal → spec → approval → register planned → skill_matcher vê planned
```

## 5 blocos

| Block | Nome |
|---|---|
| P6.0 | Capability Proposal Generator |
| P6.1 | Capability Spec Exporter |
| P6.2 | Capability Approval Bridge |
| P6.3 | Register Approved Capability |
| P6.4 | Gap → Planned Capability E2E |

## Restrições

- NÃO cria código executável automático
- NÃO registra capability `active` sem implementação real
- NÃO usa LangGraph/CrewAI/OpenHands
- OAuth Meta: CONGELADO
- Post real: NO-GO

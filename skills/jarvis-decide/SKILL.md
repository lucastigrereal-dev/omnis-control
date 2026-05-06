---
name: jarvis-decide
description: |
  Decision Engine: prioriza oportunidades/ações usando fórmula composta.
  Input: lista de oportunidades. Output: score ranked com recomendação.
trigger:
  - após jarvis-delegate quando múltiplas opções
  - "qual é a melhor opção?"
  - "prioriza isso"
  - "o que fazer primeiro?"
sector: cross-cutting
risk: low
model: haiku
approval_required: []
status: active
version: 1.0
reads:
  - ~/.claude/registry/decision_engine.yaml
cost_estimate: "$0.0005/run"
verification_criteria:
  - Score calculado para cada oportunidade
  - Ranking explícito (1-N)
  - Recomendação clara: fazer, sugerir, ignorar
  - Output em < 3 segundos
---

# Skill: jarvis-decide

Decision Engine: prioriza oportunidades usando fórmula composta.

## Quando usar

- Múltiplas opções concorrentes
- "qual a melhor opção?"
- "prioriza"
- "o que fazer primeiro?"

## Fórmula

```
score = receita × 0.30 + desbloqueio × 0.20 + chance × 0.15
      + urgencia × 0.15 + reaproveitamento × 0.10 + energia × 0.05
      - risco × 0.10 - complexidade × 0.10
```

Thresholds: >= 7.0 = executar | >= 4.0 = sugerir | < 4.0 = ignorar

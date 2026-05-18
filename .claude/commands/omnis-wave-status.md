# /omnis-wave-status [wave_id]

Status detalhado de uma wave ou de todas.

## Ações
1. Se wave_id fornecido: buscar no WAVE_REGISTRY.md
2. Se não: listar todas as waves não-DONE
3. Mostrar: status, commits, testes, blockers

## Output
```
WAVE STATUS {{WAVE_ID_OR_ALL}}
{{WAVE_ID}} — {{NAME}} — {{STATUS}}
Commits: {{COMMITS}}
Testes: {{TEST_RESULT}}
Gate atual: {{CURRENT_GATE}}
Próximo bloco: {{NEXT_BLOCK}}
```

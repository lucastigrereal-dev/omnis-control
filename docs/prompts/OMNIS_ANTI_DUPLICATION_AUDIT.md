# OMNIS Anti-Duplication Audit Prompt

```md
Você está no projeto OMNIS CONTROL. Modo READ-ONLY.

Sua missão: verificar se esta branch/worktree está duplicando trabalho já feito em outra branch.

## Auditoria
1. Leia `omnis_wave_registry.yaml` — identifique waves com status DONE ou REVIEW
2. Leia `omnis_worktrees.yaml` — identifique worktrees com escopos sobrepostos
3. Rode `git log --oneline -20` nesta branch
4. Compare com commits listados no wave registry

## Perguntas Críticas
- Alguma wave nesta branch já está DONE no registry?
- Algum módulo já foi implementado em outra branch?
- Os commits desta branch são funcionalmente idênticos a commits de outra branch?

## Relatório
Entregue:
- Waves nesta branch: [lista]
- Waves já DONE/REVIEW no registry que conflitam: [lista]
- Módulos sobrepostos com outros worktrees: [lista]
- Veredito: SAFE_TO_CONTINUE | DUPLICATE_DETECTED | NEEDS_MERGE_FIRST

NÃO implemente nada. NÃO edite arquivos. Apenas audite e reporte.
```

# OMNIS Finalization Manual

## Como Fechar G14 App Factory
- Todas as waves W131-W140 + W133-W162 estão DONE
- App Factory Advanced concluído em master (06caa49)
- Nenhuma ação pendente

## Como Fechar CCOS
- Verificar estado real com Lucas
- Se ainda ativo: terminar ou abandonar com decisão explícita
- Se inativo: marcar como CLOSED no registry

## Como Gerar RC Local
1. Seguir `RELEASE_CANDIDATE_CHECKLIST.md`
2. Rodar `/omnis-rc`
3. Reportar GO/NO-GO ao Lucas

## Como Preparar Próximo Bloco
1. Atualizar ROADMAP.md — mover concluídos para verde
2. Identificar próximo milestone com Lucas
3. NÃO iniciar novo milestone sem decisão do Lucas
4. Criar handoff em `.claude/state/last-handoff.md`

## Sem Deploy/Push
- Toda finalização é LOCAL
- Lucas decide quando fazer push
- Nenhum deploy automático

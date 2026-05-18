# /omnis-close-wave <wave_id>

Fecha uma wave concluída.

## Ações
1. Verificar que wave existe e não está DONE
2. Confirmar que todos os gates (B1-B10) passaram
3. Confirmar que testes passam
4. Preencher WAVE_CLOSE_TEMPLATE.md
5. Atualizar WAVE_REGISTRY.md — marcar DONE + commit hash
6. Atualizar CURRENT_STATE.md
7. Atualizar .claude/state/wave-registry.json
8. Comitar atualizações de state

## Stop rules
- Gate pendente → não fechar
- Testes quebrando → não fechar
- Sem commit → não fechar

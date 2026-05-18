# OMNIS Claude Runbook

## Protocolo de Início de Sessão

1. Ler `CLAUDE.md`
2. Ler YAMLs: `omnis.project.yaml`, `omnis_state.yaml`, `omnis_wave_registry.yaml`, `omnis_worktrees.yaml`, `omnis_blocked_items.yaml`, `omnis_guardrails.yaml`
3. Rodar:
   - `git status --short`
   - `git branch --show-current`
   - `git log -1 --oneline`
4. Identificar branch/worktree atual e escopo permitido
5. Verificar P0/P1 abertos

## Protocolo Antes de Editar

1. Confirmar que o arquivo alvo está no escopo da branch atual
2. Verificar se a wave não é duplicata (consultar `omnis_wave_registry.yaml`)
3. Se houver worktree paralelo no mesmo domínio: pausar e auditar duplicação

## Protocolo Antes de Commit

1. `git status --short` — confirmar arquivos modificados
2. `git diff --stat` — revisar escopo das mudanças
3. Rodar testes do domínio afetado
4. Verificar que nenhum segredo está staged
5. Stage seletivo: `git add <arquivos específicos>`
6. NUNCA `git add .`

## Protocolo Depois de Commit

1. `git status` — confirmar working tree limpo (no escopo)
2. Atualizar `omnis_wave_registry.yaml` se wave concluída
3. Atualizar `omnis_state.yaml` se estado mudou
4. Reportar commit hash + arquivos incluídos

## Protocolo de Parada

Parar IMEDIATAMENTE se:
- Encontrar segredo exposto
- Encontrar P0 não documentado
- Testes quebrarem por causa da mudança atual
- Conflito de merge com trabalho não commitado
- Branch errada (escopo não bate com worktree)

## Como Escolher Próxima Ação

1. Verificar `omnis_state.yaml` → `next_safe_actions`
2. Prioridade: P0 → P1 → P2
3. Confirmar que a ação é segura na branch/worktree atual
4. Se nada seguro: entregar relatório de bloqueador

## Como Evitar Duplicação

1. SEMPRE consultar `omnis_wave_registry.yaml` antes de iniciar wave
2. SEMPRE consultar `omnis_worktrees.yaml` para ver branches paralelas
3. Se wave já tem status DONE ou REVIEW: NÃO EXECUTAR
4. Se worktree paralelo cobre o mesmo domínio: AUDITAR antes de agir

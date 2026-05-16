# PLAYBOOK â€” Frentes Paralelas OMNIS CCOS

## Regra maior
NÃ£o abrir todas as frentes ao mesmo tempo antes de gates de seguranÃ§a.

## Ordem segura inicial
1. Agent Architect: P37 RuntimeBridge planning.
2. Agent QA: validaÃ§Ã£o da suite base e merge gate.
3. Depois liberar P38 e P39 em paralelo, se nÃ£o houver colisÃ£o.
4. P41 sÃ³ depois de P37 estabilizado.
5. P40 depois de P37 + P41.
6. P42 depois de base de eventos/status.

## Frentes
- `../omnis-runtime-bridge` â€” feat/p37-runtime-bridge
- `../omnis-approval-core` â€” feat/p38-approval-core
- `../omnis-capability-forge` â€” feat/p39-capability-forge
- `../omnis-memory-core` â€” feat/p40-memory-core
- `../omnis-akasha-sink` â€” feat/p41-akasha-sink

## Prompt coordenador
Leia `CLAUDE.md`, `docs/OMNIS_WAVE_7B.md`, `docs/MERGE_FLOW_CCOS.md` e este playbook.
Atue como `agent-architect`.
Diga quais frentes podem iniciar agora, quais dependÃªncias existem e qual a melhor ordem de merge.
NÃ£o implemente nada ainda.

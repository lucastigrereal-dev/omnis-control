# OMNIS â€” Wave 7B / Sprint 2

## P37 â€” RuntimeBridge
Criar ponte explÃ­cita entre `execution_graph` e `execution_queue`.

## P38 â€” Approval Core
Unificar `approval_center` e `approval_runtime` em `approval_core`, mantendo backward compatibility.

## P39 â€” CapabilityForge
Consolidar `capability_forge_lite`, `capability_forge_real` e `capabilityforge` em `capability_forge`.

## P40 â€” Memory Core
Unificar `memory`, `memory_intel` e `knowledge_context` em camadas claras.

## P41 â€” Akasha Event Sink
Criar pipeline de eventos persistidos para histÃ³rico auditÃ¡vel.

## P42 â€” Live Cockpit v2
Painel operacional com status vivo dos agentes.

## Ordem recomendada
1. P37 RuntimeBridge
2. P38 Approval Core
3. P39 CapabilityForge
4. P41 Akasha Event Sink
5. P40 Memory Core
6. P42 Live Cockpit v2

## Regra
Se dois Ã©picos tocam os mesmos arquivos, merge sequencial obrigatÃ³rio.

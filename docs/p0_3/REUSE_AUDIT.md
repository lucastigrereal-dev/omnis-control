# P0.3 — Auditoria de Reuso

**Data:** 2026-05-06
**Branch:** master (286f23a)
**Testes:** 319/319 ✅

## Mapeamento Source → Destino

| Fonte (omnis-codigos-completos.md) | Destino | Status | Ação |
|-------------------------------------|---------|--------|------|
| §1.1 SQL migration (lines 29-103) | `migrations/001_unified_publish_pipeline.sql` | AUSENTE | **Criar** (adaptado: local) |
| §1.2 statemachine.py (lines 109-218) | `src/publisher/statemachine.py` | AUSENTE | **Criar** (cópia verbatim) |
| §1.3 pipeline.py (lines 224-550) | `src/publisher/pipeline.py` | AUSENTE | **Criar** (adaptado: MetaAPIDryRun) |
| §1.4 worker.py (lines 556-660) | `src/publisher/worker.py` | AUSENTE | **Criar** (cópia verbatim) |
| §2.1 logging_config.py (lines 668-736) | `src/observability/logging_config.py` | AUSENTE | **Criar** (cópia verbatim) |
| §2.2 tracer.py (lines 742-919) | `src/observability/tracer_local.py` | AUSENTE | **Criar** (adaptado: sem Langfuse) |
| §3.2 registrymanager.py (lines 1064-1174) | `src/capabilityforge/registrymanager.py` | AUSENTE | **Criar** (adaptado: thread-safe) |
| §3.3 policy.py (lines 1180-1279) | `src/capabilityforge/policy.py` | AUSENTE | **Criar** (cópia verbatim) |
| §3.4 orchestrator.py (lines 1286-1479) | `src/capabilityforge/orchestrator.py` | AUSENTE | **Criar** (proposal-only) |
| §3.5 cli.py (lines 1485-1572) | `src/capabilityforge/cli.py` | AUSENTE | **Criar** (adaptado: typer) |

## Arquivos NOVOS

| Arquivo | Descrição |
|---------|-----------|
| `src/integrations/metaapi_dryrun.py` | Mock Meta API — JSONL |
| `src/observability/tracer_local.py` | Tracer local (sem Langfuse) |
| `src/capabilityforge/models.py` | Dataclasses do forge |
| `src/capabilityforge/lifecycle.py` | FSM CreationState |
| `src/cli_commands/publisher_cmd.py` | Comandos publisher CLI |
| `src/cli_commands/forge_cmd.py` | Comandos forge CLI |

## Conflitos

- `src/cli_commands/__init__.py` existe — adicionar imports
- `src/integrations/__init__.py` existe — estender
- Nenhum conflito que exija parada

## Decisões

1. SQL: remover `organization_id`, usar `account_handle`
2. Pipeline: `MetaAPIDryRun` + `JsonLStore` substituem dependências externas
3. RegistryManager: `threading.Lock` em vez de `FileLock`
4. Orchestrator: `build_skill()` → `NotImplementedError`
5. CLI Forge: `typer` em vez de `click`

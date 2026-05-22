# OMNIS CANONICAL EXECUTION

Version: 1.0 | Ratified: 2026-05-19 | Authority: CCOO Architecture Constitution v1.0

---

## Module Identity

- **Module:** OMNIS
- **Verb:** EXECUTA
- **Role:** Motor de missões — squads, workflows, criaturas
- **Canonical Repository:** `omnis-control`
- **Git:** `feature/omnis-5waves-runtime-supreme`

---

## Variant Classification

| Variant | Classification | Path | Reason |
|---------|---------------|------|--------|
| **omnis-control** | **CANONICAL** | `C:\Users\lucas\omnis-control` | Largest (9056 files), CLI complete, mission templates, Qdrant, Docker SDK |
| omnis-maintenance | MAINTENANCE | `C:\Users\lucas\omnis-maintenance` | Duplicate of omnis-runtime |
| omnis-runtime | EXPERIMENTAL | `C:\Users\lucas\omnis-runtime` | Duplicate of omnis-maintenance |
| omnis-server | EXPERIMENTAL | `C:\Users\lucas\omnis-server` | Minimal Node.js state server, no git |

**Note:** omnis-maintenance and omnis-runtime are structural duplicates (identical skills/, src/, config/). Future merge recommended.

---

## Canonical Entrypoint

```bash
cd C:\Users\lucas\omnis-control
omnis --help     # Python CLI via typer
jarvis --help    # alias
```

### Dependencies
- typer, rich (CLI)
- httpx (HTTP client)
- pyyaml (config)
- psutil (system monitoring)
- docker (Docker SDK)
- qdrant-client (vector database)
- Pillow (image processing)

---

## What OMNIS DOES

- Executa missões via templates JSON
- Orquestra squads (app_factory, marketing, ops, sales, security)
- Gerencia skills de automação
- Conecta-se a Qdrant (vector DB)
- Monitora Docker containers

## What OMNIS DOES NOT DO

- NÃO observa o ecossistema (KRATOS faz)
- NÃO armazena memória semântica (AKASHA faz)
- NÃO organiza notas humanas (OBSIDIAN faz)
- NÃO decide estratégia sozinho (Lucas decide)

---

## Integration Points

| Target | Via | Status |
|--------|-----|--------|
| AKASHA | akasha_event_sink (filesystem) | CONFIRMED |
| Qdrant | qdrant-client (SDK) | CONFIRMED |
| Docker | docker (SDK) | CONFIRMED |
| KRATOS | /omnis/status (REST) | HYPOTHESIS |

---

## Current State

- 47 files modified, not committed (branch: feature/omnis-5waves-runtime-supreme)
- Templates: 17 automation + 6 marketing + 11 missions + 5 squads
- Missions: MIS-20260518-001 through MIS-20260518-011

---

## References

- CCOO Architecture Constitution v1.0
- CCOO Master Roadmap — FASE 3
- omnis-control/pyproject.toml

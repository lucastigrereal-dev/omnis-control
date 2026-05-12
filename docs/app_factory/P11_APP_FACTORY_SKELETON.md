# P11 App Factory Skeleton

Frente paralela isolada. Gera PRDs, schemas, blueprints e estruturas de projeto de forma determinística — sem LLM, sem rede, sem Docker.

**Status:** Skeleton completo — 75 testes passando.
**Data:** 2026-05-12
**Branch:** `parallel/p11-app-factory-skeleton`

---

## Arquitetura

```
src/app_factory/
  __init__.py                   # vazio (padrão OMNIS)
  errors.py                     # AppFactoryError → InvalidAppIdea, Planner, PRD, Structure
  models.py                     # AppIdea, AppRequirement, AppBlueprint, AppArtifact
  planner.py                    # AppFactoryPlanner (pipeline determinístico)
  prd_generator.py              # generate_prd() → markdown
  structure_generator.py        # generate_project_structure() → dict tree
```

### Fluxo

```
AppIdea → AppRequirement → AppBlueprint → AppArtifact
                                          ├── prd_markdown (str)
                                          ├── project_structure (dict)
                                          └── tech_stack_summary (dict)
```

Cada etapa é puramente determinística: regras de keyword detection, templates e heurísticas. Mesma entrada = mesma saída (exceto timestamps e IDs randômicos).

---

## Modelos

### AppIdea

Input bruto do usuário.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `idea_id` | str | ID único (`idea_xxxxxxxxxx`) |
| `title` | str | Título do app (obrigatório, max 200) |
| `description` | str | Descrição (obrigatório) |
| `target_audience` | str | Público-alvo |
| `features` | list[str] | Funcionalidades desejadas |
| `constraints` | list[str] | Restrições (orçamento, tech, prazo) |
| `domain` | str | Domínio de negócio |
| `submitted_at` | str | ISO timestamp |
| `status` | str | `draft` → `planned` → `generated` |

**Factory method:** `AppIdea.new(title, description, ...)`

### AppRequirement

Requisitos estruturados extraídos deterministicamente.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `requirement_id` | str | `req_xxxxxxxxxx` |
| `idea_id` | str | FK → AppIdea |
| `functional` | list[str] | FR-01, FR-02... |
| `non_functional` | list[str] | NFR-01, NFR-02... |
| `domain_entities` | list[str] | Entidades detectadas |
| `user_roles` | list[str] | Roles detectados |
| `app_type` | str | web, api, cli, mobile, desktop, library |
| `generated_at` | str | ISO timestamp |

**Factory method:** `AppRequirement.from_idea(idea)`

### AppBlueprint

Blueprint arquitetural com módulos, data models, API endpoints e árvore de componentes.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `blueprint_id` | str | `bp_xxxxxxxxxx` |
| `requirement_id` | str | FK → AppRequirement |
| `modules` | list[dict] | Módulos do app |
| `data_models` | list[dict] | Modelos de dados |
| `api_endpoints` | list[dict] | Endpoints REST |
| `component_tree` | dict | UI components hierárquica |
| `tech_stack` | dict | Frontend, backend, DB, cache |
| `generated_at` | str | ISO timestamp |

**Factory method:** `AppBlueprint.from_requirement(req)`

### AppArtifact

Artefato final: PRD markdown + estrutura de projeto planejada.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `artifact_id` | str | `art_xxxxxxxxxx` |
| `blueprint_id` | str | FK → AppBlueprint |
| `prd_markdown` | str | PRD completo em markdown |
| `project_structure` | dict | Árvore de diretórios planejada |
| `tech_stack_summary` | dict | Resumo do stack |
| `generated_at` | str | ISO timestamp |

**Factory method:** `AppArtifact.from_blueprint(bp, prd_md, structure)`

---

## AppFactoryPlanner

Pipeline determinístico principal.

```python
from src.app_factory.planner import AppFactoryPlanner
from src.app_factory.models import AppIdea

planner = AppFactoryPlanner()

# Dry-run: gera tudo sem persistir
idea = AppIdea.new("Blog Engine", "content management system", features=["posts", "comments", "auth"])
artifact = planner.plan(idea, dry_run=True)

print(artifact.prd_markdown)         # PRD completo
print(artifact.project_structure)    # Tree planejada

# Non dry-run: persiste em data/app_factory_plans.jsonl
artifact = planner.plan(idea, dry_run=False)

# Batch
ideas = [AppIdea.new(f"App {i}", f"desc {i}") for i in range(5)]
artifacts = planner.plan_batch(ideas, dry_run=True)
```

---

## Geração Determinística

### Keyword Detection Rules

| Keyword PT/EN | Efeito |
|---------------|--------|
| auth, login, cadastro, password | Adiciona módulo auth + user model |
| admin, dashboard, painel | Adiciona role admin + AdminDashboard |
| api, rest, endpoint | App type = API |
| cli, terminal, script | App type = CLI |
| mobile, ios, android | App type = MOBILE |
| crud, create, edit, delete | Templates CRUD |
| search, busca, filtro | Templates search |
| produto, product, carrinho | Entidade product |
| pedido, order, compra | Entidade order |
| pagamento, payment, billing | Entidade payment |
| email, notificacao, alert | Módulo notifications |

### Tech Stack por App Type

| App Type | Frontend | Backend | Database |
|----------|----------|---------|----------|
| web | React + TypeScript | Python FastAPI | PostgreSQL |
| api | N/A | Python FastAPI | PostgreSQL |
| cli | N/A | Python + Typer | SQLite |
| mobile | React Native + TS | Python FastAPI | PostgreSQL |
| desktop | Electron + React + TS | Python FastAPI | SQLite |
| library | N/A | Python library | N/A |

---

## Testes

```bash
python -m pytest tests/app_factory/ -q
```

Cobertura:

| Arquivo | Testes | O que cobre |
|---------|--------|-------------|
| `test_models.py` | 23 | Criação, validação, round-trip, detecção de tipos/roles/entidades |
| `test_planner.py` | 13 | Pipeline dry-run, persist, batch, erros, determinismo |
| `test_prd_generator.py` | 12 | Seções do PRD, tabelas, features, constraints, footer |
| `test_structure_generator.py` | 9 | Estrutura Python, readme, gitignore, no side effects |
| `test_errors.py` | 7 | Hierarquia de exceções |
| **Total** | **75** | |

---

## Regras Respeitadas

- [x] Zero dependências externas obrigatórias
- [x] Zero chamadas de rede
- [x] Zero Docker
- [x] Zero OpenHands
- [x] Não toca `src/mission/`, `src/output_generator/`, `src/cli.py`, `src/core/`
- [x] Não altera `data/`, `exports/`, `logs/`, `.env`, `pyproject.toml`
- [x] Determinístico: mesma entrada = mesma saída
- [x] 75/75 testes passando

---

## Próximos Passos (fora do escopo deste skeleton)

- Integração com CLI (`src/cli.py` → router `app-factory`)
- Geração real de arquivos (não só planejamento seco)
- Templates customizáveis por domínio
- Validação de schemas via JSON Schema
- Suporte a mais linguagens (Go, Rust, JS/TS completo)

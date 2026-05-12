# P10.12 — Mission Package Adapter Spec

**Data:** 2026-05-12 | **Status:** SPEC (sem código)
**Base:** P10 sealed (d016042..92589b2) + P2 mission_builder + P3 missions

---

## 1. Objetivo

Definir a interface de adaptação entre o **P10 Output Generator** (fábrica de outputs físicos, selada) e o **Mission Package** (orquestração de missão completa, a construir em P11).

**Regra de ouro:** P10 NÃO é alterado. Nenhum arquivo em `src/output_generator/` é modificado. O adapter USA a API pública existente do P10.

---

## 2. Análise do Gap Atual

### 2.1 O que existe

```
mission_builder (P2)
  ├── build_plan()         → MissionPlan
  ├── export_package()     → MissionPackageManifest (6 arquivos .md)
  └── run()                → (MissionPlan, MissionPackageManifest)

missions (P3)
  ├── MissionContract      → Pydantic BaseModel (imutável, content-hash)
  ├── JsonlRepository      → persistência JSONL de contratos
  └── MissionStatus        → Enum: 10 estados

output_generator (P10) ← SELADO
  ├── OutputWriterService  → facade: write(), write_json(), write_csv(), write_spec(), orchestrate()
  ├── ManifestRegistry     → JSONL append-only, queryable por work_order_id
  ├── validate_package()   → 5 checks de integridade
  ├── prepare_submission() → dry-run → approval_center.request_approval()
  └── run_batch()          → scan WOs, filter, process

approval_center (P4)
  └── request_approval()   → ApprovalRequest (subject, description, capability_id, risk_level)
```

### 2.2 O que NÃO existe (o gap)

```
MissionPlan ──???──> WorkOrders ──???──> P10.orchestrate() ──???──> MissionPackage agregado
```

Hoje o `mission_builder/package_exporter.py` cria um diretório `04_outputs/` **vazio**. Não há código que:
1. Transforme um `MissionPlan` em `WorkOrders`
2. Chame `P10.orchestrate()` para cada Work Order
3. Agregue os outputs gerados de volta no Mission Package
4. Produza um relatório consolidado de missão

---

## 3. Modelo de Dados — MissionPackage

```python
# src/mission_package/models.py (NOVO, a criar em P11)

@dataclass
class MissionContext:
    """Contexto completo de uma missão — o 'prontuário'."""
    mission_id: str                         # FK → MissionPlan.mission_id
    contract: dict                          # MissionContract.model_dump()
    plan: dict                              # MissionPlan.to_dict()
    squad: dict | None = None               # SquadPlan (futuro)
    created_at: str = ""                    # ISO timestamp

@dataclass
class MissionPackage:
    """Pacote completo de missão — contexto + outputs + approvals + logs."""
    mission_id: str
    context: MissionContext
    work_orders: list[dict]                 # Lista de work_order.json (crus)
    output_packages: list[dict]             # Resultados de P10.orchestrate() por WO
    approval_requests: list[dict]           # ApprovalRequest.to_dict()
    logs: list[dict]                        # Linhas de log da execução
    manifest_registry_entries: list[dict]   # Entradas do ManifestRegistry desta missão
    closeout: dict | None = None            # Relatório final (compilado ao final)
    status: str = "draft"                   # draft | generating | validating | approved | done
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict: ...
    def to_json(self, path: Path) -> None: ...
```

### Schema do MissionPackage em disco

```
exports/mission_packages/<mission_id>/
├── 01_mission_brief.md           # ← já existe (P2)
├── 02_context_used.md            # ← já existe (P2)
├── 03_execution_plan.md          # ← já existe (P2)
├── 04_outputs/                   # ← hoje VAZIO, será populado pelo P10
│   ├── wo_<wo_id_1>/
│   │   ├── output.md
│   │   ├── output.json
│   │   ├── output.csv
│   │   └── package_manifest.json
│   ├── wo_<wo_id_2>/
│   │   └── ...
│   └── _batch_manifest.json      # NOVO: agrega todos os WOs
├── 05_exports/                   # ← já existe (P2)
├── 06_next_action.md             # ← já existe (P2)
├── mission_manifest.json         # ← já existe (P2)
├── mission_package.json          # NOVO: MissionPackage.to_dict() completo
├── approvals.jsonl               # NOVO: log de approvals desta missão
└── mission.log.jsonl             # NOVO: log de execução
```

---

## 4. Interface do Adapter — MissionPackageBuilder

```python
# src/mission_package/builder.py (NOVO, a criar em P11)

from src.output_generator import OutputWriterService, ManifestRegistry
from src.output_generator.validator import validate_package
from src.output_generator.approval_bridge import prepare_submission

class MissionPackageBuilder:
    """Orquestrador de missão completa.
    
    USA P10 como motor de output. NUNCA reimplementa writers, manifest,
    validação ou batch.
    """

    def __init__(
        self,
        writer_service: OutputWriterService,        # ← REUSA P10
        manifest_registry: ManifestRegistry,         # ← REUSA P10
        packages_root: Path | None = None,
        approvals_log: Path | None = None,
        mission_log: Path | None = None,
    ): ...

    # ── Fase 1: Entrada ──

    def from_mission_plan(self, plan: MissionPlan) -> MissionPackage:
        """Cria MissionPackage a partir de um MissionPlan (P2).
        Extrai account_handle, intent, steps e gera Work Orders."""
        ...

    def from_mission_contract(self, contract: MissionContract) -> MissionPackage:
        """Cria MissionPackage a partir de um MissionContract (P3).
        Lê acceptance_criteria, expected_deliverables, budget, sector."""
        ...

    # ── Fase 2: Execução ──

    def build(self, package: MissionPackage, dry_run: bool = True) -> MissionPackage:
        """Orquestra a geração de todos os outputs da missão.
        
        1. Itera sobre work_orders do MissionPackage
        2. Para cada WO: chama self.writer_service.orchestrate(wo_id)
        3. Coleta resultados em output_packages
        4. Agrega entries do manifest_registry
        5. Se !dry_run: chama prepare_submission() para cada WO
        6. Atualiza status do MissionPackage
        """
        ...

    # ── Fase 3: Validação ──

    def validate(self, package: MissionPackage) -> dict:
        """Validação agregada de todos os outputs da missão.
        
        Retorna: {
            mission_id, overall_valid, wo_count, wo_valid_count,
            wo_failed_count, checks_aggregated, issues, warnings
        }
        """
        ...

    # ── Fase 4: Aprovação ──

    def submit_for_approval(self, package: MissionPackage, dry_run: bool = True) -> dict:
        """Submete TODOS os outputs ao approval_center.
        
        Agrega resultados de prepare_submission() por WO.
        Retorna: {mission_id, submissions: [...], all_approved, dry_run}
        """
        ...

    # ── Fase 5: Relatório ──

    def closeout(self, package: MissionPackage) -> dict:
        """Compila relatório final da missão.
        
        Retorna: {
            mission_id, total_wo, total_outputs, total_files,
            total_approvals, duration_seconds, status, issues, learning_notes
        }
        """
        ...

    # ── Persistência ──

    def save(self, package: MissionPackage) -> Path:
        """Persiste MissionPackage completo em disco.
        Escreve mission_package.json + approvals.jsonl + mission.log.jsonl
        Retorna o path do diretório do pacote."""
        ...

    @classmethod
    def load(cls, mission_id: str, packages_root: Path | None = None) -> MissionPackage:
        """Carrega MissionPackage do disco."""
        ...
```

---

## 5. Fluxo de Delegação ao P10

```
MissionPackageBuilder.build(package, dry_run=True)
  │
  ├─► Para cada WO em package.work_orders:
  │     │
  │     ├─► writer_service.orchestrate(wo_id)    ← CHAMADA ÚNICA ao P10
  │     │     │
  │     │     ├── build_package(wo, outputs_root)
  │     │     │   ├── write_markdown_output()
  │     │     │   ├── write_json_output()
  │     │     │   ├── write_csv_output()
  │     │     │   └── write_spec_output()
  │     │     │
  │     │     ├── manifest_registry.register() × N
  │     │     │
  │     │     └── validate_package(wo_id)
  │     │
  │     └─► Coleta output_packages[i] = result
  │
  ├─► Agrega manifest_registry_entries via registry.list_by_work_order()
  │
  └─► Retorna MissionPackage populado
```

**Zero reimplementação.** Cada WO vira exatamente 1 chamada a `orchestrate()`.

---

## 6. Pontos de Extensão para P11/P12/P13

### P11 — Mission Package Builder (código)
- Implementar `src/mission_package/builder.py` conforme interface acima
- 8+ testes: from_plan, from_contract, build_dry_run, build_live, validate_aggregated, submit_approval, closeout, save_load_roundtrip
- Depende de: `src/output_generator/` (API pública), `src/mission_builder/models.py`

### P12 — App Factory Skeleton
- `src/app_factory/mission_app.py`: app standalone que wrappa MissionPackageBuilder
- CLI: `omnis app-factory new-mission "<request>" --account @lucastigrereal`
- NÃO mexe em: `src/output_generator/`, `src/mission_package/`

### P13 — Automation/n8n Skeleton
- `src/automation/mission_trigger.py`: webhook que dispara MissionPackageBuilder
- NÃO mexe em: `src/output_generator/`, `src/mission_package/`

### P14 — Analytics/BI Skeleton
- `src/analytics/mission_dashboard.py`: agrega métricas de MissionPackage
- Lê: `exports/mission_packages/*/mission_package.json`
- NÃO mexe em: `src/output_generator/`, `src/mission_package/`

---

## 7. Tabela de Responsabilidades

| Camada | Responsabilidade | Módulo | Altera P10? |
|--------|-----------------|--------|-------------|
| **MissionPackageBuilder** | Orquestração de missão | `src/mission_package/` | NÃO — USA a API |
| **OutputWriterService** | Geração de arquivos físicos | `src/output_generator/` | — (selado) |
| **ManifestRegistry** | Registro de outputs | `src/output_generator/` | — (selado) |
| **Validator** | Integridade de pacote | `src/output_generator/` | — (selado) |
| **Approval Bridge** | Submissão ao approval_center | `src/output_generator/` | — (selado) |
| **Batch Runner** | Processamento em lote | `src/output_generator/` | — (selado) |
| **MissionPlan** | Plano de missão | `src/mission_builder/` | — (existente) |
| **MissionContract** | Contrato imutável | `src/missions/` | — (existente) |
| **ApprovalCenter** | Aprovação humana | `src/approval_center/` | — (existente) |

**Princípio:** MissionPackageBuilder é o MAESTRO. P10 é a ORQUESTRA. O maestro rege, não toca os instrumentos.

---

## 8. Critérios de Aceite (10)

| # | Critério | Como verificar |
|---|----------|---------------|
| 1 | `from_mission_plan()` extrai account_handle, intent, steps do MissionPlan | Teste: `builder.from_mission_plan(plan).work_orders` não vazio |
| 2 | `build(dry_run=True)` chama `orchestrate()` para cada WO sem escrever approvals | Teste: `package.output_packages` populado, `approval_requests` vazio |
| 3 | `build(dry_run=False)` gera outputs + registra + submete approval | Teste: `package.approval_requests` populado, arquivos existem em disco |
| 4 | `validate()` agrega checks de todas as WOs e retorna `overall_valid` | Teste: 2 WOs válidas + 1 inválida → `overall_valid=False` |
| 5 | `submit_for_approval(dry_run=True)` não cria ApprovalRequest real | Teste: `submissions[0].approval_request` é None |
| 6 | `closeout()` compila total_outputs, total_files, duration, status | Teste: campos presentes, tipos corretos |
| 7 | `save()` + `load()` roundtrip preserva todos os campos | Teste: `assert saved.to_dict() == loaded.to_dict()` |
| 8 | Nenhum import de `src/output_generator/` interno (só API pública) | Review: imports só de `__init__.py` exports |
| 9 | Schema do `mission_package.json` é validável (todos os campos obrigatórios presentes) | Teste: `assert all(k in package.to_dict() for k in REQUIRED_FIELDS)` |
| 10 | Regressão total permanece 2205+ (testes P10 não quebram) | Comando: `pytest tests/ -q --tb=short` |

---

## 9. Testes Planejados (8+ para P11)

| # | Teste | Classe | O que cobre |
|---|-------|--------|-------------|
| 1 | `test_from_mission_plan_creates_work_orders` | Unit | Critério 1 |
| 2 | `test_build_dry_run_populates_output_packages` | Unit | Critério 2 |
| 3 | `test_build_live_generates_approval_requests` | Unit | Critério 3 |
| 4 | `test_validate_aggregates_all_wos` | Unit | Critério 4 |
| 5 | `test_submit_approval_dry_run_no_side_effects` | Unit | Critério 5 |
| 6 | `test_closeout_compiles_metrics` | Unit | Critério 6 |
| 7 | `test_save_load_roundtrip` | Integration | Critério 7 |
| 8 | `test_full_mission_e2e` | E2E | Critérios 1-7 integrados |
| 9 | `test_regression_output_generator_untouched` | Regression | Critério 10 |

---

## 10. Restrições Técnicas

1. **Zero alteração em `src/output_generator/`.** O módulo está selado.
2. **Apenas stdlib + dependências existentes.** Nenhum pip install novo.
3. **Dataclass, não Pydantic.** Seguir padrão do P10 (`from dataclasses import dataclass`).
4. **JSONL append-only.** Seguir padrão do `ManifestRegistry`.
5. **Dry-run por default.** Todos os métodos que geram side effects usam `dry_run=True` como padrão.
6. **Typer CLI.** Comandos expostos via `src/cli_commands/`.
7. **Zero LLM, zero rede.** Constraint do trem blindado.
8. **Testes com `tmp_path`.** Sem dependência de diretórios reais.

---

## 11. Diagrama de Sequência — Missão Completa

```
Usuário (Lucas)
  │
  │  "cria 5 carrosséis sobre Natal/RN para @lucastigrereal"
  │
  ▼
MissionBuilder.build_plan()        [P2 — existente]
  │
  │  → MissionPlan (intent=carousel, account=lucastigrereal, slots=5)
  │
  ▼
MissionPackageBuilder.from_mission_plan(plan)   [P11 — NOVO]
  │
  │  → MissionPackage (context + 5 WorkOrders rascunho)
  │
  ▼
MissionPackageBuilder.build(package, dry_run=True)   [P11 — NOVO]
  │
  ├─► P10.OutputWriterService.orchestrate("wo_01")  [P10 — SELADO]
  ├─► P10.OutputWriterService.orchestrate("wo_02")  [P10 — SELADO]
  ├─► P10.OutputWriterService.orchestrate("wo_03")  [P10 — SELADO]
  ├─► P10.OutputWriterService.orchestrate("wo_04")  [P10 — SELADO]
  └─► P10.OutputWriterService.orchestrate("wo_05")  [P10 — SELADO]
  │
  │  → MissionPackage.output_packages populado (5 resultados)
  │
  ▼
MissionPackageBuilder.validate(package)   [P11 — NOVO]
  │
  │  → overall_valid = True (todos os 5 pacotes passaram)
  │
  ▼
MissionPackageBuilder.submit_for_approval(package, dry_run=False)   [P11 — NOVO]
  │
  ├─► P10.prepare_submission("wo_01", dry_run=False)  [P10 — SELADO]
  │     └─► approval_center.request_approval()        [P4 — existente]
  ├─► ... (wo_02..wo_05)
  │
  │  → MissionPackage.approval_requests populado (5 pending)
  │
  ▼
MissionPackageBuilder.closeout(package)   [P11 — NOVO]
  │
  │  → Relatório: 5 WOs, 20 outputs, 5 approvals, status=done
  │
  ▼
MissionPackageBuilder.save(package)   [P11 — NOVO]
  │
  │  → exports/mission_packages/mb_abc123/mission_package.json
  │
  ▼
✅ Missão completa. Pacote salvo. Aguardando aprovação humana.
```

---

## 12. Próximo Passo

```
ESPECIFICAÇÃO CONCLUÍDA. Aguardando aprovação do Lucas.
```

Após aprovação desta spec: **P11 — Mission Package Builder** (código).

---

**Fim da Spec. Nenhum código foi gerado.**

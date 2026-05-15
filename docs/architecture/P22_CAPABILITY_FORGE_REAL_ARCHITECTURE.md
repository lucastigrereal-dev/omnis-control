# P22 — CAPABILITY FORGE REAL ARCHITECTURE

> **Data:** 2026-05-13
> **Status:** DRAFT — Aguardando revisão
> **Base:** master `ada6373` (P20 fechado, P21 arquitetado)
> **Pré-requisito:** P21 Memory Intelligence (fornece histórico de gaps)

---

## 1. DEFINIÇÃO

P22 Capability Forge Real é a **fábrica de código** que transforma gaps de capability detectados em missões em skills funcionais registradas no sistema. Diferente do `capability_forge_lite` (que só gera specs em markdown e registra como `status: "planned"`), a P22 **gera código real**: source files, test files, CLI registrations, e ativa capabilities com `status: "active"`.

Ela desbloqueia o `build_skill()` que está como `NotImplementedError` desde a Fase 4.

---

## 2. PROBLEMA QUE RESOLVE

**Atual:** Quando uma missão Supreme falha por falta de capability, o sistema só gera um warning e specs markdown. O operador precisa implementar manualmente cada skill nova.

**Com P22:** Gaps detectados → proposals aprovadas → código gerado automaticamente → testado → registrado como `active`. O ciclo "detectar falta → criar capability" fecha sem intervenção manual de código.

---

## 3. O QUE FAZ

1. **Gap Detection** — hook no P20: quando uma missão não encontra módulos para um intent, detecta o gap
2. **Proposal Generation** — reusa `capability_forge_lite.proposal.propose_from_gap()`
3. **Approval Bridge** — reusa `capability_forge_lite.approval_bridge` (P18 governance)
4. **Code Generation (build)** — **NOVO**: gera `src/skills/<name>/run.py`, `test_run.py`, registra no CLI
5. **Policy Scan** — reusa `capabilityforge.policy.PolicyEngine` no código gerado
6. **Test Generation** — gera teste mínimo (≥3 testes) para cada skill
7. **Registration** — reusa `capability_forge_lite.registrar.register_capability()` com `status: "active"`
8. **Dry-run** — toda geração de código é dry-run por default (arquivos não são escritos em disco)
9. **Rollback** — se policy scan falhar, código gerado é descartado

---

## 4. O QUE NÃO FAZ

| PROIBIDO | Motivo |
|---|---|
| Criar skills com lógica de negócio complexa | Forge gera scaffold/template. Lógica é preenchida depois |
| Gerar código que acessa rede/OAuth | Policy engine bloqueia imports de rede |
| Substituir o operador na decisão de criar skills | Approval gate é obrigatório |
| Modificar módulos existentes (P1-P21) | Forge só cria em `src/skills/` |
| Criar skills sem aprovação | `approval_required=True` inegociável |
| Gerar código sem testes | Mínimo 3 testes por skill |
| Implementar LLM para gerar código | Templates determinísticos, sem API calls |
| Reescrever capability_forge_lite | P22 estende, não reescreve |

---

## 5. RELAÇÃO COM P20

P22 é chamado pelo P20 no estágio de **planejamento**, quando um intent não encontra pipeline:

```python
# Em SupremePlanner.plan():
if not pipeline:
    gap = detect_capability_gap(mission.intent, mission.sector)
    mission.warnings.append(f"Capability gap: {gap.description}")
    
    # Se P22 estiver disponível:
    if gap.status == GAP_STATUS_OPEN:
        proposal = propose_from_gap(gap.gap_id)
        mission.metadata["pending_proposal_id"] = proposal.proposal_id
```

E no pós-missão, se o operador aprovou a proposal:

```python
# Em SupremeOrchestrator.run() — após approval:
if mission.metadata.get("pending_proposal_id"):
    proposal = get_approved_proposal(mission.metadata["pending_proposal_id"])
    if proposal and proposal.status == APPROVED:
        build_result = build_skill(proposal, dry_run=mission.dry_run)
        mission.metadata["built_skill"] = build_result
```

---

## 6. RELAÇÃO COM MÓDULOS EXISTENTES

| Módulo | Como P22 usa |
|---|---|
| `capability_forge_lite` | **Base.** Reusa: models, proposal, store, spec_exporter, approval_bridge, registrar, spec_validator |
| `capabilityforge` (v1) | Reusa apenas `policy.py` (PolicyEngine) para scan de segurança |
| `capability_gap` | Reusa detector e store para identificar gaps |
| P18 `governance` | Approval gate para toda proposal e build |
| P16 `observability_local` | TraceEvent para cada build |
| P21 `memory_intel` | Histórico de gaps resolvidos, padrões de sucesso/fracasso |

| Módulo | P22 NÃO importa |
|---|---|
| P1-P15, P17, P19, P20 | Domínios de negócio |

---

## 7. CONTRATOS PRINCIPAIS

### 7.1 BuildResult

```python
@dataclass
class BuildResult:
    build_id: str              # "bld_<8hex>"
    proposal_id: str
    capability_name: str
    implementation_type: str
    files_created: list[str]   # paths relativos
    test_count: int
    policy_scan: dict          # {"passed": bool, "violations": [...]}
    status: str                # "built" | "policy_failed" | "test_failed" | "registered"
    dry_run: bool
    generated_at: str
```

### 7.2 Skill Scaffold Template

```python
SKILL_TEMPLATE = '''"""{{capability_name}} — {{description}}."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class {{class_name}}Input:
    """Input para {{capability_name}}."""
    request: str
    dry_run: bool = True

    def to_dict(self) -> dict:
        return {"request": self.request, "dry_run": self.dry_run}


@dataclass
class {{class_name}}Output:
    """Output de {{capability_name}}."""
    result: dict
    status: str = "ok"
    generated_at: str = None

    def to_dict(self) -> dict:
        return {"result": self.result, "status": self.status, "generated_at": self.generated_at}


def run(input_data: dict) -> dict:
    """Executa {{capability_name}}."""
    inp = {{class_name}}Input(**input_data)
    # TODO: implementar lógica real
    output = {{class_name}}Output(
        result={"message": f"{{capability_name}} stub: {inp.request}"},
        generated_at=_now_iso(),
    )
    return output.to_dict()
'''
```

---

## 8. STATE / FLOW

```python
class BuildState(str, Enum):
    PROPOSAL_APPROVED = "proposal_approved"   # entrada: proposal aprovada
    SCAFFOLDING = "scaffolding"               # gerando arquivos
    POLICY_SCANNING = "policy_scanning"       # scan de segurança
    TEST_GENERATING = "test_generating"       # gerando testes
    VALIDATING = "validating"                 # rodando testes
    REGISTERING = "registering"              # registrando como active
    DONE = "done"                             # terminal: capability ativa
    POLICY_FAILED = "policy_failed"           # terminal: violação de segurança
    TEST_FAILED = "test_failed"               # terminal: testes não passam
```

### Transições

```
PROPOSAL_APPROVED → SCAFFOLDING → POLICY_SCANNING → TEST_GENERATING → VALIDATING → REGISTERING → DONE
                                         ↘ POLICY_FAILED
                                                          ↘ TEST_FAILED
```

---

## 9. ARQUIVOS SUGERIDOS

```
src/capability_forge_real/          # P22 namespace
├── __init__.py
├── models.py                       # BuildResult, BuildState, SkillTemplate
├── builder.py                      # build_skill() — gera código
├── scaffold.py                     # Templates por implementation_type
├── policy_scanner.py               # wrapper do PolicyEngine v1
├── test_generator.py               # gera test_run.py (≥3 testes)
├── errors.py                       # BuildError, ScaffoldError, PolicyScanError, TestGenError
└── cli.py                          # forge-real build, forge-real status

tests/capability_forge_real/
├── __init__.py
├── test_models.py                  # 15+ testes
├── test_builder.py                 # 20+ testes (build_skill com todos os tipos)
├── test_scaffold.py                # 10+ testes (templates, variáveis)
├── test_policy_scanner.py          # 10+ testes
├── test_test_generator.py          # 10+ testes
└── test_e2e_forge.py               # 10+ testes (gap → proposal → build → register)

docs/capability_forge_real/
└── P22_CAPABILITY_FORGE_REAL_SKELETON.md
```

**Total: 8 source + 5 test + 1 doc = 14 arquivos**

---

## 10. CLASSES SUGERIDAS

### builder.py

```python
class CapabilityBuilder:
    """Gera código para uma capability aprovada."""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.scanner = PolicyScanner()

    def build(self, proposal: CapabilityProposal) -> BuildResult:
        """Pipeline completo: scaffold → scan → test → validate → register."""

    def scaffold(self, proposal: CapabilityProposal) -> list[str]:
        """Gera arquivos fonte baseado no implementation_type."""

    def scan(self, files: list[str]) -> dict:
        """Policy scan nos arquivos gerados."""

    def generate_tests(self, proposal: CapabilityProposal) -> str:
        """Gera test_run.py com ≥3 testes."""

    def validate(self, test_file: str) -> bool:
        """Roda pytest no teste gerado."""

    def register(self, proposal: CapabilityProposal) -> bool:
        """Registra como active no capabilities.yaml."""

    def rollback(self, build_id: str) -> None:
        """Remove arquivos gerados em caso de falha."""
```

### scaffold.py

```python
# Templates por implementation_type
TEMPLATES = {
    "cli_wrapper": CLI_WRAPPER_TEMPLATE,       # src/skills/<name>/run.py
    "offline_package": OFFLINE_PACKAGE_TEMPLATE, # src/offline_factory/<name>/
    "manual_process": MANUAL_PROCESS_TEMPLATE,   # SOP markdown
    "external_future": EXTERNAL_FUTURE_TEMPLATE,  # stub + nota
    "app_factory_future": APP_FACTORY_TEMPLATE,   # PRD spec
}
```

---

## 11. CLI COMMANDS SUGERIDOS

```python
@forge_real.command()
@click.argument("proposal_id")
@click.option("--dry-run/--no-dry-run", default=True)
def build(proposal_id: str, dry_run: bool):
    """Gera código para uma proposal aprovada."""

@forge_real.command()
@click.argument("build_id")
def status(build_id: str):
    """Verifica status de um build."""

@forge_real.command()
@click.argument("build_id")
def rollback(build_id: str):
    """Remove arquivos de um build com falha."""
```

---

## 12. TEST STRATEGY

### Meta: ≥ 75 testes

| Arquivo | Testes | Foco |
|---|---|---|
| `test_models.py` | 15+ | BuildResult.new(), to_dict/from_dict, BuildState transições válidas/inválidas |
| `test_builder.py` | 20+ | build() com cada implementation_type, dry_run não escreve em disco, rollback remove arquivos |
| `test_scaffold.py` | 10+ | Templates renderizam corretamente, variáveis substituídas, arquivos criados nos paths corretos |
| `test_policy_scanner.py` | 10+ | Código limpo passa, código com imports proibidos falha, regex/AST scan |
| `test_test_generator.py` | 10+ | Teste gerado tem ≥3 funções, teste roda e passa, teste captura erros |
| `test_e2e_forge.py` | 10+ | gap → proposal → approval → build → register round-trip |

---

## 13. DRY-RUN STRATEGY

```python
class CapabilityBuilder:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def scaffold(self, proposal: CapabilityProposal) -> list[str]:
        files = self._generate_file_paths(proposal)
        if not self.dry_run:
            for path, content in files:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
        else:
            # Apenas simula: retorna paths, não escreve nada
            pass
        return [str(p) for p, _ in files]
```

---

## 14. FAILURE / RECOVERY

| Falha | Recovery |
|---|---|
| Scaffold gera arquivo em path já existente | `ScaffoldError` → aborta, sugere renomear capability |
| Policy scan encontra violação | `PolicyScanError` → build.state = POLICY_FAILED, lista violações |
| Teste gerado não passa | `TestGenError` → build.state = TEST_FAILED, mostra output do pytest |
| Registro falha (duplicata) | `DuplicateCapabilityError` → build.state = DONE mas registro = skipped |
| Rollback falha (arquivos já deletados) | Warning, sem erro |

---

## 15. RISCOS ARQUITETURAIS

| # | Risco | Impacto | Prob | Mitigação |
|---|---|---|---|---|
| R1 | Templates gerarem código de baixa qualidade | Médio — skills inúteis | Média | Templates são scaffolds mínimos. Qualidade vem do preenchimento manual |
| R2 | Forge gerar skills que colidem com módulos existentes | Alto — conflito de nomes | Baixa | Registry lookup antes de gerar. Prefixo `skill_` para skills dinâmicas |
| R3 | Policy scanner falso-positivo bloquear skills legítimas | Baixo — frustração | Média | Scanner é configurável. Violações são warnings, não erros (exceto rede/OAuth) |
| R4 | Build automático sem review gerar código inseguro | Crítico — segurança | Baixa | Policy scan + approval gate + dry_run default |
| R5 | `capability_forge_lite` e `capability_forge_real` divergirem | Médio — manutenção dupla | Média | P22 estende, não duplica. Idealmente deprecar capability_forge_lite após P22 |

---

## 16. ANTI-PATTERNS PROIBIDOS

```
✗ GERAR CÓDIGO SEM POLICY SCAN — build sem scan de segurança
✗ PULAR APPROVAL GATE — approval_required=False em builds
✗ CÓDIGO GERADO COM IMPORTS DE REDE — requests, httpx, socket, urllib
✗ SOBRESCREVER MÓDULOS EXISTENTES — forge só escreve em src/skills/
✗ BUILD SEM TESTES — mínimo 3 testes por skill
✗ GERAR LÓGICA DE NEGÓCIO — templates são scaffolds, não implementações
✗ IGNORAR DRY_RUN — dry_run=True bloqueia escrita em disco
```

---

## 17. CRITÉRIOS DE ACEITE

- [ ] Namespace `src/capability_forge_real/` com 8 arquivos
- [ ] Testes ≥ 75 (targeted), todos passando
- [ ] `build_skill()` funcional para 5 implementation_types
- [ ] Policy scan integrado no pipeline de build
- [ ] Test generation (≥3 testes por skill)
- [ ] Registro como `status: "active"` no capabilities.yaml
- [ ] Rollback funcional
- [ ] dry_run=True default (não escreve em disco)
- [ ] approval_required=True em todas as operações
- [ ] Zero imports de rede/OAuth
- [ ] Zero toques em módulos existentes
- [ ] Full suite sem regressões

---

## 18. ORDEM INCREMENTAL

### M1: Models + Errors
- `models.py`, `errors.py`
- `test_models.py` — 15+ testes

### M2: Scaffold + Templates
- `scaffold.py` — 5 templates
- `test_scaffold.py` — 10+ testes

### M3: Builder Core
- `builder.py` — build(), scaffold(), register(), rollback()
- `test_builder.py` — 20+ testes (com mock de escrita)

### M4: Policy Scanner + Test Generator
- `policy_scanner.py` — wrapper PolicyEngine
- `test_generator.py` — gera test_run.py
- `test_policy_scanner.py` + `test_test_generator.py` — 20+ testes

### M5: CLI + E2E + Docs
- `cli.py` — build, status, rollback
- `test_e2e_forge.py` — 10+ testes
- `__init__.py` — exports
- Skeleton doc
- Full suite validation

---

## 19. RECOMENDAÇÃO DE PARALELIZAÇÃO

**1 frente única.** P22 é sequencial: models → scaffold → builder → scanner → tests → CLI. Cada milestone consome o anterior.

---

*OMNIS Control Tower — P22 Capability Forge Real Architecture.*

# P26 — APP FACTORY SUPREME ARCHITECTURE

> **Data:** 2026-05-14
> **Status:** ARCHITECTURE DRAFT — Aguardando revisão
> **Base:** master pós-P24 (4604 testes, 0 regressões)
> **Pré-requisitos:** P25 Multi-Model + P22 Capability Forge + P23 Autonomous + P18 Governance

---

## 1. DEFINIÇÃO

P26 App Factory Supreme transforma ideias de aplicação em **aplicações completas e funcionais** seguindo um pipeline determinístico com gates de qualidade e governança. Ele estende o `src/app_factory/` existente (que tem models e planner skeleton) adicionando: geração real de código via P22, validação estrutural, scaffold executável, e entrega empacotada.

Diferente de ferramentas "vibe-coding" (Lovable, v0, Bolt), o App Factory Supreme **não gera código cego**. Cada etapa tem contratos, validações, e gates de aprovação.

---

## 2. PROBLEMA QUE RESOLVE

**Atual:** O `src/app_factory/` existe com models (AppIdea, AppRequirement, AppBlueprint, AppArtifact) e um planner determinístico, mas:
1. Não gera código executável — só produz PRD e estrutura
2. Não tem validação de qualidade do código gerado
3. Não tem rollback se a geração falhar
4. Não tem integração com o resto do OMNIS

**Com P26:** Ideia → PRD → Blueprint → Código → Testes → App Rodando. Tudo com gates.

---

## 3. O QUE FAZ

1. **Idea Intake** — recebe AppIdea (reaproveita models existentes)
2. **Requirement Extraction** — AppRequirement.from_idea() (já existe)
3. **Blueprint Design** — AppBlueprint.from_requirement() (já existe, será expandido)
4. **Code Generation** — usa P22 CapabilityForge para gerar código real de cada módulo
5. **Scaffold Assembly** — monta estrutura de diretórios e arquivos
6. **Test Generation** — gera testes para cada módulo (P22 test_generator)
7. **Policy Scan** — valida código gerado contra regras de segurança (P22 policy_scanner)
8. **Build Verification** — compila/roda testes do app gerado
9. **Packaging** — empacota app como diretório pronto ou Dockerfile
10. **Rollback** — desfaz geração se falhar em qualquer etapa

---

## 4. O QUE NÃO FAZ

| PROIBIDO | Motivo |
|---|---|
| Gerar app sem validação humana | Todo blueprint passa por approval gate |
| Ser um "Lovable" ou "v0" clone | P26 é pipeline estruturado, não chat→preview |
| Deploy automático sem approval | P26 gera código. Deploy é P27 (Real World Actions) |
| Modificar código existente do OMNIS | Apps gerados vão para diretório isolado |
| Criar apps que acessam APIs externas sem declaração | Toda dependência externa é declarada no blueprint |
| Substituir o P22 Forge | P26 USA o P22, não duplica |
| Gerar apps com UI complexa sem design system | v1 foca em API/CLI apps. Web é limitado a templates |

---

## 5. RELAÇÃO COM P20 SUPREME

P26 é invocado como **skill do P20**:

```python
# P20 adapters.py — nova entry:
("P26", "build_app"): lambda c, x: AppFactorySupreme(dry_run=c.get("dry_run", True))
    .build(AppIdea.from_dict(c["idea"]))
    .to_dict()
```

O P20 orquestra o fluxo: recebe ideia → classifica intenção "build_app" → delega ao P26.

---

## 6. RELAÇÃO COM P21 MEMORY

P21 fornece **contexto histórico de apps similares**:

- "App tipo CRUD com auth: 3 apps similares gerados, 2 com sucesso"
- "Tech stack React+FastAPI teve 100% sucesso em 5 builds"
- "App com entidade 'payment' requer revisão extra de segurança"

Isso evita repetir erros e acelera o planejamento.

---

## 7. RELAÇÃO COM P22 FORGE

P26 é o **consumidor principal do P22**:

| Etapa P26 | Usa P22 |
|---|---|
| Code Generation | `CapabilityBuilder.build()` para cada módulo |
| Scaffold Assembly | `render_template()` para estrutura de diretórios |
| Test Generation | `generate_test_content()` para cada módulo |
| Policy Scan | `scan_code()` para validar segurança |
| Rollback | `CapabilityBuilder.rollback()` se build falhar |

P22 gera. P26 orquestra a geração em escala de app completo.

---

## 8. RELAÇÃO COM P23 AUTONOMOUS EXECUTION

P26 pode ser executado como **missão autônoma do P23**:

```yaml
mission:
  intent: build_app
  steps:
    - validate_idea        # checkpoint: approval
    - extract_requirements # automático
    - design_blueprint     # checkpoint: review blueprint
    - generate_code        # automático (usa P22)
    - run_tests            # automático
    - policy_scan          # checkpoint: security review
    - package              # automático
```

Cada etapa de checkpoint para e pede aprovação humana. O resto roda autônomo.

---

## 9. RELAÇÃO COM P24 LIVE COCKPIT

P24 mostra:

- **Apps em construção** — pipeline status de cada build
- **Builds concluídos hoje** — com status pass/fail
- **Gaps detectados** — módulos que o P22 não conseguiu gerar
- **Tempo médio de build** — métrica de eficiência

---

## 10. CONTRATOS PRINCIPAIS

### 10.1 AppBuild (NOVO — estende o app_factory existente)

```python
@dataclass
class AppBuild:
    build_id: str              # "apb_<8hex>"
    artifact_id: str           # referencia AppArtifact
    blueprint_id: str          # referencia AppBlueprint
    status: str                # "planned" | "building" | "testing" | "packaged" | "failed"
    modules: list[ModuleBuild] # resultado de cada módulo
    test_results: dict         # {total, passed, failed, skipped}
    policy_violations: list[dict]
    output_dir: str            # diretório onde app foi gerado
    errors: list[str]
    started_at: str
    completed_at: str

    @classmethod
    def from_blueprint(cls, blueprint: AppBlueprint) -> "AppBuild": ...

    @property
    def is_success(self) -> bool: ...
    @property
    def overall_pass_rate(self) -> float: ...
```

### 10.2 ModuleBuild

```python
@dataclass
class ModuleBuild:
    module_name: str           # "auth", "core", "web", etc.
    files_generated: list[str] # paths dos arquivos gerados
    build_result: BuildResult  # resultado do P22 CapabilityBuilder
    tests_pass: bool
    policy_scan_pass: bool
    errors: list[str]
```

### 10.3 BuildPipeline (orquestrador)

```python
class BuildPipeline:
    """Pipeline completo: Idea → Code → Tests → Package."""

    def __init__(self, dry_run: bool = True): ...
    def build(self, idea: AppIdea) -> AppBuild: ...
    def validate_idea(self, idea: AppIdea) -> bool: ...
    def generate_module(self, blueprint: AppBlueprint, module: dict) -> ModuleBuild: ...
    def assemble(self, build: AppBuild) -> AppBuild: ...
    def verify(self, build: AppBuild) -> AppBuild: ...
    def rollback(self, build_id: str) -> bool: ...
```

---

## 11. STATE / FLOW

```
┌──────────────────────────────────────────────────────────────────┐
│                    P26 APP FACTORY PIPELINE                       │
│                                                                   │
│  [User] "cria app de gestão de conteúdo"                         │
│     │                                                             │
│  ┌──▼──────────────────────────────────────────────────────────┐ │
│  │ 1. INTAKE                                                     │ │
│  │    AppIdea.new(title, description) → validate()              │ │
│  │    Gate: idea.is_valid? ── Não → InvalidAppIdeaError         │ │
│  └──────────────────────────────────────────────────────────────┘ │
│     │                                                             │
│  ┌──▼──────────────────────────────────────────────────────────┐ │
│  │ 2. REQUIREMENTS                                               │ │
│  │    AppRequirement.from_idea(idea) → func/non-func/entities   │ │
│  │    [deterministico, existe em app_factory/models.py]         │ │
│  └──────────────────────────────────────────────────────────────┘ │
│     │                                                             │
│  ┌──▼──────────────────────────────────────────────────────────┐ │
│  │ 3. BLUEPRINT ◀── APPROVAL GATE (P18)                         │ │
│  │    AppBlueprint.from_requirement(req) → módulos, tech stack  │ │
│  │    Gate: blueprint aprovado? ── Não → ApprovalDeniedError    │ │
│  └──────────────────────────────────────────────────────────────┘ │
│     │                                                             │
│  ┌──▼──────────────────────────────────────────────────────────┐ │
│  │ 4. CODE GENERATION (P22 Forge)                                │ │
│  │    for module in blueprint.modules:                           │ │
│  │        build_result = CapabilityBuilder.build(proposal)       │ │
│  │    Gate: todos módulos gerados sem erro?                      │ │
│  └──────────────────────────────────────────────────────────────┘ │
│     │                                                             │
│  ┌──▼──────────────────────────────────────────────────────────┐ │
│  │ 5. TEST GENERATION + VERIFICATION                             │ │
│  │    for module in build.modules:                               │ │
│  │        tests = generate_test_content(module)                  │ │
│  │        result = run_tests(module)                             │ │
│  │    Gate: test_pass_rate >= 80%?                               │ │
│  └──────────────────────────────────────────────────────────────┘ │
│     │                                                             │
│  ┌──▼──────────────────────────────────────────────────────────┐ │
│  │ 6. POLICY SCAN ◀── SECURITY GATE                              │ │
│  │    scan_code(output_dir) → violations                         │ │
│  │    Gate: zero critical/high violations?                       │ │
│  └──────────────────────────────────────────────────────────────┘ │
│     │                                                             │
│  ┌──▼──────────────────────────────────────────────────────────┐ │
│  │ 7. PACKAGE                                                    │ │
│  │    AppArtifact.from_blueprint(blueprint, prd, structure)     │ │
│  │    → output_dir/ com estrutura completa + README             │ │
│  └──────────────────────────────────────────────────────────────┘ │
│     │                                                             │
│     ▼                                                             │
│  [AppBuild] status="packaged" → pronto para uso                   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 12. ARQUIVOS SUGERIDOS

```
src/app_factory/                        # DIRETÓRIO EXISTENTE — SERÁ EXPANDIDO
├── __init__.py                         # Atualizar exports (BuildPipeline, AppBuild, etc.)
├── models.py                           # EXISTENTE — adicionar AppBuild, ModuleBuild, BuildStatus
├── errors.py                           # EXISTENTE — adicionar BuildError, VerificationError, PackageError
├── planner.py                          # EXISTENTE — renomear/estender: AppFactoryPlanner → BuildPlanner
├── prd_generator.py                    # EXISTENTE — manter
├── structure_generator.py              # EXISTENTE — manter
├── pipeline.py                         # NOVO — BuildPipeline (orquestrador principal)
├── code_generator.py                   # NOVO — bridge para P22 CapabilityBuilder
├── verifier.py                         # NOVO — BuildVerifier (roda testes, policy scan)
├── packager.py                         # NOVO — AppPackager (empacota app final)
└── cli.py                              # NOVO — CLI: app-factory build, status, list, rollback

tests/app_factory/
├── test_models.py                      # Expandir — +10 testes para AppBuild, ModuleBuild
├── test_pipeline.py                    # NOVO — 15+ testes
├── test_code_generator.py              # NOVO — 12+ testes (bridge P22)
├── test_verifier.py                    # NOVO — 12+ testes
├── test_packager.py                    # NOVO — 10+ testes
├── test_cli.py                         # NOVO — 10+ testes
└── test_e2e_app_factory.py             # NOVO — 12+ testes

docs/app_factory/
└── P26_APP_FACTORY_SUPREME_ARCHITECTURE.md
```

**Total: 4 novos arquivos source + 6 novos test files + 1 doc = 11 novos arquivos**
**(Reaproveita 6 arquivos existentes do src/app_factory/)**

---

## 13. CLASSES SUGERIDAS

```python
class BuildPipeline:
    """Orquestrador principal do App Factory Supreme."""
    def __init__(self, dry_run: bool = True, output_base: Path = ...): ...
    def build(self, idea: AppIdea) -> AppBuild: ...
    def validate_idea(self, idea: AppIdea) -> list[str]: ...
    def plan_build(self, idea: AppIdea) -> AppBlueprint: ...
    def generate_code(self, blueprint: AppBlueprint) -> list[ModuleBuild]: ...
    def verify_build(self, build: AppBuild) -> AppBuild: ...
    def package(self, build: AppBuild) -> AppBuild: ...
    def rollback(self, build_id: str) -> bool: ...

class CodeGenerator:
    """Bridge entre P26 e P22 CapabilityForge."""
    def __init__(self, forge_builder: CapabilityBuilder): ...
    def generate_module(self, module_spec: dict) -> BuildResult: ...
    def generate_tests(self, module_spec: dict, code: str) -> str: ...
    def scan_policy(self, code: str) -> list[dict]: ...

class BuildVerifier:
    """Verifica qualidade do build: testes, policy scan, estrutura."""
    def verify(self, build: AppBuild) -> BuildVerifier: ...
    def run_tests(self, module: ModuleBuild) -> dict: ...
    def check_structure(self, output_dir: Path) -> list[str]: ...
    def scan_security(self, output_dir: Path) -> list[dict]: ...

class AppPackager:
    """Empacota app final com README, requirements, Dockerfile."""
    def package(self, build: AppBuild) -> Path: ...
    def generate_readme(self, build: AppBuild) -> str: ...
    def generate_dockerfile(self, build: AppBuild) -> str: ...
```

---

## 14. CLI COMMANDS SUGERIDOS

```
app-factory build <title> [--description "..."] [--features "..."]   # Pipeline completo
app-factory plan <title> [--description "..."]                       # Só planejamento (PRD + Blueprint)
app-factory status <build_id>                                        # Status de um build
app-factory list [--status packaged|failed|building]                 # Lista builds
app-factory rollback <build_id>                                      # Desfaz build
app-factory export <build_id> [--format zip|dir] [-o path]           # Exporta app gerado
```

---

## 15. TEST STRATEGY

| Arquivo | Testes | Foco |
|---|---|---|
| `test_models.py` (expandir) | +10 | AppBuild.new(), ModuleBuild, status transitions |
| `test_pipeline.py` | 15+ | Pipeline completo dry-run. Cada etapa isolada. Rollback |
| `test_code_generator.py` | 12+ | Bridge P22: gerar módulo, gerar testes, scan policy |
| `test_verifier.py` | 12+ | Verificação de estrutura, testes passam, security scan |
| `test_packager.py` | 10+ | README gerado, estrutura de diretórios correta |
| `test_cli.py` | 10+ | Comandos CLI funcionam, flags de dry-run |
| `test_e2e_app_factory.py` | 12+ | Ideia → AppBuild completo. Dry-run + real (com mock P22) |

**Meta: ≥ 80 testes novos** (somados aos existentes do app_factory)

---

## 16. DRY-RUN STRATEGY

```python
class BuildPipeline:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def build(self, idea: AppIdea) -> AppBuild:
        if self.dry_run:
            # Planeja tudo, mas não escreve arquivos em disco
            blueprint = self.plan_build(idea)
            return AppBuild(
                status="planned",
                blueprint_id=blueprint.blueprint_id,
                modules=[],
                output_dir=str(self.output_base / "dry_run" / idea.idea_id),
            )
        # Execução real: gera código, escreve em disco, verifica
```

Dry-run = planeja blueprint, estima módulos, NÃO escreve código.

---

## 17. APPROVAL STRATEGY

3 gates de aprovação (via P18 Governance):

| Gate | Quando | Quem aprova |
|---|---|---|
| **Blueprint Gate** | Após design do blueprint, antes de gerar código | Operador revisa tech stack, módulos |
| **Security Gate** | Após policy scan, antes de empacotar | Automático se zero violations críticas |
| **Package Gate** | Antes de exportar/mover para produção | Operador revisa build completo |

Usa `GovernanceDecision` do P18 com `action_type="deploy"` para o gate final.

---

## 18. FAILURE / RECOVERY

| Falha | Comportamento |
|---|---|
| P22 Forge falha em módulo | ModuleBuild.status="failed". Pipeline continua com módulos restantes |
| Geração de código com erro de sintaxe | Verifier detecta → rebuild automático (max 2 retries) |
| Policy scan encontra violation crítica | Build pausa. Alerta no P24. Operador revisa |
| Testes do app gerado falham | Se pass_rate < 80%, módulo marcado como "degraded" |
| Disco cheio durante geração | Pipeline aborta com erro claro. Rollback limpa diretório |
| Rollback falha | Arquivos marcados para limpeza manual. Alerta no P24 |

---

## 19. RISCOS ARQUITETURAIS

| # | Risco | Impacto | Prob | Mitigação |
|---|---|---|---|---|
| R1 | App gerado com código inseguro | Crítico | Média | Policy scan obrigatório. Security gate não-automático para critical |
| R2 | BuildPipeline virar God Class | Alto | Média | CodeGenerator, Verifier, Packager são classes separadas |
| R3 | apps gerados colidirem com módulos OMNIS | Alto | Baixa | Output isolado em `generated_apps/`. Nunca escreve em `src/` |
| R4 | Geração infinita (loop) | Médio | Baixa | Timeout global de 10min por build. Max 3 retries por módulo |
| R5 | Dependência circular entre módulos gerados | Médio | Baixa | Blueprint detection de ciclos. Topological sort antes de gerar |

---

## 20. ANTI-PATTERNS PROIBIDOS

```
✗ GERAR CÓDIGO SEM BLUEPRINT APROVADO — blueprint gate é obrigatório
✗ LOVABLE/VERCEL FAKE — não é "descreva e veja mágica". É pipeline com contratos
✗ ESCREVER EM src/ DO OMNIS — apps gerados vão para generated_apps/
✗ IGNORAR POLICY SCAN — todo build passa por scan. Violation crítica = bloqueio
✗ GERAR APP SEM TESTES — test generation é etapa obrigatória do pipeline
✗ MISTURAR P26 COM P22 — P26 orquestra, P22 gera. Responsabilidades separadas
✗ APAGAR APP EXISTENTE SEM ROLLBACK — rollback é sempre possível por 24h
```

---

## 21. CRITÉRIOS DE ACEITE

- [ ] `BuildPipeline.build()` funcional: Idea → AppBuild completo
- [ ] Integração com P22 CapabilityBuilder funcionando
- [ ] 3 approval gates funcionando (blueprint, security, package)
- [ ] Testes ≥ 80 novos, todos passando
- [ ] Rollback funcional
- [ ] dry_run=True default
- [ ] Zero toques em módulos externos (exceto P22 e P18 via contratos públicos)
- [ ] Apps gerados em diretório isolado (`generated_apps/`)
- [ ] CLI funcional com 6 comandos
- [ ] Full suite sem regressões

---

## 22. ORDEM INCREMENTAL DE IMPLEMENTAÇÃO

### M1: Expansão dos Models Existentes
- Expandir `models.py` com AppBuild, ModuleBuild, BuildStatus
- Expandir `errors.py` com BuildError, VerificationError, PackageError
- `test_models.py` — +10 testes

### M2: Code Generator Bridge (P22)
- `code_generator.py` — bridge para CapabilityBuilder
- `test_code_generator.py` — 12+ testes

### M3: Verifier + Packager
- `verifier.py` — BuildVerifier
- `packager.py` — AppPackager
- `test_verifier.py`, `test_packager.py` — 22+ testes

### M4: BuildPipeline + CLI
- `pipeline.py` — BuildPipeline
- `cli.py` — CLI commands
- `test_pipeline.py`, `test_cli.py` — 25+ testes

### M5: E2E + Docs + Integração
- `test_e2e_app_factory.py` — 12+ testes
- Atualizar `__init__.py`
- Skeleton doc + full suite validation

---

## 23. RECOMENDAÇÃO DE PARALELIZAÇÃO

**1 frente única.** O pipeline é linear: models → generator → verifier → packager → pipeline → e2e. M3 (verifier + packager) podem ser feitos em paralelo entre si, mas dependem de M2 pronto.

---

*OMNIS Control Tower — P26 App Factory Supreme Architecture.*

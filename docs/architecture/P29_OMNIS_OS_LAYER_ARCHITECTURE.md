# P29 — OMNIS OPERATING SYSTEM LAYER ARCHITECTURE

> **Data:** 2026-05-14
> **Status:** ARCHITECTURE DRAFT — Aguardando revisão
> **Base:** master pós-P24 (4604 testes, 0 regressões)
> **Pré-requisitos:** P24 Cockpit + P25 Multi-Model + P26 App Factory + P27 Actions + P28 Self-Improvement

---

## 1. DEFINIÇÃO

P29 OMNIS Operating System Layer é a camada de **consolidação arquitetural** que transforma o ecossistema OMNIS de uma coleção de 25+ módulos independentes em um **sistema operacional coeso** para operações de conteúdo. Ele define contratos universais de módulo, ciclo de vida padronizado, descoberta automática, e uma interface unificada de sistema.

Se P20 é o cérebro e P24 é o painel, P29 é o **kernel** — a camada que faz todos os módulos falarem a mesma língua.

---

## 2. PROBLEMA QUE RESOLVE

**Atual:** OMNIS tem 68 diretórios em `src/`, cada um com padrões similares mas não idênticos:
- Alguns usam `@dataclass`, outros não
- Alguns têm `.new()` factory, outros não
- Alguns têm `.to_dict()/.from_dict()`, outros não
- Alguns têm `errors.py`, outros não
- Não há descoberta automática — imports são manuais
- Não há health check padronizado — cada módulo faz diferente (ou não faz)
- Não há versão de módulo — impossível saber se um módulo é compatível

**Com P29:** Todo módulo segue o **OMNIS Module Contract**. O sistema sabe quais módulos existem, suas versões, saúde, e dependências — automaticamente.

---

## 3. O QUE FAZ

1. **Module Contract** — interface padrão que todo módulo OMNIS implementa
2. **Module Registry** — descoberta automática de módulos (scan de `src/`)
3. **Module Lifecycle** — estados padronizados: registered → active → degraded → inactive
4. **Health Protocol** — todo módulo tem `health_check()` padronizado
5. **Dependency Graph** — grafo de dependências entre módulos, com detecção de ciclos
6. **Versioning** — todo módulo declara versão e compatibilidade
7. **Event Bus** — comunicação pub/sub entre módulos (desacoplada)
8. **OS Kernel** — bootstrap, shutdown, health monitor, module loader
9. **System API** — interface unificada para consultar e gerenciar o sistema

---

## 4. O QUE NÃO FAZ

| PROIBIDO | Motivo |
|---|---|
| Reescrever módulos existentes | P29 adiciona contratos. Módulos são adaptados, não reescritos |
| Ser um service mesh ou Kubernetes | P29 é camada lógica Python, não infraestrutura |
| Substituir o P20 Supreme | P20 orquestra missões. P29 gerencia módulos |
| Forçar todos os módulos a migrar | Módulos antigos são wrapped, não quebrados |
| Ser um sistema operacional real (kernel, memória) | P29 é camada de abstração, não kernel de SO |
| Gerenciar processos do sistema | Fora do escopo. Docker e Windows gerenciam processos |

---

## 5. RELAÇÃO COM P20 SUPREME

P29 **padroniza como o P20 vê os módulos**:

```python
# Antes (P20 adapters.py):
from src.marketing.models import CampaignBrief
from src.marketing.service import MarketingPlanner
# ... import manual de cada módulo

# Depois (P29):
kernel = OmnisKernel()
marketing = kernel.get_module("marketing")
campaign_brief = marketing.call("build_campaign_brief", **params)
```

P20 para de importar módulos diretamente e passa a usar o `OmnisKernel` como barramento.

---

## 6. RELAÇÃO COM P21 MEMORY

P21 é **um módulo no registry P29**:

- `kernel.get_module("memory_intel")` → MemoryIntelligence
- P29 event bus notifica P21 quando novos aprendizados são detectados
- P21 health check reporta ao P29

---

## 7. RELAÇÃO COM P22 FORGE

P22 pode **gerar novos módulos que já nascem compatíveis com P29**:

```python
# Template de skill P22 agora inclui:
class MyNewSkill(OmnisModule):
    name = "my_new_skill"
    version = "0.1.0"
    dependencies = ["memory_intel", "omnis_supreme"]

    def health_check(self) -> ModuleHealth: ...
    def on_register(self) -> None: ...
```

P22 gera módulo. P29 registra e gerencia.

---

## 8. RELAÇÃO COM P23 AUTONOMOUS EXECUTION

P29 fornece ao P23 **visibilidade de saúde dos módulos durante execução**:

- Antes de executar step, P23 consulta P29: `kernel.is_module_healthy("publisher_argos")?`
- Se módulo está `degraded`, P23 decide: pausar, pular, ou fallback
- Event Bus notifica P23 quando um módulo volta a ficar healthy

---

## 9. RELAÇÃO COM P24 LIVE COCKPIT

P24 é **o principal consumidor do P29**:

- P24 não precisa mais de `collect_module_health()` manual com 13 imports
- P24 chama `kernel.list_modules()` → `[ModuleInfo(...), ...]`
- Health status de cada módulo vem direto do contrato P29
- P24 mostra dependency graph interativo

---

## 10. CONTRATOS PRINCIPAIS

### 10.1 OmnisModule (contrato base)

```python
class OmnisModule(ABC):
    """Contrato universal que todo módulo OMNIS deve implementar."""

    name: str                  # ex: "memory_intel"
    namespace: str             # ex: "src.memory_intel"
    version: str               # ex: "1.0.0" (semver)
    description: str           # uma linha
    dependencies: list[str]    # nomes de outros módulos

    @abstractmethod
    def health_check(self) -> ModuleHealth: ...

    @abstractmethod
    def get_exports(self) -> list[str]: ...

    def on_register(self, kernel: "OmnisKernel") -> None: ...  # hook opcional
    def on_activate(self) -> None: ...                          # hook opcional
    def on_deactivate(self) -> None: ...                        # hook opcional
```

### 10.2 ModuleHealth

```python
@dataclass
class ModuleHealth:
    module_name: str
    status: str                # "healthy" | "degraded" | "error" | "unknown"
    imports_ok: bool
    tests_passing: int
    tests_total: int
    version: str
    last_checked: str
    errors: list[str]
    warnings: list[str]

    @property
    def is_healthy(self) -> bool: ...
    @property
    def test_pass_rate(self) -> float: ...
```

### 10.3 ModuleInfo (registro)

```python
@dataclass
class ModuleInfo:
    module_id: str             # "om_<8hex>"
    name: str
    namespace: str
    version: str
    status: str                # "registered" | "active" | "degraded" | "inactive"
    dependencies: list[str]
    dependents: list[str]      # módulos que dependem deste
    health: ModuleHealth
    registered_at: str
    last_health_check: str
```

### 10.4 OmnisKernel

```python
class OmnisKernel:
    """Kernel do OMNIS OS — bootstrap, registry, event bus, lifecycle."""

    def __init__(self, dry_run: bool = True): ...
    def bootstrap(self) -> None: ...                       # descobre e registra todos os módulos
    def register(self, module: OmnisModule) -> None: ...   # registra um módulo
    def get_module(self, name: str) -> OmnisModule: ...    # busca módulo por nome
    def list_modules(self) -> list[ModuleInfo]: ...        # lista todos
    def health_check_all(self) -> list[ModuleHealth]: ...  # health check de todos
    def dependency_graph(self) -> dict: ...                # grafo de dependências
    def detect_cycles(self) -> list[list[str]]: ...        # detecta dependências circulares
    def shutdown(self) -> None: ...                        # desliga graciosamente

    # Event Bus
    def publish(self, event: str, data: dict) -> None: ...
    def subscribe(self, event: str, callback: Callable) -> None: ...
```

---

## 11. STATE / FLOW

```
┌──────────────────────────────────────────────────────────────────┐
│                    OMNIS OS BOOTSTRAP SEQUENCE                    │
│                                                                   │
│  1. OmnisKernel.__init__()                                        │
│     │                                                             │
│  2. bootstrap()                                                   │
│     │                                                             │
│     ├─→ scan src/ directory                                       │
│     │   Detecta diretórios com __init__.py                        │
│     │   Tenta importar cada um                                    │
│     │                                                             │
│     ├─→ para cada módulo detectado:                               │
│     │   ├─→ tenta instanciar OmnisModule                          │
│     │   ├─→ se implementa contrato → ModuleInfo(status=registered)│
│     │   └─→ se não → wrap como LegacyModule (status=degraded)    │
│     │                                                             │
│     ├─→ resolve dependencies                                      │
│     │   ├─→ topological sort                                      │
│     │   ├─→ detect_cycles() → reporta, não quebra                 │
│     │   └─→ activation order                                      │
│     │                                                             │
│     ├─→ activate modules (em ordem de dependência)                │
│     │   └─→ cada módulo: registered → active                      │
│     │                                                             │
│     ├─→ health_check_all()                                        │
│     │   └─→ módulos com health.check() passando → healthy         │
│     │                                                             │
│     └─→ KernelReady                                               │
│                                                                   │
│  [Runtime]                                                        │
│     ├─→ Event Bus: módulos publicam e subscrevem eventos         │
│     ├─→ Health Monitor: check periódico (a cada 60s)             │
│     └─→ Cockpit (P24): consome kernel.list_modules()             │
│                                                                   │
│  [Shutdown]                                                       │
│     └─→ kernel.shutdown() → deactivate (ordem reversa)            │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

**Módulos legados (sem contrato P29) são automaticamente wrapped como `LegacyModule` com status "degraded". Não quebram.**

---

## 12. ARQUIVOS SUGERIDOS

```
src/omnis_os/
├── __init__.py               # Exports: OmnisKernel, OmnisModule, ModuleHealth, etc.
├── models.py                 # ModuleHealth, ModuleInfo, OmnisEvent, KernelConfig
├── errors.py                 # OsError, ModuleNotFoundError, DependencyCycleError, BootstrapError
├── kernel.py                 # OmnisKernel — bootstrap, registry, lifecycle, shutdown
├── module_contract.py        # OmnisModule (ABC), ModuleContract, LEGACY_MODULE_WRAPPER
├── registry.py               # ModuleRegistry — scan, register, unregister
├── dependency.py             # DependencyGraph — resolve, detect_cycles, topological_sort
├── event_bus.py              # EventBus — pub/sub desacoplado
├── health_monitor.py         # HealthMonitor — check periódico, alertas
├── legacy_wrapper.py         # LegacyModule — wrapper para módulos sem contrato P29
└── cli.py                    # CLI: os bootstrap, os status, os modules, os health, os graph

tests/omnis_os/
├── test_models.py            # 15+ testes
├── test_kernel.py            # 15+ testes
├── test_module_contract.py   # 12+ testes
├── test_registry.py          # 12+ testes
├── test_dependency.py        # 12+ testes
├── test_event_bus.py         # 10+ testes
├── test_health_monitor.py    # 10+ testes
├── test_legacy_wrapper.py    # 10+ testes
└── test_e2e_os.py            # 12+ testes

docs/omnis_os/
└── P29_OMNIS_OS_LAYER_ARCHITECTURE.md
```

**Total: 11 source + 9 test + 1 doc = 21 arquivos**

---

## 13. CLASSES SUGERIDAS

```python
class OmnisKernel:
    """Kernel central — bootstrap, registro, ciclo de vida."""
    def __init__(self, config: KernelConfig = ..., dry_run: bool = True): ...
    def bootstrap(self) -> "BootstrapResult": ...
    def get_module(self, name: str) -> OmnisModule: ...
    def list_modules(self, status: str = None) -> list[ModuleInfo]: ...
    def health_check_all(self) -> list[ModuleHealth]: ...
    def dependency_graph(self) -> dict: ...
    def detect_cycles(self) -> list[list[str]]: ...
    def shutdown(self) -> None: ...
    @property
    def is_ready(self) -> bool: ...

class ModuleRegistry:
    """Descoberta e registro de módulos."""
    def scan(self, base_path: Path) -> list[str]: ...
    def register(self, module: OmnisModule) -> ModuleInfo: ...
    def unregister(self, name: str) -> bool: ...
    def find(self, name: str) -> ModuleInfo: ...
    def list_all(self) -> list[ModuleInfo]: ...
    def wrap_legacy(self, module_path: str) -> OmnisModule: ...

class DependencyGraph:
    """Grafo de dependências entre módulos."""
    def add_module(self, name: str, deps: list[str]) -> None: ...
    def resolve(self) -> list[str]: ...           # ordem topológica
    def detect_cycles(self) -> list[list[str]]: ... # ciclos encontrados
    def get_dependents(self, name: str) -> list[str]: ...
    def activation_order(self) -> list[str]: ...

class EventBus:
    """Barramento de eventos pub/sub."""
    def publish(self, event: str, data: dict) -> None: ...
    def subscribe(self, event: str, callback: Callable) -> None: ...
    def unsubscribe(self, event: str, callback: Callable) -> None: ...
    def list_subscribers(self, event: str) -> list[str]: ...

class HealthMonitor:
    """Monitor de saúde contínuo."""
    def __init__(self, kernel: OmnisKernel, interval_seconds: int = 60): ...
    def check_all(self) -> list[ModuleHealth]: ...
    def check_module(self, name: str) -> ModuleHealth: ...
    def start(self) -> None: ...   # inicia loop de monitoramento
    def stop(self) -> None: ...

class LegacyModule:
    """Wrapper para módulos que não implementam OmnisModule."""
    def __init__(self, namespace: str): ...
    def wrap(self) -> OmnisModule: ...  # adapta módulo antigo ao contrato
```

---

## 14. CLI COMMANDS SUGERIDOS

```
os bootstrap                            # Inicializa kernel, descobre módulos
os status                               # Status geral: módulos, saúde, eventos
os modules [--status active|degraded]   # Lista módulos registrados
os health [module_name]                 # Health check de módulo específico
os graph [--format text|json]           # Grafo de dependências
os cycles                               # Detecta dependências circulares
os events [--tail]                      # Event bus — últimos eventos
os shutdown                             # Desliga graciosamente
```

---

## 15. TEST STRATEGY

| Arquivo | Testes | Foco |
|---|---|---|
| `test_models.py` | 15+ | ModuleHealth validation, ModuleInfo registration, OmnisEvent pub/sub |
| `test_kernel.py` | 15+ | Bootstrap descobre módulos. Kernel.get_module(). Shutdown gracioso |
| `test_module_contract.py` | 12+ | OmnisModule ABC. Módulo sem health_check → erro claro. Legacy wrapper |
| `test_registry.py` | 12+ | Scan descobre diretórios. Register/unregister. Wrapping de legado |
| `test_dependency.py` | 12+ | Topological sort. Detecção de ciclos. Ordem de ativação |
| `test_event_bus.py` | 10+ | Pub/sub. Múltiplos subscribers. Unsubscribe |
| `test_health_monitor.py` | 10+ | Check periódico. Status transições: active → degraded → active |
| `test_legacy_wrapper.py` | 10+ | Módulo sem contrato → LegacyModule. Health check fallback |
| `test_e2e_os.py` | 12+ | Bootstrap full → list → health → event → shutdown |

**Meta: ≥ 108 testes**

---

## 16. DRY-RUN STRATEGY

```python
class OmnisKernel:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def bootstrap(self) -> BootstrapResult:
        if self.dry_run:
            # Scan e registro sem ativar módulos
            modules = self.registry.scan(Path("src/"))
            return BootstrapResult(
                status="dry_run",
                modules_found=len(modules),
                modules_activated=0,
                legacy_modules=[m for m in modules if self.registry.is_legacy(m)],
            )
        # Bootstrap real: ativa módulos, inicia health monitor
```

Dry-run = descobre e reporta. Não ativa, não inicia monitor, não publica eventos.

---

## 17. APPROVAL STRATEGY

P29 tem **2 ações que requerem approval** (via P18):

| Ação | Risco | Requer |
|---|---|---|
| `os shutdown` | medium | Confirmação (para evitar desligar sem querer) |
| `os unregister <module>` | high | Approval com reason obrigatório |

Bootstrap, status, health, graph — todas read-only, sem approval.

---

## 18. FAILURE / RECOVERY

| Falha | Comportamento |
|---|---|
| Módulo falha health_check | Status → "degraded". Event Bus notifica. P24 mostra alerta |
| Dependência circular detectada | Reportada, módulos marcados como "degraded". Bootstrap não quebra |
| Módulo não importável | Wrapped como LegacyModule(status="unknown"). Não bloqueia bootstrap |
| Event Bus subscriber lança exceção | Erro logado. Outros subscribers continuam. Publisher não é afetado |
| Kernel shutdown com módulo travado | Timeout 5s por módulo. Força deactivate após timeout |
| Bootstrap em disco vazio (sem src/) | `BootstrapError("no modules found")`. Kernel inicia vazio |

---

## 19. RISCOS ARQUITETURAIS

| # | Risco | Impacto | Prob | Mitigação |
|---|---|---|---|---|
| R1 | Bootstrap lento (>10s) com 68 módulos | Médio | Média | Scan lazy. Health check paralelo (ThreadPool). Timeout por módulo |
| R2 | Kernel virar God Object | Alto | Média | Kernel só coordena. Registry, Dependency, EventBus, HealthMonitor são separados |
| R3 | Quebrar módulos existentes ao adaptar | Alto | Baixa | Legacy wrapper não modifica módulo original. Só adiciona camada |
| R4 | Dependências circulares não detectadas | Médio | Baixa | detect_cycles() é obrigatório no bootstrap. Ciclos → degraded |
| R5 | Event Bus sobrecarregar em alta frequência | Baixo | Baixa | Event Bus é in-process. Sem serialização/network overhead |

---

## 20. ANTI-PATTERNS PROIBIDOS

```
✗ FORÇAR MIGRAÇÃO DE MÓDULOS ANTIGOS — LegacyModule wrapper automático
✗ KERNEL COM LÓGICA DE DOMÍNIO — kernel coordena, não executa regra de negócio
✗ QUEBRAR SE MÓDULO FALTA — bootstrap continua. Módulo ausente → unknown
✗ DEPENDÊNCIA CIRCULAR SILENCIOSA — detectada e reportada
✗ REWRITE DE 68 MÓDULOS — P29 adiciona contratos, não reescreve
✗ EVENT BUS PERSISTENTE — eventos são in-memory, não duráveis. P16/P21 armazenam estado
✗ SUBSTITUIR P24 — P29 alimenta P24 com dados padronizados
```

---

## 21. CRITÉRIOS DE ACEITE

- [ ] Namespace `src/omnis_os/` com 11 arquivos
- [ ] Testes ≥ 108 (targeted), todos passando
- [ ] `OmnisKernel.bootstrap()` descobre 68+ módulos em src/
- [ ] LegacyModule wrapper funcional — módulo antigo não quebra
- [ ] `DependencyGraph.resolve()` retorna ordem topológica
- [ ] `detect_cycles()` funcional
- [ ] `EventBus.publish/subscribe` funcional com múltiplos subscribers
- [ ] `HealthMonitor.check_all()` retorna `ModuleHealth` para cada módulo
- [ ] dry_run=True default
- [ ] Zero alterações em módulos existentes (wrapper, não rewrite)
- [ ] Full suite sem regressões

---

## 22. ORDEM INCREMENTAL DE IMPLEMENTAÇÃO

### M1: Models + Errors + Module Contract
- `models.py`, `errors.py`, `module_contract.py`
- `test_models.py`, `test_module_contract.py`

### M2: Registry + Legacy Wrapper
- `registry.py`, `legacy_wrapper.py`
- `test_registry.py`, `test_legacy_wrapper.py`

### M3: Dependency Graph
- `dependency.py`
- `test_dependency.py`

### M4: Event Bus + Health Monitor
- `event_bus.py`, `health_monitor.py`
- `test_event_bus.py`, `test_health_monitor.py`

### M5: Kernel + CLI + E2E + Docs
- `kernel.py`, `cli.py`
- `test_kernel.py`, `test_e2e_os.py`
- `__init__.py`, skeleton doc, full suite

---

## 23. RECOMENDAÇÃO DE PARALELIZAÇÃO

**1 frente única.** M1→M2→M3→M4→M5 linear. M4 (EventBus + HealthMonitor) podem ser implementados em paralelo entre si (são independentes), mas ambos dependem de M3 (DependencyGraph) para saber quais módulos monitorar.

---

*OMNIS Control Tower — P29 OMNIS OS Layer Architecture.*

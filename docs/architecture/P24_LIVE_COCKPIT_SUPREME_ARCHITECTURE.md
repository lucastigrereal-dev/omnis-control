# P24 — LIVE COCKPIT SUPREME ARCHITECTURE

> **Data:** 2026-05-13
> **Status:** DRAFT — Aguardando revisão
> **Base:** master `ada6373` (P20-P23 arquitetados)
> **Pré-requisitos:** P20 Supreme + P21 Memory Intel + P23 Autonomous Execution

---

## 1. DEFINIÇÃO

P24 Live Cockpit Supreme é o **painel de controle visual** do ecossistema OMNIS. Ele consolida informações de todos os 20+ módulos em uma interface unificada de monitoramento. Diferente de um dashboard analítico tradicional, o Cockpit é **orientado a missão**: mostra o que está acontecendo AGORA, não o que aconteceu ontem.

É o equivalente OMNIS de um cockpit de avião: instrumentos críticos, alertas visuais, e visibilidade total sem sobrecarga de informação.

---

## 2. PROBLEMA QUE RESOLVE

**Atual:** O operador precisa verificar 5-10 arquivos/serviços diferentes para entender o estado do sistema: `docker ps` para containers, `python -m pytest` para saúde de código, arquivos em `exports/` para outputs de missão, logs do P16 para tracing, etc.

**Com P24:** Uma tela. Um comando. Visibilidade total em 3 segundos.

---

## 3. O QUE FAZ

1. **Mission Overview** — missões ativas, em approval, concluídas hoje
2. **Module Health** — status de cada módulo (testes passando? imports ok?)
3. **Campaign Pipeline** — campanhas ativas (P19) → publishing (P8) → delivery (P17)
4. **Alert Feed** — warnings, blockers, checkpoints pendentes
5. **Observability Snapshot** — últimas métricas do P16
6. **Memory Status** — fontes disponíveis, último ContextPack gerado
7. **Capability Gaps** — gaps abertos, proposals pendentes (P22)
8. **Autonomous Runs** — execuções autônomas em andamento (P23)
9. **Quick Actions** — atalhos para comandos frequentes
10. **Export** — snapshot do cockpit em markdown/json para compartilhar

---

## 4. O QUE NÃO FAZ

| PROIBIDO | Motivo |
|---|---|
| Controlar módulos (iniciar/parar/editar) | Cockpit é read-only. Controle = Claude Code |
| Substituir Grafana/Observability | P24 consome P16, não substitui |
| Fazer análise preditiva ou ML | Fora do escopo. P13 analytics cobre análise |
| Ser uma UI web complexa com React | v1 é terminal dashboard (Rich/Textual). Web é futuro |
| Auto-ajustar parâmetros do sistema | Read-only. Ações manuais via Claude Code |
| Conectar-se a APIs externas | Dados vêm dos módulos locais |
| Armazenar histórico | Snapshots efêmeros. P4/P16 armazenam histórico |

---

## 5. RELAÇÃO COM P20

P24 consome o P20 como **fonte primária de dados**:

```python
# Cockpit pergunta ao P20:
cockpit_data = {
    "active_missions": SupremeOrchestrator.list_active_missions(),  # NOVO método
    "recent_reports": SupremeOrchestrator.list_recent_reports(limit=5),
    "pending_approvals": SupremeOrchestrator.list_pending_approvals(),
}
```

P20 ganha métodos de **introspecção** (não alteram comportamento, apenas expõem estado):

```python
class SupremeOrchestrator:
    # Existente:
    def run(self, request: str) -> SupremeMission: ...

    # NOVOS (para P24):
    @staticmethod
    def list_active_missions() -> list[dict]: ...
    @staticmethod  
    def list_recent_reports(limit: int = 5) -> list[dict]: ...
    @staticmethod
    def list_pending_approvals() -> list[dict]: ...
    @staticmethod
    def get_mission_summary(mission_id: str) -> dict: ...
```

---

## 6. RELAÇÃO COM MÓDULOS EXISTENTES

| Módulo | Dados expostos no Cockpit |
|---|---|
| P20 `omnis_supreme` | Missões ativas, relatórios, approvals pendentes |
| P19 `campaign_manager` | Campanhas ativas, budgets, ROIs |
| P17 `delivery_portal` | Deliveries pendentes, feedbacks |
| P8 `publisher_argos` | Itens na fila de publish |
| P16 `observability_local` | Último ObservabilitySnapshot, alertas |
| P13 `analytics` | MetricSummary das últimas 24h |
| P18 `governance` | Políticas ativas, decisões recentes |
| P4 `memory_pack` | Fontes disponíveis, último ContextPack |
| P21 `memory_intel` | Últimos aprendizados, padrões detectados |
| P22 `capability_forge_real` | Gaps abertos, proposals pendentes |
| P23 `autonomous_execution` | Runs autônomas ativas, status |

| Módulo | NÃO exposto (domínio interno) |
|---|---|
| P1, P2, P3, P5, P6, P7, P9, P10, P11, P12, P14, P15 | Muito granular para cockpit. Agregados via P19/P17/P20 |

---

## 7. CONTRATOS PRINCIPAIS

### 7.1 CockpitSnapshot

```python
@dataclass
class CockpitSnapshot:
    snapshot_id: str             # "ckp_<8hex>"
    generated_at: str
    
    # Missões
    active_missions: list[dict]        # SupremeMission resumidas
    missions_today: int
    missions_completed_today: int
    pending_approvals: int
    
    # Pipeline
    active_campaigns: int              # P19 campaigns != archived
    pending_deliveries: int            # P17 packages != closed
    publish_queue_size: int            # P8 items pendentes
    
    # Saúde
    modules_healthy: int
    modules_total: int
    tests_passing: int
    tests_failing: int
    alerts: list[dict]                 # [{severity, module, message}]
    
    # Autônomo
    autonomous_runs_active: int
    autonomous_runs_paused: int
    
    # Memória / Aprendizado
    memory_sources_available: int
    recent_learnings: list[str]
    open_capability_gaps: int
    
    # Sistema
    disk_percent_free: float
    containers_healthy: int
    containers_unhealthy: int
```

### 7.2 CockpitModule

```python
@dataclass
class CockpitModule:
    """Registro de um módulo no cockpit."""
    module_name: str             # "P20", "P17", "P19", etc.
    namespace: str               # "omnis_supreme", "delivery_portal", etc.
    status: str                  # "healthy" | "degraded" | "error" | "unknown"
    test_count: int
    test_pass_rate: float        # 0.0 - 1.0
    last_validated: str
    imports_ok: bool
    alerts: list[str]
```

---

## 8. STATE / FLOW

P24 não tem state machine própria — ele é stateless. Cada chamada gera um `CockpitSnapshot` fresco.

### Refresh flow

```
┌──────────────────────────────────────────────┐
│              COCKPIT REFRESH                  │
│                                               │
│  [User] cockpit refresh                       │
│     │                                          │
│     ├─→ P20: active missions + approvals      │
│     ├─→ P19: campaign counts by status        │
│     ├─→ P17: delivery counts by status        │
│     ├─→ P8:  queue size                       │
│     ├─→ P16: latest ObservabilitySnapshot     │
│     ├─→ P21: recent learnings                 │
│     ├─→ P22: open gaps count                  │
│     ├─→ P23: autonomous runs status           │
│     └─→ System: disk, containers              │
│                                               │
│  [Aggregate] → CockpitSnapshot                │
│  [Render] → Terminal output                   │
│  [Cache] → 60s TTL (evita refresh excessivo) │
└──────────────────────────────────────────────┘
```

---

## 9. ARQUIVOS SUGERIDOS

```
src/live_cockpit/                   # P24 namespace
├── __init__.py
├── models.py                       # CockpitSnapshot, CockpitModule
├── collector.py                    # CockpitCollector — coleta dados de todos os módulos
├── renderer.py                     # CockpitRenderer — formata saída (terminal/v1)
├── alerts.py                       # AlertAggregator — consolida alerts de todos os módulos
├── errors.py                       # CockpitError, ModuleUnreachableError
└── cli.py                          # cockpit, cockpit refresh, cockpit export

tests/live_cockpit/
├── __init__.py
├── test_models.py                  # 10+ testes
├── test_collector.py               # 20+ testes (coleta de cada módulo)
├── test_renderer.py                # 10+ testes (formatação de saída)
├── test_alerts.py                  # 10+ testes
└── test_e2e_cockpit.py             # 10+ testes

docs/live_cockpit/
└── P24_LIVE_COCKPIT_SUPREME_SKELETON.md
```

**Total: 7 source + 4 test + 1 doc = 12 arquivos**

---

## 10. CLASSES SUGERIDAS

```python
class CockpitCollector:
    """Coleta dados de todos os módulos para montar o snapshot."""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.alert_aggregator = AlertAggregator()

    def collect_all(self) -> CockpitSnapshot:
        """Coleta dados de todos os módulos registrados."""

    def collect_missions(self) -> dict: ...       # P20
    def collect_campaigns(self) -> dict: ...      # P19
    def collect_deliveries(self) -> dict: ...     # P17
    def collect_publish_queue(self) -> dict: ...  # P8
    def collect_observability(self) -> dict: ...  # P16
    def collect_memory(self) -> dict: ...         # P21 + P4
    def collect_capability_gaps(self) -> dict: ... # P22
    def collect_autonomous(self) -> dict: ...     # P23
    def collect_system_health(self) -> dict: ...  # disk, containers
    def collect_module_health(self) -> list[CockpitModule]: ...


class CockpitRenderer:
    """Renderiza CockpitSnapshot para terminal."""

    def render(self, snapshot: CockpitSnapshot) -> str:
        """Formata snapshot como texto para terminal."""

    def render_compact(self, snapshot: CockpitSnapshot) -> str:
        """Versão compacta (1 linha por seção)."""

    def render_json(self, snapshot: CockpitSnapshot) -> str:
        """Exporta como JSON."""

    def render_markdown(self, snapshot: CockpitSnapshot) -> str:
        """Exporta como Markdown (para compartilhar)."""


class AlertAggregator:
    """Consolida alerts de todos os módulos."""

    def collect_alerts(self) -> list[dict]:
        """Varre módulos e coleta warnings/blockers."""

    def prioritize(self, alerts: list[dict]) -> list[dict]:
        """Ordena por severity: critical > high > medium > low."""

    def summary(self, alerts: list[dict]) -> str:
        """Resumo de 1 linha: '3 critical, 2 high, 5 medium'."""
```

---

## 11. CLI COMMANDS SUGERIDOS

```python
@cockpit.command()
def show():
    """Exibe o cockpit completo."""

@cockpit.command()
def refresh():
    """Força refresh do snapshot (ignora cache)."""

@cockpit.command()
def compact():
    """Versão compacta do cockpit (1 tela)."""

@cockpit.command()
@click.option("--format", type=click.Choice(["json", "markdown"]), 
              default="markdown")
def export(format: str):
    """Exporta snapshot atual para arquivo."""

@cockpit.command()
def watch():
    """Modo watch: atualiza cockpit a cada 60s."""
```

---

## 12. TEST STRATEGY

### Meta: ≥ 60 testes

| Arquivo | Testes | Foco |
|---|---|---|
| `test_models.py` | 10+ | CockpitSnapshot.new(), to_dict/from_dict, CockpitModule status |
| `test_collector.py` | 20+ | Cada método collect_* retorna dados no formato esperado. Módulo indisponível → status "unknown" (não quebra) |
| `test_renderer.py` | 10+ | Render gera texto formatado, compact não excede 40 linhas, JSON é válido, markdown tem cabeçalhos |
| `test_alerts.py` | 10+ | Coleta alerts de múltiplos módulos, priorização correta, resumo de 1 linha |
| `test_e2e_cockpit.py` | 10+ | collect_all() → CockpitSnapshot completo → render → sem exceções |

---

## 13. DRY-RUN STRATEGY

Cockpit é **sempre read-only**, então dry_run é menos crítico. Mas segue o padrão:

```python
class CockpitCollector:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run  # default True

    def collect_all(self) -> CockpitSnapshot:
        # dry_run não muda comportamento (cockpit é read-only)
        # Mas mantemos por consistência com o resto do OMNIS
        pass
```

---

## 14. FAILURE / RECOVERY

| Falha | Comportamento |
|---|---|
| Módulo não importável | `ModuleUnreachableError` → status="unknown" no CockpitModule, prossegue |
| P20 sem missões ativas | Campos de missão zerados, sem erro |
| P16 sem snapshot recente | "No recent observability data" no campo de alerts |
| Disk/container check falha | "System health: unavailable" — cockpit não quebra |
| Timeout na coleta (>10s) | Retorna snapshot parcial com warning "collection incomplete" |

**Princípio:** Cockpit nunca quebra. Sempre retorna o melhor snapshot possível com dados disponíveis.

---

## 15. RISCOS ARQUITETURAIS

| # | Risco | Impacto | Prob | Mitigação |
|---|---|---|---|---|
| R1 | Cockpit importar 15+ módulos e virar God Module | Alto — acoplamento | Média | Collector usa lazy imports. Cada collect_* é independente |
| R2 | Refresh lento (>5s) frustrar operador | Baixo — UX | Média | Cache 60s. Cada collect_* tem timeout de 2s |
| R3 | Dados inconsistentes entre módulos (timing) | Baixo | Baixa | Snapshot tem timestamp único. Consistência eventual é aceitável |
| R4 | Cockpit evoluir para UI web complexa | Médio — escopo | Baixa | v1 é terminal apenas. Web é projeto separado |

---

## 16. ANTI-PATTERNS PROIBIDOS

```
✗ CONTROLAR MÓDULOS PELO COCKPIT — cockpit é read-only
✗ IMPORTAR MÓDULOS DE DOMÍNIO DIRETAMENTE — usar exports públicos
✗ CACHE PARA SEMPRE — TTL máximo 60s
✗ QUEBRAR SE MÓDULO INDISPONÍVEL — degradação graciosa
✗ 500 LINHAS DE CÓDIGO POR ARQUIVO — manter módulos pequenos
✗ FAZER ANÁLISE NO COCKPIT — cockpit mostra, não analisa
```

---

## 17. CRITÉRIOS DE ACEITE

- [ ] Namespace `src/live_cockpit/` com 7 arquivos
- [ ] Testes ≥ 60 (targeted), todos passando
- [ ] CockpitCollector.collect_all() funcional
- [ ] CockpitRenderer com 4 formatos (full, compact, json, markdown)
- [ ] `cockpit show` exibe snapshot completo no terminal
- [ ] Módulo indisponível → status "unknown", não quebra
- [ ] Cache 60s TTL
- [ ] dry_run=True default
- [ ] Zero toques em módulos existentes
- [ ] Full suite sem regressões

---

## 18. ORDEM INCREMENTAL

### M1: Models + Errors
- `models.py`, `errors.py`
- `test_models.py` — 10+ testes

### M2: Collector Core
- `collector.py` — collect_all(), collect_missions(), collect_system_health()
- `test_collector.py` — 10+ testes

### M3: Full Collector + Alerts
- Completar `collector.py` — todos os collect_* methods
- `alerts.py` — AlertAggregator
- `test_collector.py` + `test_alerts.py` — 20+ testes

### M4: Renderer + CLI
- `renderer.py` — 4 formatos
- `cli.py` — cockpit show, refresh, compact, export
- `test_renderer.py` — 10+ testes

### M5: E2E + Docs
- `test_e2e_cockpit.py` — 10+ testes
- `__init__.py`, skeleton doc
- Full suite validation

---

## 19. RECOMENDAÇÃO DE PARALELIZAÇÃO

**1 frente única.** P24 é o módulo mais simples pós-P20. 12 arquivos, 60 testes. Sequencial sem oportunidade de paralelismo.

---

*OMNIS Control Tower — P24 Live Cockpit Supreme Architecture.*

# P28 — SELF-IMPROVEMENT LOOP ARCHITECTURE

> **Data:** 2026-05-14
> **Status:** ARCHITECTURE DRAFT — Aguardando revisão
> **Base:** master pós-P24 (4604 testes, 0 regressões)
> **Pré-requisitos:** P21 Memory + P22 Forge + P23 Autonomous + P24 Cockpit + P25 Multi-Model

---

## 1. DEFINIÇÃO

P28 Self-Improvement Loop é o **ciclo de aprendizado e melhoria contínua** do OMNIS. Ele coleta feedback de todas as execuções (missões, builds, ações), analisa padrões de sucesso/fracasso, detecta gaps de capability, propõe melhorias, e as implementa após aprovação humana. É o OMNIS ficando melhor a cada iteração — mas SEM auto-modificação cega.

---

## 2. PROBLEMA QUE RESOLVE

**Atual:** O OMNIS executa missões, gera código, coleta dados — mas não aprende sistematicamente com os resultados. Padrões de falha se repetem. Gaps de capability são detectados mas não priorizados. Melhorias dependem do operador perceber manualmente.

**Com P28:** O OMNIS detecta automaticamente:
- "Missões do tipo X falham 40% das vezes no step Y" → proposta de melhoria
- "Modelo Z tem latência 3x maior que alternativas" → sugestão de troca
- "Gap de capability W aparece em 5 missões esta semana" → priorização automática
- "Padrão de código inseguro detectado em builds recentes" → atualização de policy scan

Mas **toda melhoria passa por approval humano**. P28 propõe, humano decide.

---

## 3. O QUE FAZ

1. **Feedback Collector** — coleta resultados de todas as execuções (P20 missões, P22 builds, P27 ações)
2. **Pattern Analyzer** — detecta padrões: falhas recorrentes, lentidão, gaps comuns
3. **Gap Prioritizer** — ranqueia gaps de capability por impacto/frequência/urgência
4. **Improvement Proposer** — gera propostas concretas de melhoria (não abstratas)
5. **Improvement Executor** — implementa propostas aprovadas (usa P22 para código, P25 para config)
6. **Impact Measurer** — mede se a melhoria realmente resolveu o problema
7. **Feedback Loop** — coleta o impacto e realimenta o analyzer

---

## 4. O QUE NÃO FAZ

| PROIBIDO | Motivo |
|---|---|
| Auto-modificar código sem approval | Toda proposta de melhoria passa por governance |
| Auto-otimizar hiperparâmetros de modelos | Fora do escopo. P25 gerencia modelo, não treina |
| Reescrever módulos existentes sem supervisão | Melhorias em código são PRs, não patches automáticos |
| Decidir sozinho o que melhorar | P28 PROPÕE. Operador PRIORIZA e APROVA |
| Fazer A/B testing automático em produção | Fora do escopo. Testes são isolados |
| Alterar regras de governance | Governance só muda com approval humano explícito |
| Auto-escalar infraestrutura | Fora do escopo. Infra é externa |

---

## 5. RELAÇÃO COM P20 SUPREME

P20 é a **fonte primária de feedback**:

- Toda missão concluída gera `MissionReport`
- P28 analisa reports para detectar padrões de falha
- Steps com `checkpoint` frequente → sugestão de simplificar
- Steps que sempre falham → sugestão de remover ou refatorar

```python
# P20 reporter.py já gera MissionReport
# P28 adiciona:
class FeedbackCollector:
    def collect_from_report(self, report: MissionReport) -> ExecutionFeedback: ...
```

---

## 6. RELAÇÃO COM P21 MEMORY

P21 é a **fonte de dados históricos** e o **destino de aprendizados**:

- P28 consulta P21 para análise de padrões de longo prazo
- P28 escreve em P21: `learn_from_improvement()` — registra melhorias aplicadas
- Similaridade de missões (P21) ajuda a detectar "esta falha já aconteceu antes?"

P21 e P28 formam o ciclo de memória de longo prazo do OMNIS.

---

## 7. RELAÇÃO COM P22 FORGE

P22 é o **executor de melhorias que envolvem código**:

| Melhoria Proposta | Implementada por |
|---|---|
| "Criar skill para gap X" | P22 `CapabilityBuilder.build()` |
| "Atualizar template Y com nova regra" | P22 `render_template()` |
| "Adicionar teste para cenário Z" | P22 `generate_test_content()` |
| "Corrigir policy scan para detectar W" | P22 `scaffold()` → novo policy |

P28 propõe. P22 implementa. Operador aprova.

---

## 8. RELAÇÃO COM P23 AUTONOMOUS EXECUTION

P28 **analisa execuções do P23** para detectar melhorias:

- Circuit breaker abriu 5x esta semana → proposta de aumentar threshold ou refatorar step
- Checkpoint Y sempre pausa mas nunca é negado → sugestão de rebaixar risco para auto-approve
- Timeout frequente em step Z → proposta de aumentar timeout ou dividir step

P23 também pode **executar melhorias autonomamente** (com approval gates):

```yaml
mission:
  intent: self_improve
  steps:
    - analyze_feedback       # automático
    - detect_patterns        # automático
    - propose_improvements   # checkpoint: review proposals
    - execute_improvements   # checkpoint: approval para cada melhoria
    - measure_impact         # automático (roda testes, compara métricas)
```

---

## 9. RELAÇÃO COM P24 LIVE COCKPIT

P24 mostra:

- **Melhorias propostas** — fila de proposals aguardando review
- **Melhorias aplicadas** — com impacto medido (positivo/negativo/neutro)
- **Gaps priorizados** — ranking por impacto
- **Health Score** — métrica composta de saúde do sistema (sobe quando melhorias funcionam)
- **Loop Status** — última análise, quantas melhorias pendentes

---

## 10. CONTRATOS PRINCIPAIS

### 10.1 ExecutionFeedback

```python
@dataclass
class ExecutionFeedback:
    feedback_id: str           # "sif_<8hex>"
    source_type: str           # "mission" | "build" | "action" | "system"
    source_id: str             # mission_id, build_id, action_result_id
    status: str                # "success" | "partial_success" | "failure"
    step_results: list[dict]   # detalhe por step
    errors: list[str]
    warnings: list[str]
    latency_ms: int
    model_used: str            # qual modelo foi usado (P25)
    collected_at: str

    @classmethod
    def from_mission_report(cls, report: MissionReport) -> "ExecutionFeedback": ...
    @classmethod
    def from_build_result(cls, build: AppBuild) -> "ExecutionFeedback": ...
```

### 10.2 ImprovementProposal

```python
@dataclass
class ImprovementProposal:
    proposal_id: str           # "sip_<8hex>"
    title: str                 # título curto e acionável
    category: str              # "capability_gap" | "performance" | "reliability" | "cost" | "security"
    severity: str              # low | medium | high | critical
    evidence: list[str]        # feedback_ids que fundamentam esta proposta
    current_state: str         # descrição do problema
    proposed_change: str       # o que mudar
    expected_impact: str       # como medir se funcionou
    implementation_type: str   # "code_change" | "config_change" | "new_capability" | "process_change"
    auto_implementable: bool   # True se P22 consegue implementar sozinho
    status: str                # "draft" | "proposed" | "approved" | "rejected" | "implemented" | "measured"
    approved_by: str
    created_at: str
```

### 10.3 ImpactMeasurement

```python
@dataclass
class ImpactMeasurement:
    measurement_id: str        # "sim_<8hex>"
    proposal_id: str
    metric: str                # "mission_success_rate", "avg_latency_ms", "cost_per_mission", etc.
    value_before: float
    value_after: float
    delta: float               # positivo = melhorou
    verdict: str               # "improved" | "degraded" | "neutral" | "insufficient_data"
    sample_size: int           # quantas execuções após a mudança
    measured_at: str
```

---

## 11. STATE / FLOW

```
┌──────────────────────────────────────────────────────────────────────┐
│                    P28 SELF-IMPROVEMENT LOOP                          │
│                                                                       │
│                        ┌─────────────────┐                            │
│                        │  1. COLLECT      │                            │
│                        │  Feedback de     │                            │
│                        │  todas as fontes │                            │
│                        └────────┬────────┘                            │
│                                 │                                     │
│                        ┌────────▼────────┐                            │
│                        │  2. ANALYZE      │                            │
│                        │  Pattern detection│                           │
│                        │  P21 similaridade │                           │
│                        └────────┬────────┘                            │
│                                 │                                     │
│                        ┌────────▼────────┐                            │
│                        │  3. PRIORITIZE   │                            │
│                        │  Gaps por impacto│                            │
│                        │  frequência, urg.│                           │
│                        └────────┬────────┘                            │
│                                 │                                     │
│                        ┌────────▼────────┐                            │
│                        │  4. PROPOSE      │◀── APPROVAL GATE           │
│                        │  ImprovementPro- │    Operador revisa         │
│                        │  posals concretas│    propostas               │
│                        └────────┬────────┘                            │
│                                 │                                     │
│                        ┌────────▼────────┐                            │
│                        │  5. EXECUTE      │◀── APPROVAL GATE           │
│                        │  P22 gera código │    Operador aprova         │
│                        │  P25 ajusta conf │    cada melhoria           │
│                        └────────┬────────┘                            │
│                                 │                                     │
│                        ┌────────▼────────┐                            │
│                        │  6. MEASURE      │                            │
│                        │  Impacto real    │                            │
│                        │  Antes vs Depois │                            │
│                        └────────┬────────┘                            │
│                                 │                                     │
│                        ┌────────▼────────┐                            │
│                        │  7. LEARN        │                            │
│                        │  Feedback no P21 │                            │
│                        │  Atualiza scores │                            │
│                        └────────┬────────┘                            │
│                                 │                                     │
│                          ┌──────▼──────┐                              │
│                          │  REPEAT      │                              │
│                          │  Próximo     │                              │
│                          │  ciclo       │                              │
│                          └─────────────┘                              │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

**Ciclo pode ser agendado (diário) ou trigger por evento (N falhas consecutivas).**

---

## 12. ARQUIVOS SUGERIDOS

```
src/self_improvement/
├── __init__.py               # Exports: FeedbackCollector, PatternAnalyzer, ImprovementProposer, etc.
├── models.py                 # ExecutionFeedback, ImprovementProposal, ImpactMeasurement, FeedbackSource
├── errors.py                 # ImprovementError, AnalysisError, ProposalError, MeasurementError
├── collector.py              # FeedbackCollector — coleta feedback de todas as fontes
├── analyzer.py               # PatternAnalyzer — detecta padrões de falha/sucesso
├── prioritizer.py            # GapPrioritizer — ranqueia gaps por impacto
├── proposer.py               # ImprovementProposer — gera propostas concretas
├── executor.py               # ImprovementExecutor — implementa propostas aprovadas
├── measurer.py               # ImpactMeasurer — mede antes/depois
└── cli.py                    # CLI: improve analyze, improve propose, improve status, improve history

tests/self_improvement/
├── test_models.py            # 15+ testes
├── test_collector.py         # 12+ testes
├── test_analyzer.py          # 12+ testes
├── test_prioritizer.py       # 10+ testes
├── test_proposer.py          # 12+ testes
├── test_executor.py          # 12+ testes
├── test_measurer.py          # 10+ testes
└── test_e2e_improvement.py   # 12+ testes

docs/self_improvement/
└── P28_SELF_IMPROVEMENT_LOOP_ARCHITECTURE.md
```

**Total: 10 source + 8 test + 1 doc = 19 arquivos**

---

## 13. CLASSES SUGERIDAS

```python
class FeedbackCollector:
    """Coleta feedback de todas as fontes de execução."""
    def __init__(self, dry_run: bool = True): ...
    def collect_all(self) -> list[ExecutionFeedback]: ...
    def collect_from_missions(self, since: str) -> list[ExecutionFeedback]: ...
    def collect_from_builds(self, since: str) -> list[ExecutionFeedback]: ...
    def collect_from_actions(self, since: str) -> list[ExecutionFeedback]: ...
    def collect_from_system(self) -> ExecutionFeedback: ...

class PatternAnalyzer:
    """Detecta padrões recorrentes em feedback."""
    def __init__(self, memory: MemoryIntelligence): ...
    def analyze(self, feedbacks: list[ExecutionFeedback]) -> list[Pattern]: ...
    def detect_failure_patterns(self, feedbacks) -> list[Pattern]: ...
    def detect_performance_patterns(self, feedbacks) -> list[Pattern]: ...
    def detect_gap_patterns(self, feedbacks) -> list[Pattern]: ...
    def compare_with_history(self, pattern: Pattern) -> list[Pattern]: ...

class GapPrioritizer:
    """Ranqueia gaps por impacto, frequência, urgência."""
    def prioritize(self, patterns: list[Pattern]) -> list[PrioritizedGap]: ...
    def score(self, gap: PrioritizedGap) -> float: ...
    def top_n(self, n: int = 10) -> list[PrioritizedGap]: ...

class ImprovementProposer:
    """Gera propostas concretas de melhoria."""
    def propose(self, gaps: list[PrioritizedGap]) -> list[ImprovementProposal]: ...
    def generate_proposal(self, gap: PrioritizedGap) -> ImprovementProposal: ...
    def estimate_impact(self, proposal: ImprovementProposal) -> dict: ...
    def validate_proposal(self, proposal: ImprovementProposal) -> list[str]: ...

class ImprovementExecutor:
    """Implementa propostas aprovadas."""
    def __init__(self, forge: CapabilityBuilder, dry_run: bool = True): ...
    def execute(self, proposal: ImprovementProposal) -> ImpactMeasurement: ...
    def execute_code_change(self, proposal) -> ImpactMeasurement: ...
    def execute_config_change(self, proposal) -> ImpactMeasurement: ...
    def rollback(self, proposal_id: str) -> bool: ...

class ImpactMeasurer:
    """Mede impacto real de melhorias aplicadas."""
    def measure(self, proposal: ImprovementProposal, before_feedbacks, after_feedbacks) -> ImpactMeasurement: ...
    def compare_metrics(self, metric: str, before: list, after: list) -> dict: ...
    def is_significant(self, measurement: ImpactMeasurement) -> bool: ...
```

---

## 14. CLI COMMANDS SUGERIDOS

```
improve analyze [--since "2026-05-01"]        # Analisa feedback e detecta padrões
improve gaps [--top 10]                        # Lista gaps priorizados
improve propose [--gap-id <id>]                # Gera propostas para gaps
improve list [--status proposed|approved|...]  # Lista propostas
improve approve <proposal_id>                  # Aprova proposta
improve reject <proposal_id> [--reason "..."]  # Rejeita proposta
improve execute <proposal_id> [--dry-run]      # Implementa proposta aprovada
improve measure <proposal_id>                  # Mede impacto de melhoria
improve status                                 # Status do ciclo atual
improve history [--limit 20]                   # Histórico de melhorias
```

---

## 15. TEST STRATEGY

| Arquivo | Testes | Foco |
|---|---|---|
| `test_models.py` | 15+ | ExecutionFeedback validation, ImprovementProposal status transitions, ImpactMeasurement delta |
| `test_collector.py` | 12+ | Coleta de todas as fontes. Fonte indisponível → lista vazia, sem erro |
| `test_analyzer.py` | 12+ | Detecção de padrões. Múltiplos feedbacks com mesma falha → 1 pattern |
| `test_prioritizer.py` | 10+ | Score > 0. Gap mais frequente no topo. Ranking estável |
| `test_proposer.py` | 12+ | Proposta concreta e acionável. Auto-implementable detection |
| `test_executor.py` | 12+ | Dry-run não altera código. Execução real com mock P22. Rollback |
| `test_measurer.py` | 10+ | Delta calculado corretamente. Verdict baseado em threshold. Sample insuficiente |
| `test_e2e_improvement.py` | 12+ | Collect → Analyze → Prioritize → Propose → Approve → Execute → Measure. Ciclo completo |

**Meta: ≥ 95 testes**

---

## 16. DRY-RUN STRATEGY

```python
class ImprovementExecutor:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def execute(self, proposal: ImprovementProposal) -> ImpactMeasurement:
        if self.dry_run:
            return ImpactMeasurement(
                proposal_id=proposal.proposal_id,
                metric="estimated",
                value_before=0.0,
                value_after=0.0,
                delta=0.0,
                verdict="insufficient_data",
                sample_size=0,
            )
        # Execução real
```

Todo o ciclo é dry-run safe. Collect e Analyze sempre funcionam (read-only). Propose é determinístico. Só Execute com dry_run=False altera algo — e requer approval.

---

## 17. APPROVAL STRATEGY

Duplo gate:

| Gate | Quando | Quem |
|---|---|---|
| **Proposal Gate** | Após `proposer.propose()`, antes de executar | Operador revisa proposta, evidência, impacto estimado |
| **Execution Gate** | Após proposal aprovada, antes de executar mudança | Operador autoriza implementação |

Propostas de `severity="critical"` ou `category="security"` requerem approval adicional.

Propostas `auto_implementable=False` (mudança de processo, não de código) são sempre review humano.

---

## 18. FAILURE / RECOVERY

| Falha | Comportamento |
|---|---|
| Análise sem dados suficientes | `AnalysisError("insufficient data")`. Ciclo agenda retry |
| Proposta rejeitada | `proposal.status="rejected"`. Registrada para não ser reproposta por 30 dias |
| Execução de melhoria falha | Rollback automático. Proposal volta para "approved" |
| Impacto medido é negativo (piorou) | Rollback recomendado. Alerta no P24. Proposal marcada "degraded" |
| Melhoria causa regressão em testes | Detectado pelo measurer (test suite antes/depois). Rollback |
| Loop infinito de melhorias | Max 3 melhorias ativas simultâneas. Rate limit de 1 proposta/dia |

---

## 19. RISCOS ARQUITETURAIS

| # | Risco | Impacto | Prob | Mitigação |
|---|---|---|---|---|
| R1 | Auto-modificação sem supervisão | Crítico | Muito Baixa | Duplo approval gate. Nada executa sem approval humano |
| R2 | Melhoria quebrar sistema | Alto | Média | Rollback automático. Test suite roda antes/depois. Isolamento |
| R3 | Loop de melhoria sem fim | Médio | Baixa | Max 3 ativas. 1 proposta/dia. Circuit breaker se 3 consecutivas falharem |
| R4 | Feedback insuficiente para análise | Baixo | Alta | Analyzer reporta "insufficient data" em vez de inventar padrão |
| R5 | Propostas irrelevantes ou triviais | Baixo | Média | Prioritizer por impacto. Threshold mínimo de score para propor |

---

## 20. ANTI-PATTERNS PROIBIDOS

```
✗ AUTO-MODIFICAÇÃO SEM GOVERNANÇA — duplo gate obrigatório
✗ EXECUTAR MELHORIA SEM MEDIR — toda melhoria tem ImpactMeasurement
✗ IGNORAR FEEDBACK NEGATIVO — piorou? Rollback + alerta
✗ REPROPOR MESMA COISA REJEITADA — 30 dias de cooldown
✗ ANALISAR SEM DADOS SUFICIENTES — "insufficient data" é resposta válida
✗ BYPASSAR P22 E P25 — melhorias usam ferramentas existentes, não criam atalhos
✗ MUDAR GOVERNANÇA SOZINHO — regras de governance são imutáveis pelo P28
✗ GERAR PROPOSTA ABSTRATA — toda proposta tem implementation_type concreto
```

---

## 21. CRITÉRIOS DE ACEITE

- [ ] Namespace `src/self_improvement/` com 10 arquivos
- [ ] Testes ≥ 95 (targeted), todos passando
- [ ] FeedbackCollector funcional com múltiplas fontes
- [ ] PatternAnalyzer detecta padrões recorrentes
- [ ] ImprovementProposer gera propostas concretas e acionáveis
- [ ] Duplo approval gate funcional
- [ ] ImpactMeasurer calcula delta antes/depois
- [ ] Rollback funcional para melhorias que degradam
- [ ] dry_run=True default
- [ ] Zero toques em módulos existentes (usa contratos públicos)
- [ ] Full suite sem regressões

---

## 22. ORDEM INCREMENTAL DE IMPLEMENTAÇÃO

### M1: Models + Errors + Collector
- `models.py`, `errors.py`, `collector.py`
- `test_models.py`, `test_collector.py`

### M2: Analyzer + Prioritizer
- `analyzer.py`, `prioritizer.py`
- `test_analyzer.py`, `test_prioritizer.py`

### M3: Proposer
- `proposer.py`
- `test_proposer.py`

### M4: Executor + Measurer
- `executor.py`, `measurer.py`
- `test_executor.py`, `test_measurer.py`

### M5: CLI + E2E + Docs
- `cli.py`
- `test_e2e_improvement.py`
- `__init__.py`, skeleton doc, full suite

---

## 23. RECOMENDAÇÃO DE PARALELIZAÇÃO

**1 frente única.** O loop é circular e cada etapa depende da anterior: collect → analyze → prioritize → propose → execute → measure. Não há paralelismo interno útil.

---

*OMNIS Control Tower — P28 Self-Improvement Loop Architecture.*

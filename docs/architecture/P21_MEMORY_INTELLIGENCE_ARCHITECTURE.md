# P21 — MEMORY INTELLIGENCE ARCHITECTURE

> **Data:** 2026-05-13
> **Status:** DRAFT — Aguardando revisão
> **Base:** master `ada6373` (P20 fechado, 4115 testes, working tree limpo)

---

## 1. DEFINIÇÃO DA P21

P21 Memory Intelligence é a **camada de inteligência contextual** que transforma o armazenamento passivo de memória do OMNIS em um motor ativo de contexto para missões. Ela não armazena dados — ela **recupera, ranqueia, correlaciona e aprende**.

Diferente do P4 `memory_pack` (que define modelos e simula operações) e dos bancos externos (Akasha, Qdrant, Obsidian — que armazenam dados), a P21 é o **cérebro intermediário** que:

1. **Pré-missão:** Responde "o que já sabemos sobre este tipo de missão?"
2. **Pós-missão:** Responde "o que aprendemos que deve ser lembrado?"

Ela preenche o vazio entre os stubs do P20 (`_fetch_memory`, `_fetch_analytics`) e a infraestrutura pronta do P4 (`MemoryPackPlanner`, `ContextPack`, `MissionMemoryRecord`).

---

## 2. O QUE A P21 DEVE FAZER

1. **Memory Retrieval** — receber intent + contexto do P20, consultar fontes (P4), retornar ContextPack populado
2. **Memory Ranking** — usar o ranker do P4, enriquecer com pesos por fonte e tipo de missão
3. **Context Assembly** — montar ContextPack otimizado (evitar bloat, limitar tokens)
4. **Similarity Matching** — dado um intent, encontrar missões anteriores similares e seus aprendizados
5. **Pattern Extraction** — identificar padrões recorrentes: hooks que funcionam, módulos mais usados, pipelines de sucesso
6. **Learning Writeback** — receber MissionReport do P20, extrair aprendizados, gerar MissionMemoryRecord, submeter write plan
7. **Memory Safety** — validar que nenhuma operação real de escrita/delete é executada (dry_run only)
8. **Context Optimization** — evitar prompt bloat: deduplicar hits, truncar snippets, priorizar alta relevância
9. **Source Selection** — escolher quais fontes consultar com base no intent (ex: campanha → Akasha+Obsidian, análise → Analytics+Session)
10. **Feedback Loop** — cada missão completada melhora a qualidade do contexto da próxima

---

## 3. O QUE A P21 NÃO DEVE FAZER

| PROIBIDO | Motivo |
|---|---|
| Conectar-se a Akasha, Postgres, Qdrant ou qualquer banco real | P4 já estabelece dry_run only. P21 herda essa regra |
| Criar novo banco de dados ou storage | Akasha, Qdrant, Obsidian, Gringotts já existem |
| Criar modelos de memória duplicados | P4 já tem MemorySource, MemoryQuery, MemoryHit, ContextPack, MissionMemoryRecord, MemoryWritePlan |
| Importar módulos de domínio (P2, P3, P6, P7, P9, P10, P11, P12, P14, P15) | P21 é infraestrutura, não domínio |
| Executar ações reais (escrever, deletar, enviar) | dry_run=True inegociável |
| Modificar P4 ou P20 | P21 importa exports, nunca edita |
| Fazer análise estatística pesada (pandas, numpy, scipy) | P13 analytics cobre isso. P21 usa MetricSummary |
| Virar "consciência" do sistema com 2000 linhas | Máximo 500 linhas de lógica própria |
| Criar embeddings ou vector search próprio | Akasha/Qdrant já fazem isso externamente |

---

## 4. RELAÇÃO COM P20

P21 é um **plug-in de contexto** para o P20. Ela substitui os 3 stubs do `SupremeContextBuilder`:

```
ANTES (stubs):                     DEPOIS (P21):
_fetch_memory() → dict stub        _fetch_memory() → ContextPack populado
_fetch_analytics() → dict stub     _fetch_analytics() → MetricSummary[]
_fetch_briefings() → dict stub     _fetch_briefings() → CampaignBrief[] (mantido no P20)
```

E adiciona **writeback** ao `SupremeReporter`:

```
ANTES:                              DEPOIS (P21):
SupremeReporter.generate()          SupremeReporter.generate()
  └─ learnings ficam no report        └─ learnings → P21.writeback() → MissionMemoryRecord
```

### Contrato P20 ↔ P21

```python
# P21 fornece estas funções para o P20 chamar:

def retrieve_context(intent: str, mission_id: str, sector: str, 
                     max_hits: int = 8) -> ContextPack:
    """Pré-missão: recupera contexto relevante para o intent."""

def retrieve_similar_missions(intent: str, limit: int = 5) -> list[MissionMemoryRecord]:
    """Pré-missão: encontra missões anteriores similares."""

def extract_patterns(sector: str, intent: str) -> dict:
    """Pré-missão: extrai padrões de sucesso para sector+intent."""

def writeback_learnings(mission: SupremeMission, report: MissionReport) -> MemoryWritePlan:
    """Pós-missão: persiste aprendizados da missão."""
```

**P20 NÃO precisa saber que P21 existe.** O `SupremeContextBuilder` e o `SupremeReporter` apenas chamam funções. Quem implementa essas funções (P4 direto, P21, ou mock) é detalhe de wiring.

---

## 5. RELAÇÃO COM MEMORY_PACK / AKASHA / QDRANT / OBSIDIAN

```
┌──────────────────────────────────────────────────────────────────┐
│                      MEMORY STACK                                │
│                                                                  │
│  ┌─────────────┐                                                 │
│  │    P20      │  SupremeContextBuilder + SupremeReporter        │
│  │  (omnis_    │  "Preciso de contexto para intent X"            │
│  │   supreme)  │  "Aprendi Y, guarda aí"                        │
│  └──────┬──────┘                                                 │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────┐                                                 │
│  │    P21      │  Memory Intelligence                            │
│  │  (memory_   │  Retrieval, Ranking, Similarity, Patterns,      │
│  │   intel)    │  Writeback, Optimization, Safety                │
│  └──────┬──────┘                                                 │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────┐                                                 │
│  │    P4       │  Memory Pack (models + simulated ops)           │
│  │  (memory_   │  MemoryQuery, ContextPack, MemoryHit,           │
│  │   pack)     │  MissionMemoryRecord, MemoryWritePlan           │
│  └──────┬──────┘                                                 │
│         │                                                        │
│         ▼ (futuro — não no skeleton)                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                 EXTERNAL MEMORY BACKENDS                  │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │   │
│  │  │ Akasha   │ │ Obsidian │ │ Qdrant   │ │ Gringotts  │  │   │
│  │  │ pgvector │ │ 7.8K md  │ │ Mem0     │ │ schema     │  │   │
│  │  │ :5432    │ │ files    │ │ :6333    │ │ unificado  │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### Responsabilidades

| Camada | Responsabilidade | Estado atual |
|---|---|---|
| **P20** | Solicita contexto, reporta aprendizados | Stubs (3 funções retornam dicts vazios) |
| **P21** | Recupera, ranqueia, correlaciona, aprende | **NÃO EXISTE — esta arquitetura** |
| **P4** | Modelos, simulação, validação, ranking | Completo (108 testes, 7 sources) |
| **Akasha** | Vector store, 20K docs, 606K chunks | Externo, acessível via pgvector |
| **Obsidian** | 7.792 arquivos markdown | Externo, filesystem |
| **Qdrant/Mem0** | Graph relacional, embeddings | Externo, :6333 |
| **Gringotts** | Schema de negócio unificado | Externo |

---

## 6. CONTEXT PACK CONTRACT

P21 enriquece o `ContextPack` do P4 com metadados adicionais para o P20:

```python
@dataclass
class ContextPack:
    """Do P4 — P21 preenche e retorna para P20."""
    pack_id: str              # "pack_<8hex>"
    query_id: str             # "qry_<8hex>"
    hits: list[MemoryHit]     # hits ranqueados e truncados
    assembled_text: str       # texto montado para injeção no prompt
    source_summary: dict      # {"akasha": 3, "obsidian": 2, ...}
    total_hits: int
    total_sources: int
    top_relevance: str        # "exact" | "high" | "medium" | "low" | "none"
    dry_run: bool
    created_at: str

    # P21 adiciona (via assemble):
    # - assembled_text é otimizado: ≤ 2000 caracteres
    # - hits são deduplicados por título similar
    # - snippets truncados em 300 chars cada
```

### Contrato de tamanho

| Campo | Limite | Razão |
|---|---|---|
| `assembled_text` | ≤ 2000 chars | Evitar prompt bloat no Claude Code |
| `hits` | ≤ 10 | P4 default é 10, P21 respeita |
| `snippet` por hit | ≤ 300 chars | Suficiente para contexto, não sobrecarrega |
| Hits por source | ≤ 3 | Evitar viés de fonte única |

---

## 7. MEMORY QUERY CONTRACT

```python
@dataclass  
class MemoryQuery:
    """Do P4 — P21 cria e submete ao MemoryPackPlanner."""
    query_id: str             # "qry_<8hex>"
    text: str                 # texto de busca (intent + contexto)
    sources: list[str]        # fontes selecionadas por intent
    sectors: list[str]        # setor(es) relevantes
    max_hits: int = 10
    min_relevance: str = "low"
    filters: dict             # filtros adicionais (tags, datas)
    dry_run: bool = True
    created_at: str
```

### Source selection por intent

```python
INTENT_TO_SOURCES = {
    "create_campaign":     ["akasha", "obsidian", "session"],
    "publish_content":     ["akasha", "obsidian", "session"],
    "deliver_to_client":   ["session", "gringotts"],
    "analyze_performance": ["akasha", "session", "biblioteca"],
    "commercial_outreach": ["gringotts", "session", "obsidian"],
}
```

---

## 8. LEARNING RECORD CONTRACT

```python
@dataclass
class MissionMemoryRecord:
    """Do P4 — P21 cria a partir do MissionReport do P20."""
    record_id: str            # "rec_<8hex>"
    mission_id: str           # referencia SupremeMission
    sector: str
    title: str                # "Campanha Natal 2026 — aprendizados"
    summary: str              # resumo executivo do que foi aprendido
    key_insights: list[str]   # insights pontuais
    decisions: list[str]      # decisões tomadas e seu resultado
    outcomes: list[str]       # métricas de resultado
    source_type: str = "session"
    status: str = "draft"
    tags: list[str]           # ["campanha", "natal", "cliente_x"]
    metadata: dict
    created_at: str
    updated_at: str
```

### Extração de aprendizados (do MissionReport)

```python
def _extract_learnings_from_report(report: MissionReport) -> list[MissionMemoryRecord]:
    records = []
    
    # 1. Insights dos steps que falharam
    for step_summary in report.steps_summary:
        if step_summary["status"] == "failed":
            records.append(MissionMemoryRecord.new(
                mission_id=report.mission_id,
                sector=step_summary.get("sector", "unknown"),
                title=f"Falha: {step_summary['operation']}",
                summary=f"Step {step_summary['step_id']} falhou: {step_summary.get('error', 'unknown')}",
                key_insights=[f"Evitar {step_summary['operation']} sem {step_summary.get('missing_dep', 'pré-requisito')}"],
                decisions=[f"Não repetir {step_summary['operation']} nestas condições"],
                outcomes=["step_failed"],
                tags=["failure", step_summary.get("module_ref", "unknown")],
            ))
    
    # 2. Insights dos steps que tiveram sucesso
    for step_summary in report.steps_summary:
        if step_summary["status"] == "done":
            records.append(MissionMemoryRecord.new(
                mission_id=report.mission_id,
                sector=step_summary.get("sector", "unknown"),
                title=f"Sucesso: {step_summary['operation']}",
                summary=f"Step concluído em {step_summary.get('duration_ms', '?')}ms",
                key_insights=[f"Pipeline {step_summary['module_ref']} funcionou para {report.mission_id}"],
                decisions=[],
                outcomes=[f"duration_ms={step_summary.get('duration_ms', 0)}"],
                tags=["success", step_summary.get("module_ref", "unknown")],
            ))
    
    # 3. Insights das métricas agregadas
    if report.metrics:
        records.append(MissionMemoryRecord.new(
            mission_id=report.mission_id,
            sector="cross-cutting",
            title=f"Métricas: {report.mission_id}",
            summary=f"Missão envolveu {report.metrics.get('total_steps', 0)} steps, "
                    f"{report.metrics.get('success_rate', 0)}% sucesso",
            key_insights=report.metrics.get("insights", []),
            decisions=[],
            outcomes=[f"success_rate={report.metrics.get('success_rate', 0)}%"],
            tags=["metrics", "summary"],
        ))

    return records
```

---

## 9. MISSION SIMILARITY MODEL

```python
@dataclass
class MissionSimilarityResult:
    """Resultado de busca por missões similares."""
    source_mission: MissionMemoryRecord
    similarity_score: float          # 0.0 a 1.0
    matched_on: list[str]            # ["intent", "sector", "tags", "modules"]
    relevant_learnings: list[str]    # insights aplicáveis à nova missão

def find_similar_missions(
    intent: str,
    sector: str,
    tags: list[str],
    past_records: list[MissionMemoryRecord],
    limit: int = 5,
) -> list[MissionSimilarityResult]:
    """Calcula similaridade entre uma nova missão e registros passados.

    Score = weighted sum:
      - mesmo intent:      +0.40
      - mesmo sector:      +0.30
      - overlap de tags:   +0.20 (proporcional)
      - módulos em comum:  +0.10 (proporcional)
    """
    results = []
    for record in past_records:
        score = 0.0
        matched_on = []

        if record.metadata.get("intent") == intent:
            score += 0.40
            matched_on.append("intent")

        if record.sector == sector:
            score += 0.30
            matched_on.append("sector")

        tag_overlap = len(set(tags) & set(record.tags))
        if tag_overlap > 0:
            score += 0.20 * (tag_overlap / max(len(tags), 1))
            matched_on.append("tags")

        results.append(MissionSimilarityResult(
            source_mission=record,
            similarity_score=round(score, 2),
            matched_on=matched_on,
            relevant_learnings=record.key_insights,
        ))

    results.sort(key=lambda r: r.similarity_score, reverse=True)
    return results[:limit]
```

---

## 10. RETRIEVAL STRATEGY

```
┌─────────────────────────────────────────────────────────────────┐
│                   P21 RETRIEVAL FLOW                            │
│                                                                 │
│  Input: intent, sector, mission_id, max_hits=8                 │
│                                                                 │
│  Step 1 — Source Selection                                     │
│    INTENT_TO_SOURCES[intent] → ["akasha", "obsidian", ...]     │
│                                                                 │
│  Step 2 — Build Query                                          │
│    text = f"{intent} {sector}" + tags context                  │
│    MemoryQuery.new(text, sources, sectors=[sector])            │
│                                                                 │
│  Step 3 — Simulated Retrieval                                  │
│    MemoryPackPlanner.simulate_query(query)                     │
│    → hits sintéticos baseados em overlap de palavras           │
│                                                                 │
│  Step 4 — Rank & Filter                                        │
│    rank_memory_hits(hits, min_relevance="low", max_hits)       │
│    → ordenado por (rank_score, source_priority)                │
│                                                                 │
│  Step 5 — Assemble ContextPack                                 │
│    ContextPack.new(query_id).assemble(ranked_hits)             │
│    → assembled_text otimizado (≤ 2000 chars)                   │
│                                                                 │
│  Step 6 — Enrich with Similar Missions                         │
│    similar = find_similar_missions(intent, sector, tags)       │
│    → insights de missões passadas anexados ao contexto         │
│                                                                 │
│  Output: ContextPack + MissionSimilarityResult[]               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 11. WRITEBACK STRATEGY

```
┌─────────────────────────────────────────────────────────────────┐
│                   P21 WRITEBACK FLOW                            │
│                                                                 │
│  Input: SupremeMission + MissionReport (do P20)                │
│                                                                 │
│  Step 1 — Extract Learnings                                    │
│    _extract_learnings_from_report(report)                      │
│    → list[MissionMemoryRecord]                                 │
│                                                                 │
│  Step 2 — Classify & Tag                                       │
│    Cada record recebe tags: intent, sector, modules, status    │
│                                                                 │
│  Step 3 — Build Write Plan                                     │
│    MemoryPackPlanner.plan_memory_writeback(                    │
│        records, target_source="akasha", action="upsert"        │
│    )                                                            │
│    → MemoryWritePlan (dry_run=True, approval_required=True)    │
│                                                                 │
│  Step 4 — Validate Safety                                      │
│    Garantir: is_dry_run=True, requires_approval=True           │
│    Garantir: action != "delete"                                │
│    Garantir: 5 safety_rules_applied presentes                  │
│                                                                 │
│  Step 5 — Log Write Plan (não executar)                        │
│    Registrar que o plano existe, mas NÃO executar              │
│    Status: "planned_for_review"                                │
│                                                                 │
│  Output: MemoryWritePlan (revisão pendente do operador)        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 12. MEMORY SAFETY / GUARDRAILS

### Safety rules (herdadas do P4 + novas)

| # | Regra | Origem | Mecanismo |
|---|---|---|---|
| 1 | `dry_run_only` | P4 | Todas operações têm dry_run=True |
| 2 | `no_real_akasha_connection` | P4 | Zero imports de psycopg2, asyncpg, sqlalchemy |
| 3 | `writeback_plan_never_execute` | P4 | Planos são gerados, nunca executados |
| 4 | `approval_required` | P4 | requires_approval=True em todos os write plans |
| 5 | `no_delete_by_default` | P4 | action="delete" é bloqueado |
| 6 | `no_prompt_injection` | P21 | assembled_text sanitizado (escapar markdown, limitar tamanho) |
| 7 | `no_memory_pollution` | P21 | Dedup de hits, limite de records por missão |
| 8 | `no_circular_context` | P21 | Missão não pode referenciar seu próprio contexto como input |

### Sanitização de assembled_text

```python
def _sanitize_context_text(text: str, max_chars: int = 2000) -> str:
    """Previne prompt injection e limita tamanho."""
    # Truncar
    if len(text) > max_chars:
        text = text[:max_chars-3] + "..."

    # Remover padrões perigosos (blocos de código, instruções)
    text = text.replace("```", "")

    return text
```

---

## 13. COMO EVITAR MEMORY POLLUTION

| Estratégia | Implementação |
|---|---|
| **Limit records por missão** | Máximo 5 MissionMemoryRecords por missão |
| **Dedup por similaridade** | Dois hits com títulos 90% similares → manter o de maior rank |
| **Expiração implícita** | Records com status "superseded" não são retornados em queries |
| **Source balance** | Máximo 3 hits por source no mesmo ContextPack |
| **Tag hygiene** | Tags são validados contra vocabulário controlado (intents + sectors + modules) |
| **Relevância mínima** | Queries default min_relevance="low", mas P21 sobe para "medium" em contextos de produção |
| **Review gate** | Todo write plan tem approval_required=True — operador revisa antes de persistir |

---

## 14. COMO EVITAR PROMPT / CONTEXT BLOAT

| Estratégia | Limite |
|---|---|
| **assembled_text máximo** | 2000 caracteres |
| **Hits por query** | Máximo 10 (default P4), P21 usa 8 |
| **Snippet por hit** | Máximo 300 caracteres |
| **Similar missions** | Máximo 3 resultados anexados ao contexto |
| **Pattern insights** | Máximo 5 bullet points |
| **Priorização** | Hits "high" e "exact" vêm primeiro, "low" são truncados primeiro |
| **Fallback** | Se assembled_text > 2000 após montagem, truncar removendo hits "low" do final |

---

## 15. ESTADOS OU FLUXOS NECESSÁRIOS

P21 não tem state machine própria complexa — ela opera em **dois modos**:

```python
class MemoryIntelMode(str, Enum):
    RETRIEVAL = "retrieval"    # Pré-missão: busca contexto
    WRITEBACK = "writeback"    # Pós-missão: persiste aprendizados
```

### Fluxo Retrieval

```
idle → building_query → querying → ranking → assembling → optimizing → done
                                                                      ↘ error (degradado)
```

### Fluxo Writeback

```
idle → extracting_learnings → classifying → building_plan → validating → planned_for_review
                                                                           ↘ validation_failed
```

**Sem estados terminais complexos** — P21 é stateless entre chamadas. Cada chamada do P20 é independente.

---

## 16. CLASSES SUGERIDAS

### models.py

| Classe | Prefixo | Descrição |
|---|---|---|
| `MemoryIntelConfig` | `mic_` | Configuração: source mapping, limites, thresholds |
| `MissionSimilarityResult` | `sim_` | Resultado de similaridade entre missões |
| `RetrievalResult` | `ret_` | Resultado completo de retrieval (ContextPack + similares + patterns) |
| `MemoryIntelMode` | — | Enum: RETRIEVAL, WRITEBACK |

### service.py

```python
class MemoryIntelligence:
    """Motor de inteligência contextual.

    Uso:
        mi = MemoryIntelligence(dry_run=True)
        
        # Pré-missão
        context = mi.retrieve(intent="create_campaign", sector="midia", 
                              mission_id="spr_abc123")
        
        # Pós-missão
        plan = mi.writeback(mission, report)
    """

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.planner = MemoryPackPlanner.create()
        self.config = MemoryIntelConfig.load()

    # ── Retrieval ──────────────────────────────────────────

    def retrieve(self, intent: str, sector: str, mission_id: str,
                 max_hits: int = 8) -> RetrievalResult:
        """Recupera contexto completo para uma missão."""

    def retrieve_context(self, intent: str, sector: str,
                         max_hits: int = 8) -> ContextPack:
        """Recupera apenas o ContextPack."""

    def retrieve_similar_missions(self, intent: str, sector: str,
                                   tags: list[str] = None,
                                   limit: int = 5) -> list[MissionSimilarityResult]:
        """Encontra missões anteriores similares."""

    def extract_patterns(self, sector: str, intent: str) -> dict:
        """Extrai padrões de sucesso/fracasso para sector+intent."""

    # ── Writeback ─────────────────────────────────────────

    def writeback(self, mission: SupremeMission, 
                  report: MissionReport) -> MemoryWritePlan:
        """Persiste aprendizados de uma missão completa."""

    def learn_from_step(self, mission_id: str, step: SupremeStep,
                        result: dict) -> MissionMemoryRecord:
        """Aprende com um step individual."""

    # ── Internals ─────────────────────────────────────────

    def _select_sources(self, intent: str) -> list[str]: ...
    def _build_query_text(self, intent: str, sector: str, 
                          tags: list[str] = None) -> str: ...
    def _optimize_pack(self, pack: ContextPack) -> ContextPack: ...
    def _extract_learnings(self, report: MissionReport) -> list[MissionMemoryRecord]: ...
```

### errors.py

```python
class MemoryIntelError(Exception): ...                    # base
class RetrievalError(MemoryIntelError): ...               # falha na recuperação
class WritebackError(MemoryIntelError): ...               # falha na persistência
class ContextTooLargeError(MemoryIntelError): ...         # assembled_text > limite
class NoSourcesAvailableError(MemoryIntelError): ...      # zero fontes para intent
class SimilarityError(MemoryIntelError): ...              # falha no cálculo de similaridade
class SafetyViolationError(MemoryIntelError): ...         # violação de safety rule
```

---

## 17. ARQUIVOS SUGERIDOS

```
src/memory_intel/               # P21 namespace
├── __init__.py                 # exports públicos
├── models.py                   # MemoryIntelConfig, MissionSimilarityResult, RetrievalResult, MemoryIntelMode
├── service.py                  # MemoryIntelligence (motor principal)
├── similarity.py               # find_similar_missions(), score calculation
├── safety.py                   # sanitize_context_text(), validate_safety_rules()
└── errors.py                   # MemoryIntelError + subclasses

tests/memory_intel/
├── __init__.py
├── test_models.py              # 20+ testes (config, similarity result, retrieval result)
├── test_service.py             # 30+ testes (retrieve, writeback, extract_patterns)
├── test_similarity.py          # 15+ testes (scoring, edge cases)
├── test_safety.py              # 10+ testes (sanitização, limites, safety rules)
└── test_integration_p20.py     # 10+ testes (P21 → P4 → ContextPack round-trip)

docs/memory_intel/
└── P21_MEMORY_INTELLIGENCE_SKELETON.md
```

**Total: 6 source + 5 test + 1 doc = 12 arquivos**

---

## 18. TEST STRATEGY

### Meta: ≥ 85 testes

| Arquivo | Testes | Foco |
|---|---|---|
| `test_models.py` | 20+ | MemoryIntelConfig, RetrievalResult, MissionSimilarityResult, MemoryIntelMode enum |
| `test_service.py` | 30+ | MemoryIntelligence.retrieve() com todos os 5 intents, writeback() com report real, extract_patterns(), _select_sources() para cada intent |
| `test_similarity.py` | 15+ | find_similar_missions() — mesmo intent, mesmo sector, tags overlap, mixed, zero matches, score bounds [0.0, 1.0] |
| `test_safety.py` | 10+ | sanitize_context_text() com text normal/longo/markdown/tags HTML, validate_safety_rules(), limites de hits e records |
| `test_integration_p20.py` | 10+ | P21.retrieve() → ContextPack → P21.writeback() round-trip com dados simulados do P20 |

### Comandos

```powershell
python -m pytest tests/memory_intel/ -q          # targeted ≥ 85
python -m pytest tests/ -q                         # full suite ≥ 4200
```

---

## 19. DRY-RUN STRATEGY

```python
class MemoryIntelligence:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def retrieve(self, intent: str, ...) -> RetrievalResult:
        # Query é sempre dry_run
        query = MemoryQuery.new(text=..., sources=..., dry_run=self.dry_run)
        
        # Retrieval é simulado (P4)
        result = self.planner.simulate_query(query)
        
        # ContextPack assembly é determinístico (sem randomness)
        pack = ContextPack.new(query.query_id)
        pack.assemble(result["hits"])
        
        return RetrievalResult(pack=pack, ...)

    def writeback(self, mission, report) -> MemoryWritePlan:
        # Write plan é sempre dry_run
        plan = self.planner.plan_memory_writeback(
            records, target_source="akasha", action="upsert"
        )
        # plan.is_dry_run = True (default do P4)
        # plan.requires_approval = True (default do P4)
        return plan
```

**Comportamento:**
- Retrieval: simulado, sem conexão real → sempre seguro
- Writeback: plano gerado, nunca executado → sempre seguro
- Nenhuma operação real de I/O além de CPU e memória RAM

---

## 20. FAILURE / RECOVERY

| Falha | Comportamento | Recovery |
|---|---|---|
| Nenhuma fonte disponível para intent | `NoSourcesAvailableError` → retorna RetrievalResult vazio com warning | P20 prossegue com contexto degradado |
| Query simulado retorna 0 hits | ContextPack.is_empty = True → warning | P20 usa apenas analytics + briefings |
| assembled_text > 2000 chars | `ContextTooLargeError` → _optimize_pack() remove hits "low" | Trunca até caber no limite |
| Writeback recebe report vazio | `WritebackError` → retorna WritePlan com 0 records + nota | Missão conclui sem writeback |
| Safety rule violada | `SafetyViolationError` → operação bloqueada | Log do erro, missão prossegue sem writeback |
| P4 indisponível (import quebra) | `RetrievalError` → P20 usa stubs como fallback | Degradação graciosa |

---

## 21. CRITÉRIOS DE ACEITE

- [ ] Namespace `src/memory_intel/` com 6 arquivos
- [ ] Testes ≥ 85 (targeted), todos passando
- [ ] Full suite ≥ 4200 passando, 0 novas falhas
- [ ] MemoryIntelligence.retrieve() funcional para 5 intents
- [ ] MemoryIntelligence.writeback() funcional com MissionReport
- [ ] find_similar_missions() com scoring correto (0.0-1.0)
- [ ] Sanitização de assembled_text (≤ 2000 chars, sem markdown perigoso)
- [ ] dry_run=True e approval_required=True em todas as operações
- [ ] Zero imports de módulos proibidos
- [ ] Zero toques em módulos existentes (P4, P20, etc.)
- [ ] Integração correta com MemoryPackPlanner (P4)
- [ ] RetrievalResult contém ContextPack + similares + patterns
- [ ] MissionMemoryRecord gerados com tags controladas
- [ ] Safety rules documentadas e testadas

---

## 22. RISCOS ARQUITETURAIS

| # | Risco | Impacto | Prob | Mitigação |
|---|---|---|---|---|
| R1 | P21 duplicar lógica do P4 | Médio — confusão de responsabilidade | Baixa | P21 só chama P4, nunca redefine modelos. P4 é source of truth dos modelos |
| R2 | ContextPack crescer e poluir prompt do Claude Code | Alto — piora qualidade das respostas | Média | Limite rígido de 2000 chars. Testes de tamanho no CI |
| R3 | Simulated retrieval gerar hits irrelevantes | Baixo — só afeta qualidade do contexto | Alta | Palavra-chave matching é frágil. Aceitável para skeleton. Melhorar com embeddings reais pós-MVP |
| R4 | P21 importar P20 criando ciclo | Crítico — import loop | Nula | P21 NUNCA importa P20. Tipos de P20 são passados como dict |
| R5 | MissionMemoryRecord acumular lixo (memory pollution) | Médio — degradação gradual | Média | Limite de 5 records/missão. Dedup. Review gate do operador |
| R6 | Similarity score ingênuo (keyword-based) não capturar semântica | Baixo — falso positivo/negativo | Alta | Aceitável para skeleton. Embeddings no futuro (Akasha/Qdrant) |
| R7 | knowledge_context.ContextPack vs memory_pack.ContextPack colisão de nomes | Baixo — confusão | Média | P21 sempre importa de memory_pack explicitamente. Não referenciar knowledge_context |

---

## 23. ORDEM RECOMENDADA DE IMPLEMENTAÇÃO

### Milestone 1: Models + Errors
- `models.py`, `errors.py`
- `test_models.py` — 20+ testes

### Milestone 2: Core Service — Retrieval
- `service.py` — MemoryIntelligence com retrieve(), retrieve_context(), _select_sources(), _build_query_text()
- `test_service.py` — 15+ testes (retrieval)

### Milestone 3: Similarity + Patterns
- `similarity.py` — find_similar_missions(), extract_patterns()
- Atualizar `service.py` — integrate similar missions into retrieve()
- `test_similarity.py` — 15+ testes

### Milestone 4: Writeback + Safety
- Atualizar `service.py` — writeback(), learn_from_step()
- `safety.py` — sanitize_context_text(), validate_safety_rules()
- `test_safety.py` — 10+ testes
- Completar `test_service.py` — 15+ testes (writeback)

### Milestone 5: Integration + Docs
- `__init__.py` — exports
- `test_integration_p20.py` — 10+ testes
- Skeleton doc
- Full suite validation

---

## 24. SE DEVE SER 1 FRENTE OU MÚLTIPLAS FRENTES

### VEREDITO: **1 frente única**

P21 é linear: `models → retrieval → similarity → writeback → safety → integration`. Cada milestone depende do anterior. Não há paralelismo interno.

| Argumento | Conclusão |
|---|---|
| Dependências internas | Sequenciais (similarity usa models, writeback usa retrieval + similarity) |
| Complexidade | Média-baixa (~500 linhas de lógica, 6 source files) |
| Riscos de merge | Altos se paralelizado (modelos compartilhados entre M2 e M3) |
| Tempo estimado | ~1 sessão Claude Code (5 milestones sequenciais) |

---

## VEREDITO FINAL

```
█████████████████████████████████████████████████████████████
█                                                         █
█   P21 MEMORY INTELLIGENCE                               █
█                                                         █
█   Tipo: Camada de inteligência contextual               █
█   Arquivos: 12 (6 source + 5 test + 1 doc)             █
█   Testes alvo: ≥ 85                                     █
█   Worktrees: 1 (única)                                  █
█   Ordem: Sequencial M1→M5                               █
█                                                         █
█   Stack:                                                █
█   P20 (omnis_supreme) → P21 (memory_intel) → P4         █
█   (memory_pack) → Akasha/Qdrant/Obsidian (externos)    █
█                                                         █
█   RISCO PRINCIPAL: Memory pollution                     █
█   MITIGAÇÃO: Limite 5 records/missão + review gate      █
█                                                         █
█████████████████████████████████████████████████████████████
```

---

## P21 DEVE SER FEITA ANTES OU JUNTO COM P22 CAPABILITY FORGE?

**Antes.** P21 é pré-requisito para o P22:

| Ordem | Módulo | Justificativa |
|---|---|---|
| **Agora** | P21 Memory Intelligence | P20 já tem stubs esperando P21. Sem P21, o Context Builder do P20 continua vazio. P21 faz o ciclo "aprender com passado → planejar melhor" funcionar |
| **Depois** | P22 Capability Forge Real | P22 precisa de contexto histórico (quais capabilities faltam? quais missões falharam por falta de capability?) que a P21 fornece. P22 sem P21 = forge cego |

---

## PRÓXIMOS PASSOS

1. Revisão desta arquitetura pelo operador
2. Aprovação
3. Criação de worktree única: `omnis-p21-memory-intel`
4. Implementação sequencial M1→M5
5. Merge --no-ff na master
6. Full suite ≥ 4200 testes
7. Tag `p21-memory-intel-complete-<date>`

---

*OMNIS Control Tower — P21 Memory Intelligence Architecture.*
*Aguardando revisão e aprovação do operador.*

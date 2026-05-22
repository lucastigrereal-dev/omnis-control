# OMNIS Observability Architecture

## Visao Geral

O OMNIS executa missoes. A camada de observability permite que ele se observe, se diagnostique e se recupere.

```
┌─────────────────────────────────────────────────────────┐
│                    OMNIS Observability                   │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │  EVENTS  │  │TELEMETRY │  │  TRACES  │  │ HEALTH  │ │
│  │  (bus)   │  │(provider)│  │(distrib) │  │ (score) │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │
│       │              │              │              │      │
│  ┌────┴──────────────┴──────────────┴──────────────┴───┐ │
│  │              Redis Streams (append-only)             │ │
│  │   omnis:events:missions | tasks | providers | ...    │ │
│  └────────────────────────┬────────────────────────────┘ │
│                           │                              │
│  ┌──────────┐  ┌──────────┴─────┐  ┌──────────────────┐ │
│  │ REPLAY   │  │    AUDIT       │  │    METRICS       │ │
│  │(mission) │  │ (append-only)  │  │  (runtime/SLO)   │ │
│  └──────────┘  └────────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Fluxo de Dados

```
Skill/Agent
    │
    ├─→ Tracer.start_span() ──→ TraceSpan (trace_id, span_id)
    │
    ├─→ TelemetryCollector.record_call() ──→ ProviderMetric
    │       └─→ EventBus.publish(STREAMS["providers"])
    │
    ├─→ RuntimeMetricsCollector.record() ──→ RuntimeMetric
    │
    ├─→ AuditLog.record() ──→ AuditEntry (append-only JSONL)
    │
    └─→ EventBus.publish() ──→ Redis Stream
            ├─→ Consumer: HealthScorer (atualiza health score)
            ├─→ Consumer: ReplayEngine (reconstroi estado)
            └─→ Consumer: Dead Letter Queue (eventos com falha)
```

## Componentes

### 1. Event Bus (Redis Streams)

**10 streams** — um por dominio:

| Stream | Eventos | Retencao |
|--------|---------|----------|
| `omnis:events:missions` | mission_started, mission_failed, mission_completed... | 100K |
| `omnis:events:tasks` | task_started, task_completed, task_failed... | 100K |
| `omnis:events:waves` | wave_started, wave_completed... | 100K |
| `omnis:events:providers` | provider_called, provider_failed... | 100K |
| `omnis:events:memory` | memory_retrieval, memory_stored... | 100K |
| `omnis:events:telemetry` | token_usage, latency_recorded... | 100K |
| `omnis:events:health` | health_check... | 100K |
| `omnis:events:anomalies` | anomaly_detected, hallucination_detected... | 100K |
| `omnis:events:audit` | todos os AuditEntry | 100K |
| `omnis:events:dead_letter` | eventos que falharam no processamento | 10K |

**Garantias:**
- Append-only: cada evento e escrito uma vez, nunca modificado
- Idempotencia: `idempotency_key` previne duplicatas
- Ordem total: `sequence` monotonicamente crescente
- Replay-safe: `xrange` permite ler do inicio para reconstrucao de estado

### 2. Telemetry (Provider Observability)

Rastreia cada chamada a providers externos:

```
record_call()
  ├── provider: "anthropic" | "openai" | "gemini"
  ├── model: "claude-opus-4-7"
  ├── tokens: {input, output, cache_read, cache_write}
  ├── latency: {duration_ms, ttfb_ms}
  ├── cost_usd: 0.023
  └── hallucination_score: 0.0-1.0
```

**Snapshot agrega:** total_calls, success_count, failure_count, total_tokens, total_cost, p95/p99 latency, hallucination_rate, retry_rate, provider_breakdown.

### 3. Distributed Tracing

Propagacao W3C Trace Context entre processos:

```
MISSION (trace_id: abc)
├── task_decomposer (span_id: d1, parent: null)
│   ├── parse_briefing (span_id: d2, parent: d1)
│   └── validate (span_id: d3, parent: d1)
├── parallel_runner (span_id: r1)
│   ├── squad_a (span_id: a1, parent: r1)
│   └── squad_b (span_id: b1, parent: r1)
└── result_reconciler (span_id: rec1)
```

Headers `traceparent` propagam contexto via env vars ou mensagens entre worktrees/agentes.

### 4. Health Score

Score composto ponderado:

```
total = sum(score_i * weight_i) / sum(weight_i)

Componentes:
├── event_bus      (w=0.25) — Redis connectivity
├── providers      (w=0.30) — success rate, latency
├── missions       (w=0.20) — success rate, error rate
├── resources      (w=0.15) — disk, memory
└── circuit_breakers (w=0.10) — open/closed status

Thresholds:
  >= 0.90 → HEALTHY
  >= 0.70 → DEGRADED
  >= 0.40 → UNHEALTHY
  < 0.40  → CRITICAL
```

**Anomaly Detection:**
- Score drop >15% em 3 medicoes → ANOMALY_DETECTED
- Provider failure rate >10% → ANOMALY_DETECTED
- Latency spike >200% baseline → ANOMALY_DETECTED
- Cost spike >300% baseline → ANOMALY_DETECTED

### 5. Runtime Metrics + SLO

8 SLIs canonicos:

| SLI | Target | Window |
|-----|--------|--------|
| mission_success_rate | 95% | 60min |
| task_success_rate | 98% | 15min |
| provider_availability | 99.5% | 5min |
| p95_latency_ms | 5000ms | 15min |
| event_bus_latency_ms | 500ms | 5min |
| health_score | 0.90 | 5min |
| cost_per_mission_usd | $1.00 | 60min |
| hallucination_rate | 2% | 30min |

### 6. Replay Engine

Reconstroi estado do sistema reprocessando eventos em ordem:

```
ReplayEngine.replay_mission(mission_id)
  ├── Le eventos do stream em sequencia
  ├── Reconstroi: missions, tasks, provider_calls, errors
  ├── Totaliza: token_total, cost_total
  └── Verifica determinismo: 2 replays identicos

ReplayAuditor.audit_stream(stream)
  ├── Detecta gaps na sequencia
  ├── Detecta duplicatas (idempotency_key)
  └── Report: complete/gaps/duplicates
```

### 7. Audit Log

Append-only, imutavel, JSONL:

```
data/audit/20260521.jsonl
  ├── {entry_id, timestamp, actor, action, resource, outcome, detail, ...}
  ├── {entry_id, timestamp, actor, action, resource, outcome, detail, ...}
  └── ...

Query: AuditLog.read_range(start, end, action=DECISION)
       AuditLog.get_mission_audit_trail(mission_id)
```

## Diagrama de Integracao

```
┌──────────────────────────────────────────────────┐
│                 OMNIS Runtime                     │
│                                                   │
│  ┌─────────┐    ┌──────────┐    ┌─────────────┐  │
│  │ Skill   │───→│ Tracer   │───→│ Telemetry   │  │
│  │Executor │    │(spans)   │    │Collector    │  │
│  └────┬────┘    └──────────┘    └──────┬──────┘  │
│       │                                │          │
│       │         ┌──────────┐          │          │
│       └────────→│EventBus  │←─────────┘          │
│                 │(Redis)   │                      │
│                 └────┬─────┘                      │
│                      │                            │
│       ┌──────────────┼──────────────┐             │
│       │              │              │             │
│  ┌────┴────┐   ┌────┴────┐   ┌────┴────┐        │
│  │Health   │   │Replay   │   │Audit    │        │
│  │Scorer   │   │Engine   │   │Log      │        │
│  └────┬────┘   └────┬────┘   └────┬────┘        │
│       │              │              │             │
│  ┌────┴────┐   ┌────┴────┐   ┌────┴────┐        │
│  │Metrics  │   │Metric   │   │JSONL    │        │
│  │Collector│   │Snapshot │   │Files    │        │
│  └─────────┘   └─────────┘   └─────────┘        │
└──────────────────────────────────────────────────┘
         │              │              │
    ┌────┴────┐    ┌────┴────┐   ┌────┴────┐
    │ KRATOS  │    │ Akasha  │   │Data Dir │
    │ Cockpit │    │ Memory  │   │on Disk  │
    └─────────┘    └─────────┘   └─────────┘
```

## Eventos Definidos (37 tipos)

```
MISSION:  started, failed, completed, cancelled, paused, resumed
TASK:     started, completed, failed, skipped
WAVE:     started, completed, failed
RETRY:    triggered, exhausted
ROLLBACK: triggered, completed
CIRCUIT:  breaker_opened, breaker_closed
PROVIDER: called, failed, recovered
MEMORY:   retrieval, stored, evicted
RESOURCE: token_usage, cost_incurred, latency_recorded
QUALITY:  hallucination_detected, hallucination_resolved,
          guardrail_triggered
APPROVAL: requested, resolved
SYSTEM:   health_check, anomaly_detected, checkpoint_created,
          evidence_recorded
```

## Validacao — Contratos

1. **Replay possivel** — Eventos append-only com sequence number + timestamp wall-clock garantem reconstrucao deterministica.
2. **Traceability completa** — Toda operacao tem trace_id + span_id + parent_span_id. W3C Trace Context propaga entre processos.
3. **Metricas coerentes** — SLOs com janela configurada. Aggregacoes com percentile (p95/p99). Burn rate tracking.
4. **Health score consistente** — Media ponderada com thresholds fixos. Anomaly detection com rolling baseline.
5. **Audit safe** — Append-only JSONL. Nunca deleta ou modifica. Replayavel para compliance.
6. **Structured logs** — Tudo e EventEnvelope (Pydantic) serializado como JSON. Nada de string logs.

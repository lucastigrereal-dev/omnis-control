"""P25 Multi-Model Orchestration — models."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


# ── ID / timestamp helpers ──────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ── Task complexity constants ───────────────────────────────────────────────

COMPLEXITY_LOW = "low"
COMPLEXITY_MEDIUM = "medium"
COMPLEXITY_HIGH = "high"
COMPLEXITY_CRITICAL = "critical"

VALID_COMPLEXITIES = {COMPLEXITY_LOW, COMPLEXITY_MEDIUM, COMPLEXITY_HIGH, COMPLEXITY_CRITICAL}

# ── Provider constants ──────────────────────────────────────────────────────

PROVIDER_ANTHROPIC = "anthropic"
PROVIDER_OPENAI = "openai"
PROVIDER_GROQ = "groq"
PROVIDER_OLLAMA = "ollama"
PROVIDER_MOCK = "mock"

VALID_PROVIDERS = {PROVIDER_ANTHROPIC, PROVIDER_OPENAI, PROVIDER_GROQ, PROVIDER_OLLAMA, PROVIDER_MOCK}

# ── Capability constants ────────────────────────────────────────────────────

CAPABILITY_TEXT = "text"
CAPABILITY_CODE = "code"
CAPABILITY_ANALYSIS = "analysis"
CAPABILITY_PLANNING = "planning"
CAPABILITY_CLASSIFICATION = "classification"
CAPABILITY_SUMMARIZATION = "summarization"

# ── Routing strategy ────────────────────────────────────────────────────────

STRATEGY_COST_OPTIMAL = "cost_optimal"
STRATEGY_PERFORMANCE = "performance"
STRATEGY_FALLBACK = "fallback"

VALID_STRATEGIES = {STRATEGY_COST_OPTIMAL, STRATEGY_PERFORMANCE, STRATEGY_FALLBACK}


# ── ModelConfig ─────────────────────────────────────────────────────────────

@dataclass
class ModelConfig:
    model_id: str
    name: str
    provider: str
    capabilities: list[str] = field(default_factory=list)
    cost_per_1k_tokens: float = 0.0
    avg_latency_ms: int = 0
    max_tokens: int = 4096
    priority: int = 1
    enabled: bool = True
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        name: str,
        provider: str,
        capabilities: Optional[list[str]] = None,
        cost_per_1k_tokens: float = 0.0,
        avg_latency_ms: int = 0,
        max_tokens: int = 4096,
        priority: int = 1,
        enabled: bool = True,
    ) -> "ModelConfig":
        if provider not in VALID_PROVIDERS:
            raise ValueError(f"Invalid provider: {provider!r}. Must be one of {sorted(VALID_PROVIDERS)}")
        return cls(
            model_id=_new_id("mm"),
            name=name,
            provider=provider,
            capabilities=capabilities or [],
            cost_per_1k_tokens=cost_per_1k_tokens,
            avg_latency_ms=avg_latency_ms,
            max_tokens=max_tokens,
            priority=priority,
            enabled=enabled,
        )

    def to_dict(self) -> dict:
        return {
            "model_id": self.model_id,
            "name": self.name,
            "provider": self.provider,
            "capabilities": self.capabilities,
            "cost_per_1k_tokens": self.cost_per_1k_tokens,
            "avg_latency_ms": self.avg_latency_ms,
            "max_tokens": self.max_tokens,
            "priority": self.priority,
            "enabled": self.enabled,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ModelConfig":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    @property
    def is_cheap(self) -> bool:
        return self.cost_per_1k_tokens <= 0.005

    @property
    def is_fast(self) -> bool:
        return self.avg_latency_ms <= 500


# ── TaskClass ───────────────────────────────────────────────────────────────

@dataclass
class TaskClass:
    """Classification of a task for routing purposes."""
    task_id: str
    task_type: str
    complexity: str
    risk_level: str
    requires_creativity: bool = False
    requires_precision: bool = False
    min_capabilities: list[str] = field(default_factory=list)
    max_cost_usd: float = 0.10
    max_latency_ms: int = 5000
    classified_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        task_type: str,
        complexity: str = COMPLEXITY_MEDIUM,
        risk_level: str = "low",
        requires_creativity: bool = False,
        requires_precision: bool = False,
        min_capabilities: Optional[list[str]] = None,
        max_cost_usd: float = 0.10,
        max_latency_ms: int = 5000,
    ) -> "TaskClass":
        if complexity not in VALID_COMPLEXITIES:
            raise ValueError(f"Invalid complexity: {complexity!r}")
        return cls(
            task_id=_new_id("tc"),
            task_type=task_type,
            complexity=complexity,
            risk_level=risk_level,
            requires_creativity=requires_creativity,
            requires_precision=requires_precision,
            min_capabilities=min_capabilities or [],
            max_cost_usd=max_cost_usd,
            max_latency_ms=max_latency_ms,
        )

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "complexity": self.complexity,
            "risk_level": self.risk_level,
            "requires_creativity": self.requires_creativity,
            "requires_precision": self.requires_precision,
            "min_capabilities": self.min_capabilities,
            "max_cost_usd": self.max_cost_usd,
            "max_latency_ms": self.max_latency_ms,
            "classified_at": self.classified_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TaskClass":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# ── RoutingRequest ──────────────────────────────────────────────────────────

@dataclass
class RoutingRequest:
    request_id: str
    task: TaskClass
    prompt: str
    context: dict = field(default_factory=dict)
    preferred_provider: str = ""
    dry_run: bool = True
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        task: TaskClass,
        prompt: str = "",
        context: Optional[dict] = None,
        preferred_provider: str = "",
        dry_run: bool = True,
    ) -> "RoutingRequest":
        return cls(
            request_id=_new_id("mrr"),
            task=task,
            prompt=prompt,
            context=context or {},
            preferred_provider=preferred_provider,
            dry_run=dry_run,
        )

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "task": self.task.to_dict(),
            "prompt": self.prompt,
            "context": self.context,
            "preferred_provider": self.preferred_provider,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RoutingRequest":
        task_data = d.get("task", {})
        if isinstance(task_data, dict) and task_data.get("task_id"):
            task = TaskClass.from_dict(task_data)
        else:
            task = TaskClass.new("unknown")
        return cls(
            request_id=d.get("request_id", _new_id("mrr")),
            task=task,
            prompt=d.get("prompt", ""),
            context=d.get("context", {}),
            preferred_provider=d.get("preferred_provider", ""),
            dry_run=d.get("dry_run", True),
            created_at=d.get("created_at", ""),
        )


# ── RoutingDecision ─────────────────────────────────────────────────────────

@dataclass
class RoutingDecision:
    decision_id: str
    request_id: str
    selected_model: ModelConfig
    fallback_chain: list[str] = field(default_factory=list)
    reason: str = ""
    estimated_cost_usd: float = 0.0
    estimated_tokens: int = 0
    strategy: str = STRATEGY_COST_OPTIMAL
    is_dry_run: bool = True
    decided_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        request_id: str,
        selected_model: ModelConfig,
        fallback_chain: Optional[list[str]] = None,
        reason: str = "",
        estimated_cost_usd: float = 0.0,
        estimated_tokens: int = 0,
        strategy: str = STRATEGY_COST_OPTIMAL,
        is_dry_run: bool = True,
    ) -> "RoutingDecision":
        return cls(
            decision_id=_new_id("mrd"),
            request_id=request_id,
            selected_model=selected_model,
            fallback_chain=fallback_chain or [],
            reason=reason,
            estimated_cost_usd=estimated_cost_usd,
            estimated_tokens=estimated_tokens,
            strategy=strategy,
            is_dry_run=is_dry_run,
        )

    def to_dict(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "request_id": self.request_id,
            "selected_model": self.selected_model.to_dict(),
            "fallback_chain": self.fallback_chain,
            "reason": self.reason,
            "estimated_cost_usd": self.estimated_cost_usd,
            "estimated_tokens": self.estimated_tokens,
            "strategy": self.strategy,
            "is_dry_run": self.is_dry_run,
            "decided_at": self.decided_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RoutingDecision":
        model_data = d.get("selected_model", {})
        if isinstance(model_data, dict) and model_data.get("model_id"):
            selected_model = ModelConfig.from_dict(model_data)
        else:
            selected_model = ModelConfig.new("unknown", PROVIDER_MOCK)
        return cls(
            decision_id=d.get("decision_id", _new_id("mrd")),
            request_id=d.get("request_id", ""),
            selected_model=selected_model,
            fallback_chain=d.get("fallback_chain", []),
            reason=d.get("reason", ""),
            estimated_cost_usd=d.get("estimated_cost_usd", 0.0),
            estimated_tokens=d.get("estimated_tokens", 0),
            strategy=d.get("strategy", STRATEGY_COST_OPTIMAL),
            is_dry_run=d.get("is_dry_run", True),
            decided_at=d.get("decided_at", ""),
        )

    @property
    def has_fallback(self) -> bool:
        return len(self.fallback_chain) > 0

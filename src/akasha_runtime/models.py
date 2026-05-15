from dataclasses import dataclass, field
from typing import Optional
from uuid import uuid4


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AkashaConnectionConfig:
    config_id: str = field(default_factory=lambda: _new_id("akc"))
    host: str = "localhost"
    port: int = 5432
    db_name: str = "akasha"
    user: str = ""
    pool_size: int = 5
    timeout_seconds: int = 10
    dry_run: bool = True
    enabled: bool = False
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "config_id": self.config_id,
            "host": self.host,
            "port": self.port,
            "db_name": self.db_name,
            "user": self.user,
            "pool_size": self.pool_size,
            "timeout_seconds": self.timeout_seconds,
            "dry_run": self.dry_run,
            "enabled": self.enabled,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AkashaConnectionConfig":
        return cls(
            config_id=data.get("config_id", ""),
            host=data.get("host", "localhost"),
            port=data.get("port", 5432),
            db_name=data.get("db_name", "akasha"),
            user=data.get("user", ""),
            pool_size=data.get("pool_size", 5),
            timeout_seconds=data.get("timeout_seconds", 10),
            dry_run=data.get("dry_run", True),
            enabled=data.get("enabled", False),
            metadata=data.get("metadata", {}),
        )


@dataclass
class AkashaConnectionStatus:
    status_id: str = field(default_factory=lambda: _new_id("aks"))
    config_id: str = ""
    connected: bool = False
    latency_ms: float = 0.0
    pool_available: int = 0
    pool_total: int = 0
    error_message: str = ""
    checked_at: str = field(default_factory=_now_iso)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "status_id": self.status_id,
            "config_id": self.config_id,
            "connected": self.connected,
            "latency_ms": self.latency_ms,
            "pool_available": self.pool_available,
            "pool_total": self.pool_total,
            "error_message": self.error_message,
            "checked_at": self.checked_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AkashaConnectionStatus":
        return cls(
            status_id=data.get("status_id", ""),
            config_id=data.get("config_id", ""),
            connected=data.get("connected", False),
            latency_ms=data.get("latency_ms", 0.0),
            pool_available=data.get("pool_available", 0),
            pool_total=data.get("pool_total", 0),
            error_message=data.get("error_message", ""),
            checked_at=data.get("checked_at", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class AkashaHealthResult:
    result_id: str = field(default_factory=lambda: _new_id("akh"))
    config_id: str = ""
    healthy: bool = False
    connection_status: Optional[AkashaConnectionStatus] = None
    checks: dict[str, bool] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    checked_at: str = field(default_factory=_now_iso)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "config_id": self.config_id,
            "healthy": self.healthy,
            "connection_status": self.connection_status.to_dict() if self.connection_status else None,
            "checks": self.checks,
            "errors": self.errors,
            "checked_at": self.checked_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AkashaHealthResult":
        cs = data.get("connection_status")
        return cls(
            result_id=data.get("result_id", ""),
            config_id=data.get("config_id", ""),
            healthy=data.get("healthy", False),
            connection_status=AkashaConnectionStatus.from_dict(cs) if cs else None,
            checks=data.get("checks", {}),
            errors=data.get("errors", []),
            checked_at=data.get("checked_at", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class AkashaWritePolicy:
    policy_id: str = field(default_factory=lambda: _new_id("akp"))
    name: str = ""
    allowed_collections: list[str] = field(default_factory=list)
    max_batch_size: int = 100
    require_embedding: bool = True
    dedup_enabled: bool = True
    dedup_keys: list[str] = field(default_factory=lambda: ["content_hash"])
    require_approval: bool = False
    dry_run: bool = True
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "allowed_collections": self.allowed_collections,
            "max_batch_size": self.max_batch_size,
            "require_embedding": self.require_embedding,
            "dedup_enabled": self.dedup_enabled,
            "dedup_keys": self.dedup_keys,
            "require_approval": self.require_approval,
            "dry_run": self.dry_run,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AkashaWritePolicy":
        return cls(
            policy_id=data.get("policy_id", ""),
            name=data.get("name", ""),
            allowed_collections=data.get("allowed_collections", []),
            max_batch_size=data.get("max_batch_size", 100),
            require_embedding=data.get("require_embedding", True),
            dedup_enabled=data.get("dedup_enabled", True),
            dedup_keys=data.get("dedup_keys", ["content_hash"]),
            require_approval=data.get("require_approval", False),
            dry_run=data.get("dry_run", True),
            metadata=data.get("metadata", {}),
        )


@dataclass
class AkashaMemoryDocument:
    doc_id: str = field(default_factory=lambda: _new_id("akd"))
    collection: str = ""
    content: str = ""
    source_system: str = "omnis"
    event_type: str = ""
    embedding: list[float] = field(default_factory=list)
    content_hash: str = ""
    metadata: dict = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "collection": self.collection,
            "content": self.content,
            "source_system": self.source_system,
            "event_type": self.event_type,
            "embedding": self.embedding,
            "content_hash": self.content_hash,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AkashaMemoryDocument":
        return cls(
            doc_id=data.get("doc_id", ""),
            collection=data.get("collection", ""),
            content=data.get("content", ""),
            source_system=data.get("source_system", "omnis"),
            event_type=data.get("event_type", ""),
            embedding=data.get("embedding", []),
            content_hash=data.get("content_hash", ""),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", ""),
        )


@dataclass
class AkashaEventMapping:
    mapping_id: str = field(default_factory=lambda: _new_id("akm"))
    event_type: str = ""
    target_collection: str = ""
    priority: int = 0
    require_approval: bool = False
    transform_hint: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "mapping_id": self.mapping_id,
            "event_type": self.event_type,
            "target_collection": self.target_collection,
            "priority": self.priority,
            "require_approval": self.require_approval,
            "transform_hint": self.transform_hint,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AkashaEventMapping":
        return cls(
            mapping_id=data.get("mapping_id", ""),
            event_type=data.get("event_type", ""),
            target_collection=data.get("target_collection", ""),
            priority=data.get("priority", 0),
            require_approval=data.get("require_approval", False),
            transform_hint=data.get("transform_hint", ""),
            metadata=data.get("metadata", {}),
        )

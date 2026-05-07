"""State machine de publicacao — 9 estados, transicoes validadas."""
from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import uuid
import logging

logger = logging.getLogger("omnis.publisher.statemachine")


class ContentStatus(str, Enum):
    IDEA = "idea"
    BRIEF = "brief"
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    QUEUED = "queued"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"


ALLOWED_TRANSITIONS: Dict[ContentStatus, List[ContentStatus]] = {
    ContentStatus.IDEA: [ContentStatus.BRIEF, ContentStatus.FAILED],
    ContentStatus.BRIEF: [ContentStatus.DRAFT, ContentStatus.IDEA, ContentStatus.FAILED],
    ContentStatus.DRAFT: [ContentStatus.REVIEW, ContentStatus.BRIEF, ContentStatus.FAILED],
    ContentStatus.REVIEW: [ContentStatus.APPROVED, ContentStatus.DRAFT, ContentStatus.FAILED],
    ContentStatus.APPROVED: [ContentStatus.QUEUED, ContentStatus.DRAFT],
    ContentStatus.QUEUED: [ContentStatus.PUBLISHING, ContentStatus.FAILED],
    ContentStatus.PUBLISHING: [ContentStatus.PUBLISHED, ContentStatus.FAILED],
    ContentStatus.PUBLISHED: [],
    ContentStatus.FAILED: [ContentStatus.QUEUED],
}


class InvalidTransitionError(Exception):
    pass


@dataclass
class ContentContext:
    """Estado acumulado de um item ao longo do pipeline."""
    content_id: str
    title: str
    account_handle: str = ""
    status: ContentStatus = ContentStatus.IDEA
    body: Optional[str] = None
    caption: Optional[str] = None
    hashtags: List[str] = field(default_factory=list)
    media_urls: List[str] = field(default_factory=list)
    format: str = "post"
    scheduled_at: Optional[datetime] = None
    idempotency_key: str = field(default_factory=lambda: str(uuid.uuid4()))
    retry_count: int = 0
    max_retries: int = 3
    error_log: List[Dict[str, Any]] = field(default_factory=list)
    transitions: List[Dict[str, Any]] = field(default_factory=list)

    def transition_to(
        self,
        new_status: ContentStatus,
        actor: str = "system",
        reason: str = "",
        payload: Optional[Dict] = None,
    ) -> ContentContext:
        allowed = ALLOWED_TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise InvalidTransitionError(
                f"Transicao invalida: {self.status} -> {new_status}. "
                f"Permitidas: {[s.value for s in allowed]}"
            )
        transition = {
            "from": self.status.value,
            "to": new_status.value,
            "actor": actor,
            "reason": reason,
            "payload": payload or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.transitions.append(transition)
        logger.info(
            "content_transition",
            extra={
                "content_id": self.content_id,
                "from_status": self.status.value,
                "to_status": new_status.value,
                "actor": actor,
            },
        )
        self.status = new_status
        return self

    def record_error(self, error: str, stage: str) -> ContentContext:
        self.error_log.append({
            "stage": stage,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "retry_count": self.retry_count,
        })
        self.retry_count += 1
        return self

    @property
    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries

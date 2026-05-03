"""
Status enum com máquina de estados para assets de vídeo.

Transições válidas:
  inbox ──────────► triaged ──► caption_ready ──► approved ──► scheduled ──► published
   │                  │              │               │
   └──► rejected ─────┴──────────────┴───────────────┘
        │
        └──► archived (terminal)
        ──► inbox (reativar)
"""

from enum import Enum


class AssetStatus(str, Enum):
    """Status possível de um asset de vídeo."""

    INBOX = "inbox"
    TRIAGED = "triaged"
    CAPTION_READY = "caption_ready"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    REJECTED = "rejected"
    ARCHIVED = "archived"

    def can_transition_to(self, target: "AssetStatus") -> bool:
        return target in _TRANSITIONS.get(self, set())

    def is_terminal(self) -> bool:
        return self in (AssetStatus.PUBLISHED, AssetStatus.ARCHIVED)

    def is_active(self) -> bool:
        return self not in (AssetStatus.REJECTED, AssetStatus.ARCHIVED)


_TRANSITIONS: dict[AssetStatus, set[AssetStatus]] = {
    AssetStatus.INBOX: {AssetStatus.TRIAGED, AssetStatus.REJECTED},
    AssetStatus.TRIAGED: {AssetStatus.CAPTION_READY, AssetStatus.REJECTED},
    AssetStatus.CAPTION_READY: {AssetStatus.APPROVED, AssetStatus.REJECTED},
    AssetStatus.APPROVED: {AssetStatus.SCHEDULED, AssetStatus.REJECTED},
    AssetStatus.SCHEDULED: {AssetStatus.PUBLISHED, AssetStatus.INBOX},
    AssetStatus.PUBLISHED: set(),  # terminal
    AssetStatus.REJECTED: {AssetStatus.INBOX, AssetStatus.ARCHIVED},
    AssetStatus.ARCHIVED: set(),  # terminal
}

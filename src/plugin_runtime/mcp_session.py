"""W153 — MCP Session Manager (tracks active MCP connections, mock-first)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .models import _new_id, _now_iso


SESSION_ACTIVE = "active"
SESSION_CLOSED = "closed"
SESSION_EXPIRED = "expired"


@dataclass
class McpSession:
    session_id: str
    plugin_id: str
    status: str = SESSION_ACTIVE
    call_count: int = 0
    created_at: str = field(default_factory=_now_iso)
    closed_at: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    @classmethod
    def new(cls, plugin_id: str, metadata: Optional[dict] = None) -> "McpSession":
        return cls(
            session_id=_new_id("sess"),
            plugin_id=plugin_id,
            metadata=metadata or {},
        )

    def is_active(self) -> bool:
        return self.status == SESSION_ACTIVE

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "plugin_id": self.plugin_id,
            "status": self.status,
            "call_count": self.call_count,
            "created_at": self.created_at,
            "closed_at": self.closed_at,
            "metadata": self.metadata,
        }


class McpSessionManager:
    """Tracks and manages MCP plugin sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, McpSession] = {}

    def open(self, plugin_id: str, metadata: Optional[dict] = None) -> McpSession:
        sess = McpSession.new(plugin_id, metadata=metadata)
        self._sessions[sess.session_id] = sess
        return sess

    def close(self, session_id: str) -> bool:
        sess = self._sessions.get(session_id)
        if sess is None:
            return False
        sess.status = SESSION_CLOSED
        sess.closed_at = _now_iso()
        return True

    def expire(self, session_id: str) -> bool:
        sess = self._sessions.get(session_id)
        if sess is None:
            return False
        sess.status = SESSION_EXPIRED
        return True

    def record_call(self, session_id: str) -> bool:
        sess = self._sessions.get(session_id)
        if sess is None or not sess.is_active():
            return False
        sess.call_count += 1
        return True

    def get(self, session_id: str) -> Optional[McpSession]:
        return self._sessions.get(session_id)

    def active_sessions(self) -> list[McpSession]:
        return [s for s in self._sessions.values() if s.is_active()]

    def sessions_for_plugin(self, plugin_id: str) -> list[McpSession]:
        return [s for s in self._sessions.values() if s.plugin_id == plugin_id]

    def count(self) -> int:
        return len(self._sessions)

"""Knowledge + Context Pack models."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class KnowledgeEntry:
    entry_id: str
    title: str
    content: str
    source: str            # "manual" | "akasha" | "library"
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "tags": self.tags,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "KnowledgeEntry":
        return cls(**data)


@dataclass
class KnowledgePack:
    pack_id: str
    name: str
    description: str
    tags: list[str] = field(default_factory=list)
    entries: list[KnowledgeEntry] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(cls, name: str, description: str = "", tags: Optional[list[str]] = None) -> "KnowledgePack":
        return cls(
            pack_id=f"kp_{uuid.uuid4().hex[:8]}",
            name=name,
            description=description,
            tags=tags or [],
        )

    def entry_count(self) -> int:
        return len(self.entries)

    def to_dict(self) -> dict:
        return {
            "pack_id": self.pack_id,
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "entries": [e.to_dict() for e in self.entries],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "KnowledgePack":
        data = dict(data)
        entries_raw = data.pop("entries", [])
        obj = cls(**data)
        obj.entries = [KnowledgeEntry.from_dict(e) for e in entries_raw]
        return obj


@dataclass
class ContextFact:
    key: str
    value: str
    category: str = "general"

    def to_dict(self) -> dict:
        return {"key": self.key, "value": self.value, "category": self.category}

    @classmethod
    def from_dict(cls, data: dict) -> "ContextFact":
        return cls(**data)


@dataclass
class ContextPack:
    context_id: str
    account_handle: str
    display_name: str
    facts: list[ContextFact] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    tone: str = "casual"
    language: str = "pt-BR"
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(cls, account_handle: str, display_name: str, **kwargs) -> "ContextPack":
        return cls(
            context_id=f"ctx_{uuid.uuid4().hex[:8]}",
            account_handle=account_handle.lstrip("@").lower(),
            display_name=display_name,
            **kwargs,
        )

    def get_fact(self, key: str) -> Optional[str]:
        for f in self.facts:
            if f.key == key:
                return f.value
        return None

    def set_fact(self, key: str, value: str, category: str = "general") -> None:
        for f in self.facts:
            if f.key == key:
                f.value = value
                f.category = category
                return
        self.facts.append(ContextFact(key=key, value=value, category=category))

    def to_dict(self) -> dict:
        return {
            "context_id": self.context_id,
            "account_handle": self.account_handle,
            "display_name": self.display_name,
            "facts": [f.to_dict() for f in self.facts],
            "topics": self.topics,
            "tone": self.tone,
            "language": self.language,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ContextPack":
        data = dict(data)
        facts_raw = data.pop("facts", [])
        obj = cls(**data)
        obj.facts = [ContextFact.from_dict(f) for f in facts_raw]
        return obj

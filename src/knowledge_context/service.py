"""Knowledge + Context Pack service — JSONL persistence."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.knowledge_context.models import KnowledgePack, KnowledgeEntry, ContextPack, ContextFact

PACKS_LOG = Path("data/knowledge_packs.jsonl")
CONTEXT_LOG = Path("data/context_packs.jsonl")


class PackNotFoundError(ValueError):
    pass


class ContextNotFoundError(ValueError):
    pass


class ValidationError(ValueError):
    pass


def _load_jsonl(path: Path, cls) -> list:
    if not path.exists():
        return []
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                items.append(cls.from_dict(json.loads(line)))
            except Exception:
                continue
    return items


def _save_jsonl(path: Path, items: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Knowledge Packs ──────────────────────────────────────────────────────────

def create_pack(
    name: str,
    description: str = "",
    tags: Optional[list[str]] = None,
    log_path: Path = None,
) -> KnowledgePack:
    if log_path is None:
        log_path = PACKS_LOG
    if not name.strip():
        raise ValidationError("name cannot be empty")
    pack = KnowledgePack.new(name=name, description=description, tags=tags or [])
    packs = _load_jsonl(log_path, KnowledgePack)
    packs.append(pack)
    _save_jsonl(log_path, packs)
    return pack


def add_entry(
    pack_id: str,
    title: str,
    content: str,
    source: str = "manual",
    tags: Optional[list[str]] = None,
    log_path: Path = None,
) -> KnowledgePack:
    if log_path is None:
        log_path = PACKS_LOG
    packs = _load_jsonl(log_path, KnowledgePack)
    pack = None
    for p in packs:
        if p.pack_id == pack_id or p.pack_id.startswith(pack_id):
            pack = p
            break
    if not pack:
        raise PackNotFoundError(f"Pack '{pack_id}' not found")
    entry = KnowledgeEntry(
        entry_id=f"ke_{uuid.uuid4().hex[:8]}",
        title=title,
        content=content,
        source=source,
        tags=tags or [],
    )
    pack.entries.append(entry)
    pack.updated_at = _now()
    _save_jsonl(log_path, packs)
    return pack


def list_packs(tag: Optional[str] = None, log_path: Path = None) -> list[KnowledgePack]:
    if log_path is None:
        log_path = PACKS_LOG
    packs = _load_jsonl(log_path, KnowledgePack)
    if tag:
        packs = [p for p in packs if tag in p.tags]
    return packs


def get_pack(pack_id: str, log_path: Path = None) -> KnowledgePack:
    if log_path is None:
        log_path = PACKS_LOG
    packs = _load_jsonl(log_path, KnowledgePack)
    for p in packs:
        if p.pack_id == pack_id or p.pack_id.startswith(pack_id):
            return p
    raise PackNotFoundError(f"Pack '{pack_id}' not found")


# ── Context Packs ────────────────────────────────────────────────────────────

def set_context(
    account_handle: str,
    display_name: str,
    tone: str = "casual",
    language: str = "pt-BR",
    topics: Optional[list[str]] = None,
    log_path: Path = None,
) -> ContextPack:
    if log_path is None:
        log_path = CONTEXT_LOG
    handle = account_handle.lstrip("@").lower()
    contexts = _load_jsonl(log_path, ContextPack)
    existing = next((c for c in contexts if c.account_handle == handle), None)
    if existing:
        existing.display_name = display_name
        existing.tone = tone
        existing.language = language
        if topics is not None:
            existing.topics = topics
        existing.updated_at = _now()
        _save_jsonl(log_path, contexts)
        return existing
    ctx = ContextPack.new(
        account_handle=handle,
        display_name=display_name,
        tone=tone,
        language=language,
        topics=topics or [],
    )
    contexts.append(ctx)
    _save_jsonl(log_path, contexts)
    return ctx


def set_context_fact(
    account_handle: str,
    key: str,
    value: str,
    category: str = "general",
    log_path: Path = None,
) -> ContextPack:
    if log_path is None:
        log_path = CONTEXT_LOG
    handle = account_handle.lstrip("@").lower()
    contexts = _load_jsonl(log_path, ContextPack)
    ctx = next((c for c in contexts if c.account_handle == handle), None)
    if not ctx:
        raise ContextNotFoundError(f"Context for '@{handle}' not found — create with context-set first")
    ctx.set_fact(key, value, category)
    ctx.updated_at = _now()
    _save_jsonl(log_path, contexts)
    return ctx


def get_context(account_handle: str, log_path: Path = None) -> ContextPack:
    if log_path is None:
        log_path = CONTEXT_LOG
    handle = account_handle.lstrip("@").lower()
    contexts = _load_jsonl(log_path, ContextPack)
    found = next((c for c in contexts if c.account_handle == handle), None)
    if not found:
        raise ContextNotFoundError(f"Context for '@{handle}' not found")
    return found


def list_contexts(log_path: Path = None) -> list[ContextPack]:
    if log_path is None:
        log_path = CONTEXT_LOG
    return _load_jsonl(log_path, ContextPack)

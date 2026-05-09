"""Knowledge + Context Pack — unified knowledge management."""
from src.knowledge_context.service import (
    create_pack, add_entry, list_packs, get_pack,
    set_context, set_context_fact, get_context, list_contexts,
)

__all__ = [
    "create_pack", "add_entry", "list_packs", "get_pack",
    "set_context", "set_context_fact", "get_context", "list_contexts",
]

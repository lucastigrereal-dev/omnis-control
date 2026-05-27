"""Indexa notas Obsidian no Qdrant. Rodar overnight."""
from __future__ import annotations
import os
import time
from pathlib import Path
from typing import Optional

OBSIDIAN_PATH = Path(os.getenv("OBSIDIAN_VAULT_PATH", r"C:/Users/lucas/Obsidian"))
BATCH_SIZE = 50
SKIP_FOLDERS = {".obsidian", ".trash", "templates", ".git"}
MIN_CONTENT_LEN = 100


def extract_tags(content: str) -> list[str]:
    """Extrai tags do frontmatter YAML simples."""
    tags = []
    if content.startswith("---"):
        try:
            end = content.index("---", 3)
            frontmatter = content[3:end]
            for line in frontmatter.splitlines():
                if line.strip().startswith("tags:"):
                    raw = line.split(":", 1)[1].strip()
                    tags = [t.strip().strip("-").strip() for t in raw.split(",") if t.strip()]
        except (ValueError, IndexError):
            pass
    return tags


def index_vault(
    vault_path: Optional[Path] = None,
    dry_run: bool = False,
    limit: Optional[int] = None,
) -> dict:
    """
    Indexa notas Obsidian no Qdrant.

    Args:
        vault_path: caminho do vault (default: OBSIDIAN_PATH)
        dry_run: se True, conta notas sem indexar
        limit: limita número de notas (útil para testes)

    Returns:
        {"indexed": N, "skipped": N, "errors": N, "total": N}
    """
    from src.memory.memory_client import OmnisMemoryClient

    path = vault_path or OBSIDIAN_PATH

    if not path.exists():
        return {
            "indexed": 0,
            "skipped": 0,
            "errors": 0,
            "total": 0,
            "note": f"Vault não encontrado: {path}",
        }

    notes = [
        p for p in path.rglob("*.md")
        if not any(skip in p.parts for skip in SKIP_FOLDERS)
    ]

    if limit:
        notes = notes[:limit]

    if dry_run:
        return {"indexed": 0, "skipped": 0, "errors": 0, "total": len(notes), "dry_run": True}

    client = OmnisMemoryClient()
    indexed = 0
    skipped = 0
    errors = 0

    for i, note_path in enumerate(notes):
        try:
            content = note_path.read_text(encoding="utf-8", errors="replace")
            if len(content) < MIN_CONTENT_LEN:
                skipped += 1
                continue

            tags = extract_tags(content)
            client.remember(
                text=content[:2000],
                collection="obsidian_notes",
                payload={
                    "path": str(note_path.relative_to(path)),
                    "tags": tags,
                    "modified": note_path.stat().st_mtime,
                },
            )
            indexed += 1

            if i % BATCH_SIZE == 0 and i > 0:
                time.sleep(0.5)

        except Exception:
            errors += 1

    return {"indexed": indexed, "skipped": skipped, "errors": errors, "total": len(notes)}


if __name__ == "__main__":
    print("Iniciando indexação do Obsidian vault...")
    result = index_vault()
    print(f"✅ {result}")

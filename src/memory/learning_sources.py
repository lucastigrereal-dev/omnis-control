"""LearningSources — cite and validate sources for learning records."""
from __future__ import annotations


class LearningSources:
    """Utilities to cite and validate the provenance of a learning record."""

    def cite(self, learning: dict) -> str:
        """Return a citation string for the given learning record."""
        parts: list[str] = []

        mission_id = learning.get("mission_id", "")
        if mission_id:
            parts.append(f"mission:{mission_id}")

        source_file = learning.get("source_file", "")
        if source_file:
            parts.append(f"file:{source_file}")

        timestamp = learning.get("timestamp", "")
        if timestamp:
            parts.append(f"at:{timestamp}")

        tags = learning.get("tags", [])
        if tags:
            parts.append(f"tags:[{', '.join(tags)}]")

        if not parts:
            return "[source unknown]"
        return " | ".join(parts)

    def validate_source(self, learning: dict) -> bool:
        """Return True only if the learning has a source_file or mission_id."""
        return bool(learning.get("source_file") or learning.get("mission_id"))

"""Intent detection — deterministic keyword matching from config/intents.yaml.

No LLM. No external API. No network calls.
"""
from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Optional

import yaml

_DEFAULT_CONFIG = Path(__file__).resolve().parent.parent.parent / "config" / "intents.yaml"


def _load_config(config_path: Path = _DEFAULT_CONFIG) -> dict:
    if not config_path.exists():
        raise FileNotFoundError(f"intents.yaml not found at {config_path}")
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _normalize(text: str) -> str:
    """Lowercase + remove accents + strip."""
    nfkd = unicodedata.normalize("NFKD", text.lower().strip())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def detect_intent(
    request_text: str,
    config_path: Optional[Path] = None,
) -> tuple[str, str, str]:
    """Return (intent_key, deliverable, description).

    Checks each intent's patterns in order. First match wins.
    Falls back to ("unknown", "unknown", "") if nothing matches.
    """
    if config_path is None:
        config_path = _DEFAULT_CONFIG

    cfg = _load_config(config_path)
    normalized = _normalize(request_text)
    intents: dict = cfg.get("intents", {})
    fallback: str = cfg.get("fallback", "unknown")

    for intent_key, intent_data in intents.items():
        patterns: list[str] = intent_data.get("patterns", [])
        for pattern in patterns:
            if _normalize(pattern) in normalized:
                return (
                    intent_key,
                    intent_data.get("deliverable", "unknown"),
                    intent_data.get("description", ""),
                )

    return fallback, "unknown", ""

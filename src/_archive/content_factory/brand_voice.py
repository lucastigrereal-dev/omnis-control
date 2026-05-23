"""W098 — Brand Voice Guard model."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class BrandVoiceProfile:
    profile_id: str
    brand: str
    tone: str = "conversational"  # conversational, formal, casual, inspirational
    pillars: list[str] = field(default_factory=list)
    forbidden_terms: list[str] = field(default_factory=list)
    required_terms: list[str] = field(default_factory=list)
    max_hashtags: int = 30
    max_caption_length: int = 2200
    emoji_allowed: bool = True
    link_in_bio_default: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "profile_id": self.profile_id,
            "brand": self.brand,
            "tone": self.tone,
            "pillars": self.pillars,
            "forbidden_terms": self.forbidden_terms,
            "required_terms": self.required_terms,
            "max_hashtags": self.max_hashtags,
            "max_caption_length": self.max_caption_length,
            "emoji_allowed": self.emoji_allowed,
            "link_in_bio_default": self.link_in_bio_default,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "BrandVoiceProfile":
        return cls(
            profile_id=d["profile_id"],
            brand=d.get("brand", ""),
            tone=d.get("tone", "conversational"),
            pillars=d.get("pillars", []),
            forbidden_terms=d.get("forbidden_terms", []),
            required_terms=d.get("required_terms", []),
            max_hashtags=d.get("max_hashtags", 30),
            max_caption_length=d.get("max_caption_length", 2200),
            emoji_allowed=d.get("emoji_allowed", True),
            link_in_bio_default=d.get("link_in_bio_default", True),
            created_at=d.get("created_at", ""),
        )


@dataclass
class VoiceCheckResult:
    text_id: str
    profile_id: str
    passed: bool = True
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "text_id": self.text_id,
            "profile_id": self.profile_id,
            "passed": self.passed,
            "violations": self.violations,
            "warnings": self.warnings,
            "checked_at": self.checked_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "VoiceCheckResult":
        return cls(
            text_id=d["text_id"],
            profile_id=d.get("profile_id", ""),
            passed=d.get("passed", True),
            violations=d.get("violations", []),
            warnings=d.get("warnings", []),
            checked_at=d.get("checked_at", ""),
        )


class BrandVoiceGuard:
    """Deterministic brand voice validator. No LLM, no API."""

    DEFAULT_FORBIDDEN = [
        "lixo", "horrivel", "pessimo", "odio",
        "engano", "fraude", "golpe",
    ]

    def check(self, text: str, profile: BrandVoiceProfile) -> VoiceCheckResult:
        import uuid

        result = VoiceCheckResult(
            text_id=str(uuid.uuid4())[:8],
            profile_id=profile.profile_id,
        )

        text_lower = text.lower()

        all_forbidden = self.DEFAULT_FORBIDDEN + profile.forbidden_terms
        for term in all_forbidden:
            if term.lower() in text_lower:
                result.violations.append(f"Forbidden term found: '{term}'")
                result.passed = False

        if len(text) > profile.max_caption_length:
            result.violations.append(
                f"Caption too long: {len(text)} chars (max {profile.max_caption_length})"
            )
            result.passed = False

        if profile.required_terms:
            for term in profile.required_terms:
                if term.lower() not in text_lower:
                    result.warnings.append(f"Required term missing: '{term}'")

        hashtag_count = text.count("#")
        if hashtag_count > profile.max_hashtags:
            result.violations.append(
                f"Too many hashtags: {hashtag_count} (max {profile.max_hashtags})"
            )
            result.passed = False

        return result

    def check_caption(self, caption_text: str, profile: BrandVoiceProfile) -> VoiceCheckResult:
        return self.check(caption_text, profile)

    def check_brief(self, brief_text: str, profile: BrandVoiceProfile) -> VoiceCheckResult:
        return self.check(brief_text, profile)

    def build_default_profile(self, brand: str, tone: str = "conversational") -> BrandVoiceProfile:
        import uuid

        return BrandVoiceProfile(
            profile_id=str(uuid.uuid4())[:8],
            brand=brand,
            tone=tone,
            pillars=["educacional", "entretenimento", "vendas", "autoridade"],
        )

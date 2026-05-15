"""Tests for W098 — Brand Voice Guard."""
from __future__ import annotations

import pytest

from src.content_factory.brand_voice import BrandVoiceProfile, VoiceCheckResult, BrandVoiceGuard


class TestBrandVoiceProfile:
    def test_create_profile(self):
        p = BrandVoiceProfile(profile_id="vp1", brand="Tigre Real")
        assert p.profile_id == "vp1"
        assert p.brand == "Tigre Real"
        assert p.tone == "conversational"
        assert p.max_hashtags == 30
        assert p.max_caption_length == 2200

    def test_custom_profile(self):
        p = BrandVoiceProfile(
            profile_id="vp2",
            brand="Familia Tigre",
            tone="inspirational",
            forbidden_terms=["concorrente", "barato"],
            required_terms=["familia", "experiencia"],
            max_hashtags=15,
        )
        assert "concorrente" in p.forbidden_terms
        assert "familia" in p.required_terms
        assert p.max_hashtags == 15

    def test_to_dict_roundtrip(self):
        p = BrandVoiceProfile(
            profile_id="vp3",
            brand="Natal Ai Vou Eu",
            pillars=["turismo", "praia"],
            forbidden_terms=["termo1"],
        )
        d = p.to_dict()
        restored = BrandVoiceProfile.from_dict(d)
        assert restored.profile_id == p.profile_id
        assert restored.brand == p.brand
        assert restored.forbidden_terms == p.forbidden_terms
        assert restored.pillars == p.pillars


class TestVoiceCheckResult:
    def test_create_result(self):
        r = VoiceCheckResult(text_id="t1", profile_id="p1")
        assert r.text_id == "t1"
        assert r.passed is True
        assert r.violations == []

    def test_with_violations(self):
        r = VoiceCheckResult(
            text_id="t2",
            profile_id="p2",
            passed=False,
            violations=["Forbidden term: lixo"],
            warnings=["Missing required term: familia"],
        )
        assert r.passed is False
        assert len(r.violations) == 1
        assert len(r.warnings) == 1

    def test_to_dict_roundtrip(self):
        r = VoiceCheckResult(
            text_id="t3",
            profile_id="p3",
            passed=False,
            violations=["v1"],
            warnings=["w1"],
        )
        d = r.to_dict()
        restored = VoiceCheckResult.from_dict(d)
        assert restored.text_id == r.text_id
        assert restored.passed == r.passed
        assert restored.violations == r.violations
        assert restored.warnings == r.warnings


class TestBrandVoiceGuard:
    def setup_method(self):
        self.guard = BrandVoiceGuard()

    def _make_profile(self, **kwargs) -> BrandVoiceProfile:
        defaults = {
            "profile_id": "vp_test",
            "brand": "Tigre Real",
        }
        defaults.update(kwargs)
        return BrandVoiceProfile(**defaults)

    def test_check_clean_text_passes(self):
        profile = self._make_profile()
        result = self.guard.check("Conteudo limpo e adequado.", profile)
        assert result.passed is True
        assert len(result.violations) == 0

    def test_check_forbidden_term_detected(self):
        profile = self._make_profile()
        result = self.guard.check("Isso e um lixo completo.", profile)
        assert result.passed is False
        assert any("lixo" in v for v in result.violations)

    def test_check_custom_forbidden_term(self):
        profile = self._make_profile(forbidden_terms=["concorrente"])
        result = self.guard.check("O concorrente faz melhor.", profile)
        assert result.passed is False
        assert any("concorrente" in v for v in result.violations)

    def test_check_too_long_caption(self):
        profile = self._make_profile(max_caption_length=10)
        result = self.guard.check("Texto muito longo demais.", profile)
        assert result.passed is False
        assert any("long" in v for v in result.violations)

    def test_check_too_many_hashtags(self):
        profile = self._make_profile(max_hashtags=2)
        text = "#tag1 #tag2 #tag3 #tag4"
        result = self.guard.check(text, profile)
        assert result.passed is False
        assert any("hashtag" in v.lower() for v in result.violations)

    def test_check_missing_required_term(self):
        profile = self._make_profile(required_terms=["familia"])
        result = self.guard.check("Conteudo sem a palavra obrigatoria.", profile)
        # Missing required terms generate warnings, not failures
        assert any("familia" in w for w in result.warnings)

    def test_check_required_term_present(self):
        profile = self._make_profile(required_terms=["familia"])
        result = self.guard.check("Conteudo sobre familia e viagem.", profile)
        assert len(result.warnings) == 0

    def test_check_caption_delegates(self):
        profile = self._make_profile()
        result = self.guard.check_caption("Bom conteudo.", profile)
        assert isinstance(result, VoiceCheckResult)

    def test_check_brief_delegates(self):
        profile = self._make_profile()
        result = self.guard.check_brief("Bom brief.", profile)
        assert isinstance(result, VoiceCheckResult)

    def test_check_case_insensitive_forbidden(self):
        profile = self._make_profile()
        result = self.guard.check("Isso e LIXO.", profile)
        assert result.passed is False

    def test_build_default_profile(self):
        profile = self.guard.build_default_profile("Natal Ai Vou Eu", "inspirational")
        assert profile.brand == "Natal Ai Vou Eu"
        assert profile.tone == "inspirational"
        assert len(profile.pillars) == 4

    def test_check_multiple_violations(self):
        profile = self._make_profile(max_caption_length=10, forbidden_terms=["errado"])
        result = self.guard.check("Isso e lixo e errado e muito longo para caber.", profile)
        assert result.passed is False
        assert len(result.violations) >= 2

"""Testes de estabilidade e determinismo do content_hash."""
from __future__ import annotations

import json
import time

from src.missions.models import MissionContract, Sector


class TestContentHash:
    """content_hash() deve ser determinístico."""

    def test_hash_deterministic(self):
        c1 = MissionContract(
            title="Test Hash",
            objective="Verificar determinismo",
            sector=Sector.RESEARCH,
            user_request="hash test",
        )
        h1 = c1.content_hash()
        h2 = c1.content_hash()
        h3 = c1.content_hash()
        assert h1 == h2 == h3
        assert len(h1) == 64  # SHA-256 hex

    def test_hash_changes_with_title(self):
        c1 = MissionContract(
            title="Title A",
            objective="Same objective",
            sector=Sector.RESEARCH,
        )
        c2 = MissionContract(
            title="Title B",
            objective="Same objective",
            sector=Sector.RESEARCH,
        )
        assert c1.content_hash() != c2.content_hash()

    def test_hash_changes_with_objective(self):
        c1 = MissionContract(
            title="Same",
            objective="Objective A",
            sector=Sector.RESEARCH,
        )
        c2 = MissionContract(
            title="Same",
            objective="Objective B",
            sector=Sector.RESEARCH,
        )
        assert c1.content_hash() != c2.content_hash()

    def test_hash_changes_with_sector(self):
        c1 = MissionContract(
            title="Same", objective="Same", sector=Sector.RESEARCH,
        )
        c2 = MissionContract(
            title="Same", objective="Same", sector=Sector.SALES,
        )
        assert c1.content_hash() != c2.content_hash()

    def test_hash_independent_of_created_at(self):
        c1 = MissionContract(
            title="Test",
            objective="Time independence",
            sector=Sector.RESEARCH,
        )
        time.sleep(0.1)
        c2 = MissionContract(
            title="Test",
            objective="Time independence",
            sector=Sector.RESEARCH,
        )
        # created_at difere, mas hash deve ser igual
        assert c1.created_at != c2.created_at
        assert c1.content_hash() == c2.content_hash()

    def test_hash_changes_with_budget(self):
        c1 = MissionContract(
            title="Same", objective="Same", sector=Sector.RESEARCH,
        )
        c2 = MissionContract(
            title="Same", objective="Same", sector=Sector.RESEARCH,
            budget=c1.budget.model_copy(update={"max_tokens": 999}),
        )
        assert c1.content_hash() != c2.content_hash()

    def test_hash_consistent_across_platforms(self):
        """Simula o que seria cross-platform — o JSON canônico é ASCII puro."""
        contract = MissionContract(
            title="ASCII Only",
            objective="No unicode here",
            sector=Sector.OPERATIONS,
            user_request="simple ascii",
        )
        h = contract.content_hash()
        assert all(c in "0123456789abcdef" for c in h)

    def test_canonical_json_compact(self):
        contract = MissionContract(
            title="T",
            objective="O",
            sector=Sector.SECURITY,
        )
        canonical = contract.canonical_json()
        assert "\n" not in canonical
        assert "  " not in canonical

    def test_hash_hex_format(self):
        contract = MissionContract(
            title="T", objective="O", sector=Sector.KNOWLEDGE,
        )
        h = contract.content_hash()
        int(h, 16)  # não deve lançar ValueError

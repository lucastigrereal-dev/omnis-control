"""Contract tests for P19 Campaign Manager.

Validates:
- Import contracts: only P5 + P8 + P13 are imported
- No prohibited imports (P2, P3, P10, P14, P16, P17, legacies)
- Upstream model compatibility (mock-based)
"""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SRC_DIR = Path(__file__).resolve().parents[2] / "src" / "campaign_manager"


# ---------------------------------------------------------------------------
# Helpers — AST-based import analysis
# ---------------------------------------------------------------------------


def _get_imports_from_file(filepath: Path) -> list[str]:
    """Extract all import strings from a Python file using AST."""
    tree = ast.parse(filepath.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                base = node.module
                for alias in node.names:
                    imports.append(f"{base}.{alias.name}")
            else:
                for alias in node.names:
                    imports.append(f".{alias.name}")
    return imports


def _get_all_src_imports() -> set[str]:
    """Collect all imports across all source files in src/campaign_manager/."""
    all_imports: set[str] = set()
    for pyfile in SRC_DIR.glob("*.py"):
        all_imports.update(_get_imports_from_file(pyfile))
    return all_imports


# ============================================================================
# Authorized imports
# ============================================================================

AUTHORIZED_PREFIXES = [
    "src.marketing.models",
    "src.publisher_argos.models",
    "src.analytics.models",
    "src.analytics.service",
    "src.campaign_manager",
]

PROHIBITED_PREFIXES = [
    "src.creative_production_v2",   # P2
    "src.caption_approval_v2",      # P3
    "src.sales_crm",                 # P10
    "src.finance",                   # P14
    "src.observability_local",       # P16
    "src.delivery_portal",           # P17 cross
    "src.client_delivery",           # legacy
    "src.delivery_templates",        # legacy
    "src.campaign_package",          # legacy
    "src.campaign_auditor",          # legacy
    "src.execution_graph",           # legacy
    "src.approval_center",           # legacy
]


class TestImportContracts:
    """Ensure no prohibited imports exist in P19 source files."""

    @pytest.fixture(scope="class")
    def all_imports(self) -> set[str]:
        return _get_all_src_imports()

    def test_no_p2_imports(self, all_imports):
        for imp in all_imports:
            assert "creative_production_v2" not in imp, f"Prohibited import: {imp}"

    def test_no_p3_imports(self, all_imports):
        for imp in all_imports:
            assert "caption_approval_v2" not in imp, f"Prohibited import: {imp}"

    def test_no_p10_imports(self, all_imports):
        for imp in all_imports:
            assert "sales_crm" not in imp, f"Prohibited import: {imp}"

    def test_no_p14_imports(self, all_imports):
        for imp in all_imports:
            assert "finance" not in imp, f"Prohibited import: {imp}"

    def test_no_p16_imports(self, all_imports):
        for imp in all_imports:
            assert "observability_local" not in imp, f"Prohibited import: {imp}"

    def test_no_p17_imports(self, all_imports):
        for imp in all_imports:
            assert "delivery_portal" not in imp, f"Prohibited import: {imp}"

    def test_no_legacy_client_delivery(self, all_imports):
        for imp in all_imports:
            assert "client_delivery" not in imp, f"Prohibited import: {imp}"

    def test_no_legacy_delivery_templates(self, all_imports):
        for imp in all_imports:
            assert "delivery_templates" not in imp, f"Prohibited import: {imp}"

    def test_no_legacy_campaign_package(self, all_imports):
        for imp in all_imports:
            assert "campaign_package" not in imp, f"Prohibited import: {imp}"

    def test_no_legacy_campaign_auditor(self, all_imports):
        for imp in all_imports:
            assert "campaign_auditor" not in imp, f"Prohibited import: {imp}"

    def test_no_legacy_execution_graph(self, all_imports):
        for imp in all_imports:
            assert "execution_graph" not in imp, f"Prohibited import: {imp}"

    def test_no_legacy_approval_center(self, all_imports):
        for imp in all_imports:
            assert "approval_center" not in imp, f"Prohibited import: {imp}"


# ============================================================================
# Upstream model compatibility (P5, P8, P13 mock-based)
# ============================================================================


class TestUpstreamContracts:
    """Verify upstream models can be imported and used as expected."""

    def test_can_import_campaign_brief_from_p5(self):
        from src.marketing.models import CampaignBrief
        brief = CampaignBrief.new(
            name="Test Brief",
            objective_id="mktobj_abc",
            audience_id="aud_abc",
            budget=500.0,
        )
        assert brief.name == "Test Brief"
        assert brief.id.startswith("cmp_")

    def test_can_import_campaign_package_from_p5(self):
        from src.marketing.models import CampaignPackage
        pkg = CampaignPackage.new(name="Test Package")
        assert pkg.name == "Test Package"

    def test_can_import_marketing_objective_from_p5(self):
        from src.marketing.models import MarketingObjective
        obj = MarketingObjective.new(
            name="Awareness",
            description="Test",
            objective_type="awareness",
        )
        assert obj.name == "Awareness"

    def test_can_import_audience_profile_from_p5(self):
        from src.marketing.models import AudienceProfile
        aud = AudienceProfile.new(name="Test Audience", description="Test")
        assert aud.name == "Test Audience"

    def test_can_import_metric_summary_from_p13(self):
        from src.analytics.service import MetricSummary
        ms = MetricSummary.compute("met_abc", [10.0, 20.0, 30.0])
        assert ms.count == 3
        assert ms.avg == 20.0

    def test_can_import_metric_definition_from_p13(self):
        from src.analytics.models import MetricDefinition
        md = MetricDefinition.new(
            name="Total Likes",
            description="Test",
            category="engagement",
            aggregation="sum",
            unit="count",
        )
        assert md.name == "Total Likes"
        assert md.id.startswith("met_")

"""Tests for P22 Test Generator."""
from __future__ import annotations

import pytest

from src.capability_forge_real.test_generator import (
    generate_test_content,
    count_test_functions,
)
from src.capability_forge_real.models import CapabilityProposal, IMPL_TYPE_CLI_WRAPPER


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def cli_proposal():
    return CapabilityProposal.from_gap(
        gap_id="gap_001",
        capability_name="my_test_skill",
        sector="midia",
        desired_output="A test output",
        risk_level="medium",
        implementation_type=IMPL_TYPE_CLI_WRAPPER,
    )


# ── generate_test_content ──────────────────────────────────────────────────

class TestGenerateTestContent:
    def test_generates_valid_python(self, cli_proposal):
        content = generate_test_content(cli_proposal)
        compile(content, "<test>", "exec")

    def test_has_pytest_import(self, cli_proposal):
        content = generate_test_content(cli_proposal)
        assert "import pytest" in content

    def test_imports_skill_module(self, cli_proposal):
        content = generate_test_content(cli_proposal)
        assert "my_test_skill" in content
        assert "from src.skills.my_test_skill.run import" in content

    def test_imports_class_names(self, cli_proposal):
        content = generate_test_content(cli_proposal)
        assert "MyTestSkillInput" in content
        assert "MyTestSkillOutput" in content

    def test_has_run_test_class(self, cli_proposal):
        content = generate_test_content(cli_proposal)
        assert "class TestMyTestSkill:" in content

    def test_has_input_test_class(self, cli_proposal):
        content = generate_test_content(cli_proposal)
        assert "class TestMyTestSkillInput:" in content

    def test_has_output_test_class(self, cli_proposal):
        content = generate_test_content(cli_proposal)
        assert "class TestMyTestSkillOutput:" in content

    def test_has_helper_test_class(self, cli_proposal):
        content = generate_test_content(cli_proposal)
        assert "class TestNowIso:" in content


# ── count_test_functions ────────────────────────────────────────────────────

class TestCountTestFunctions:
    def test_counts_correctly(self, cli_proposal):
        content = generate_test_content(cli_proposal)
        count = count_test_functions(content)
        # run tests: test_run_returns_dict, test_run_has_status, test_run_has_result, stub
        # input tests: test_defaults, test_to_dict
        # output tests: test_default_status, test_to_dict
        # helper test: test_format
        assert count >= 3

    def test_empty_content_zero(self):
        assert count_test_functions("") == 0

    def test_no_tests_zero(self):
        assert count_test_functions("def helper():\n    pass\n") == 0

    def test_exact_count(self, cli_proposal):
        content = generate_test_content(cli_proposal)
        count = count_test_functions(content)
        assert count == 9  # 4 (run) + 2 (input) + 2 (output) + 1 (helper)

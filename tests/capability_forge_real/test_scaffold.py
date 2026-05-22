"""Tests for P22 Capability Forge Real scaffold module."""
from __future__ import annotations

import pytest
from pathlib import Path

from src.capability_forge_real.scaffold import (
    render_template,
    get_template,
    get_template_config,
    get_file_paths,
    SKILL_TEMPLATE,
    OFFLINE_PACKAGE_TEMPLATE,
    MANUAL_PROCESS_TEMPLATE,
    EXTERNAL_FUTURE_TEMPLATE,
    APP_FACTORY_FUTURE_TEMPLATE,
    TEMPLATES,
    TEMPLATE_CONFIGS,
    _slug,
    _class_name,
)
from src.capability_forge_real.models import SkillTemplateConfig
from src.capability_forge_real.models import (
    CapabilityProposal,
    IMPL_TYPE_CLI_WRAPPER,
    IMPL_TYPE_OFFLINE_PACKAGE,
    IMPL_TYPE_MANUAL_PROCESS,
    IMPL_TYPE_EXTERNAL_FUTURE,
    IMPL_TYPE_APP_FACTORY_FUTURE,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def cli_proposal():
    return CapabilityProposal.from_gap(
        gap_id="gap_001",
        capability_name="test_cli_skill",
        sector="midia",
        desired_output="A CLI skill for testing",
        risk_level="medium",
        implementation_type=IMPL_TYPE_CLI_WRAPPER,
    )


@pytest.fixture
def offline_proposal():
    return CapabilityProposal.from_gap(
        gap_id="gap_002",
        capability_name="test_offline_pkg",
        sector="produto",
        desired_output="An offline package",
        implementation_type=IMPL_TYPE_OFFLINE_PACKAGE,
    )


# ── Slug / Class Name ───────────────────────────────────────────────────────

class TestHelpers:
    def test_slug_basic(self):
        assert _slug("Test Skill") == "test_skill"

    def test_slug_special_chars(self):
        assert _slug("test-skill!@#") == "test_skill"

    def test_slug_strips_underscores(self):
        assert _slug("__test__") == "test"

    def test_class_name_simple(self):
        assert _class_name("test_skill") == "TestSkill"

    def test_class_name_multi_word(self):
        assert _class_name("my_new_capability") == "MyNewCapability"


# ── Template Rendering ──────────────────────────────────────────────────────

class TestRenderTemplate:
    def test_renders_capability_name(self, cli_proposal):
        result = render_template(SKILL_TEMPLATE, cli_proposal)
        assert cli_proposal.capability_name in result
        assert "{{capability_name}}" not in result

    def test_renders_class_name(self, cli_proposal):
        result = render_template(SKILL_TEMPLATE, cli_proposal)
        assert "TestCliSkill" in result

    def test_renders_description(self, cli_proposal):
        result = render_template(SKILL_TEMPLATE, cli_proposal)
        assert cli_proposal.desired_output in result

    def test_renders_output_target(self, cli_proposal):
        result = render_template(SKILL_TEMPLATE, cli_proposal)
        assert "test_cli_skill stub" in result

    def test_all_placeholders_replaced(self, cli_proposal):
        result = render_template(SKILL_TEMPLATE, cli_proposal)
        assert "{{" not in result

    def test_manual_process_template(self, cli_proposal):
        result = render_template(MANUAL_PROCESS_TEMPLATE, cli_proposal)
        assert "# test_cli_skill" in result
        assert "Processo Manual" in result

    def test_external_future_template(self, offline_proposal):
        result = render_template(EXTERNAL_FUTURE_TEMPLATE, offline_proposal)
        assert "Integracao Externa Futura" in result

    def test_app_factory_template(self, offline_proposal):
        result = render_template(APP_FACTORY_FUTURE_TEMPLATE, offline_proposal)
        assert "App Factory Future" in result

    def test_offline_package_renders(self, offline_proposal):
        result = render_template(OFFLINE_PACKAGE_TEMPLATE, offline_proposal)
        assert "TestOfflinePkg" in result
        assert "offline package" in result.lower()


# ── Template Registry ───────────────────────────────────────────────────────

class TestTemplateRegistry:
    def test_all_five_types_have_templates(self):
        for t in [IMPL_TYPE_CLI_WRAPPER, IMPL_TYPE_OFFLINE_PACKAGE,
                  IMPL_TYPE_MANUAL_PROCESS, IMPL_TYPE_EXTERNAL_FUTURE,
                  IMPL_TYPE_APP_FACTORY_FUTURE]:
            assert t in TEMPLATES

    def test_all_five_types_have_configs(self):
        for t in [IMPL_TYPE_CLI_WRAPPER, IMPL_TYPE_OFFLINE_PACKAGE,
                  IMPL_TYPE_MANUAL_PROCESS, IMPL_TYPE_EXTERNAL_FUTURE,
                  IMPL_TYPE_APP_FACTORY_FUTURE]:
            assert t in TEMPLATE_CONFIGS

    def test_get_template_returns_string(self):
        tpl = get_template(IMPL_TYPE_CLI_WRAPPER)
        assert isinstance(tpl, str)
        assert len(tpl) > 0

    def test_get_template_unknown_returns_none(self):
        assert get_template("unknown_type") is None

    def test_get_template_config_returns_config(self):
        cfg = get_template_config(IMPL_TYPE_CLI_WRAPPER)
        assert isinstance(cfg, SkillTemplateConfig)

    def test_cli_wrapper_config(self):
        cfg = get_template_config(IMPL_TYPE_CLI_WRAPPER)
        assert cfg.target_dir == "skills"
        assert cfg.filename == "run.py"

    def test_manual_process_no_tests(self):
        cfg = get_template_config(IMPL_TYPE_MANUAL_PROCESS)
        assert cfg.min_tests == 0
        assert cfg.test_filename == ""


# ── File Paths ──────────────────────────────────────────────────────────────

class TestGetFilePaths:
    def test_returns_source_path(self, cli_proposal):
        paths = get_file_paths(cli_proposal)
        assert "source" in paths
        assert paths["source"].name == "run.py"

    def test_source_dir_in_skills(self, cli_proposal):
        paths = get_file_paths(cli_proposal)
        assert "skills" in str(paths["source"])

    def test_test_path_for_cli_wrapper(self, cli_proposal):
        paths = get_file_paths(cli_proposal)
        assert "test" in paths
        assert paths["test"].name == "test_run.py"

    def test_manual_process_no_test_path(self, cli_proposal):
        # Override to manual_process
        manual = CapabilityProposal.from_gap(
            gap_id="gap_003",
            capability_name="manual_task",
            sector="operacoes",
            desired_output="A manual task",
            implementation_type=IMPL_TYPE_MANUAL_PROCESS,
        )
        paths = get_file_paths(manual)
        assert "test" not in paths or paths.get("test") is None

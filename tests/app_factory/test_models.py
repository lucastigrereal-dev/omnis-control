"""Tests for App Factory models — AppIdea, AppRequirement, AppBlueprint, AppArtifact."""
from __future__ import annotations

import pytest

from src.app_factory.errors import AppFactoryError
from src.app_factory.models import (
    APP_TYPE_API,
    APP_TYPE_CLI,
    APP_TYPE_LIBRARY,
    APP_TYPE_MOBILE,
    APP_TYPE_WEB,
    STATUS_DRAFT,
    STATUS_GENERATED,
    STATUS_PLANNED,
    AppArtifact,
    AppBlueprint,
    AppIdea,
    AppRequirement,
)


# ── AppIdea ───────────────────────────────────────────────────────────────────

class TestAppIdea:
    def test_new_creates_valid_idea(self):
        idea = AppIdea.new("My App", "A great app", "devs", ["feature X"], ["budget"])
        assert idea.title == "My App"
        assert idea.description == "A great app"
        assert idea.idea_id.startswith("idea_")
        assert idea.status == STATUS_DRAFT
        assert idea.features == ["feature X"]
        assert idea.constraints == ["budget"]
        assert idea.target_audience == "devs"

    def test_new_defaults_empty_lists(self):
        idea = AppIdea.new("Simple", "desc")
        assert idea.features == []
        assert idea.constraints == []

    def test_validate_empty_title_fails(self):
        idea = AppIdea.new("", "desc")
        issues = idea.validate()
        assert "title is required" in issues

    def test_validate_empty_description_fails(self):
        idea = AppIdea.new("title", "")
        issues = idea.validate()
        assert "description is required" in issues

    def test_validate_title_too_long(self):
        idea = AppIdea.new("X" * 250, "desc")
        issues = idea.validate()
        assert any("200" in i for i in issues)

    def test_is_valid_returns_true_for_good_idea(self):
        idea = AppIdea.new("Good", "Valid description")
        assert idea.is_valid is True

    def test_is_valid_returns_false_for_bad_idea(self):
        idea = AppIdea.new("", "")
        assert idea.is_valid is False

    def test_to_dict_from_dict_round_trip(self):
        idea = AppIdea.new("RoundTrip", "desc", features=["a", "b"])
        d = idea.to_dict()
        idea2 = AppIdea.from_dict(d)
        assert idea2.title == idea.title
        assert idea2.features == idea.features
        assert idea2.idea_id == idea.idea_id

    def test_new_strips_whitespace(self):
        idea = AppIdea.new("  Title  ", "  Desc  ", "  Aud  ", domain="  fintech  ")
        assert idea.title == "Title"
        assert idea.description == "Desc"
        assert idea.target_audience == "Aud"
        assert idea.domain == "fintech"


# ── AppRequirement ────────────────────────────────────────────────────────────

class TestAppRequirement:
    def test_from_idea_produces_requirements(self):
        idea = AppIdea.new("Auth App", "login and registration system", features=["auth", "login"])
        req = AppRequirement.from_idea(idea)
        assert req.requirement_id.startswith("req_")
        assert req.idea_id == idea.idea_id
        assert len(req.functional) > 0
        assert req.app_type == APP_TYPE_WEB

    def test_from_idea_defaults_when_no_features(self):
        idea = AppIdea.new("Bare App", "just something minimal")
        req = AppRequirement.from_idea(idea)
        assert len(req.functional) > 0
        assert len(req.non_functional) > 0

    def test_from_idea_detects_app_type_api(self):
        idea = AppIdea.new("REST API", "microservice with endpoints", features=["api", "rest"])
        req = AppRequirement.from_idea(idea)
        assert req.app_type == APP_TYPE_API

    def test_from_idea_detects_app_type_cli(self):
        idea = AppIdea.new("CLI Tool", "command-line script to batch process", features=["cli", "batch"])
        req = AppRequirement.from_idea(idea)
        assert req.app_type == APP_TYPE_CLI

    def test_from_idea_detects_mobile(self):
        idea = AppIdea.new("Mobile App", "ios and android app", features=["mobile", "ios"])
        req = AppRequirement.from_idea(idea)
        assert req.app_type == APP_TYPE_MOBILE

    def test_from_idea_detects_library(self):
        idea = AppIdea.new("SDK", "a reusable package for auth", features=["library", "sdk"])
        req = AppRequirement.from_idea(idea)
        assert req.app_type == APP_TYPE_LIBRARY

    def test_from_idea_detects_roles(self):
        idea = AppIdea.new("Admin Dashboard", "painel administrativo com admin e cliente")
        req = AppRequirement.from_idea(idea)
        assert "admin" in req.user_roles

    def test_from_idea_detects_entities(self):
        idea = AppIdea.new("E-commerce", "loja virtual com produtos, carrinho e pagamentos")
        req = AppRequirement.from_idea(idea)
        assert len(req.domain_entities) >= 2  # product, order, payment

    def test_to_dict_from_dict_round_trip(self):
        idea = AppIdea.new("Round", "trip test")
        req = AppRequirement.from_idea(idea)
        d = req.to_dict()
        req2 = AppRequirement.from_dict(d)
        assert req2.requirement_id == req.requirement_id
        assert req2.functional == req.functional

    def test_deduplicates_functional(self):
        idea = AppIdea.new("Auth App", "login system", features=["auth", "login"])
        req = AppRequirement.from_idea(idea)
        # Should not have duplicate "User registration" entries
        assert req.functional.count("User registration") <= 1


# ── AppBlueprint ──────────────────────────────────────────────────────────────

class TestAppBlueprint:
    def test_from_requirement_creates_blueprint(self):
        idea = AppIdea.new("Blog", "content platform with users and posts")
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        assert bp.blueprint_id.startswith("bp_")
        assert bp.requirement_id == req.requirement_id
        assert len(bp.modules) > 0

    def test_blueprint_always_has_core_module(self):
        idea = AppIdea.new("Minimal", "tiny app")
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        module_names = [m["name"] for m in bp.modules]
        assert "core" in module_names

    def test_blueprint_has_tests_module(self):
        idea = AppIdea.new("Tested", "app")
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        module_names = [m["name"] for m in bp.modules]
        assert "tests" in module_names

    def test_api_endpoints_always_has_health(self):
        idea = AppIdea.new("Healthy", "app")
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        paths = [e["path"] for e in bp.api_endpoints]
        assert "/health" in paths

    def test_tech_stack_for_web(self):
        idea = AppIdea.new("WebApp", "website")
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        assert "PostgreSQL" in str(bp.tech_stack.get("database", ""))

    def test_tech_stack_for_cli(self):
        idea = AppIdea.new("CLI Tool", "terminal script", features=["cli"])
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        assert bp.tech_stack.get("database") == "SQLite"

    def test_data_models_match_entities(self):
        idea = AppIdea.new("Shop", "ecommerce with products orders payments", features=["payments", "orders"])
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        entity_names = [m["name"] for m in bp.data_models]
        assert len(entity_names) >= 1

    def test_to_dict_from_dict_round_trip(self):
        idea = AppIdea.new("Round", "trip")
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        d = bp.to_dict()
        bp2 = AppBlueprint.from_dict(d)
        assert bp2.blueprint_id == bp.blueprint_id


# ── AppArtifact ───────────────────────────────────────────────────────────────

class TestAppArtifact:
    def test_from_blueprint_creates_artifact(self):
        idea = AppIdea.new("Full App", "complete system")
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        art = AppArtifact.from_blueprint(bp, "# PRD\n\nContent.", {"src": None})
        assert art.artifact_id.startswith("art_")
        assert art.blueprint_id == bp.blueprint_id
        assert "# PRD" in art.prd_markdown
        assert "src" in art.project_structure

    def test_to_dict_from_dict_round_trip(self):
        idea = AppIdea.new("Round", "trip")
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        art = AppArtifact.from_blueprint(bp, "# PRD", {"src": None})
        d = art.to_dict()
        art2 = AppArtifact.from_dict(d)
        assert art2.artifact_id == art.artifact_id
        assert art2.prd_markdown == art.prd_markdown


# ── Constants ─────────────────────────────────────────────────────────────────

class TestConstants:
    def test_status_constants(self):
        assert STATUS_DRAFT == "draft"
        assert STATUS_PLANNED == "planned"
        assert STATUS_GENERATED == "generated"

    def test_app_type_constants(self):
        assert APP_TYPE_WEB == "web"
        assert APP_TYPE_CLI == "cli"
        assert APP_TYPE_API == "api"
        assert APP_TYPE_MOBILE == "mobile"
        assert APP_TYPE_LIBRARY == "library"

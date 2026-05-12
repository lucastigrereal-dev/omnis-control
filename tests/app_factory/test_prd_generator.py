"""Tests for PRD Generator — markdown output."""
from __future__ import annotations

from src.app_factory.models import AppBlueprint, AppIdea, AppRequirement
from src.app_factory.prd_generator import generate_prd


class TestPRDGenerator:
    def test_generates_non_empty_markdown(self):
        idea = AppIdea.new("MD App", "test markdown gen")
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        md = generate_prd(bp, req, idea)
        assert len(md) > 100
        assert md.startswith("# PRD:")

    def test_contains_idea_title(self):
        idea = AppIdea.new("UniqueTitle99", "test")
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        md = generate_prd(bp, req, idea)
        assert "UniqueTitle99" in md

    def test_contains_blueprint_id(self):
        idea = AppIdea.new("BP Ref", "test")
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        md = generate_prd(bp, req, idea)
        assert bp.blueprint_id in md

    def test_contains_functional_requirements(self):
        idea = AppIdea.new("FR Test", "test with requirements")
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        md = generate_prd(bp, req, idea)
        assert "Functional Requirements" in md
        assert "FR-01" in md

    def test_contains_non_functional_requirements(self):
        idea = AppIdea.new("NFR Test", "test")
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        md = generate_prd(bp, req, idea)
        assert "Non-Functional Requirements" in md
        assert "NFR-01" in md

    def test_api_endpoints_table(self):
        idea = AppIdea.new("API Test", "rest api", features=["api"])
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        md = generate_prd(bp, req, idea)
        assert "| Method | Path | Description |" in md

    def test_tech_stack_section(self):
        idea = AppIdea.new("Tech Test", "web app")
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        md = generate_prd(bp, req, idea)
        assert "Tech Stack" in md

    def test_empty_features_shows_placeholder(self):
        idea = AppIdea.new("NoFeatures", "simple app")
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        md = generate_prd(bp, req, idea)
        assert "derived from requirements" in md

    def test_explicit_features_appear(self):
        idea = AppIdea.new("Feat", "app", features=["Custom feature A", "Custom feature B"])
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        md = generate_prd(bp, req, idea)
        assert "Custom feature A" in md
        assert "Custom feature B" in md

    def test_constraints_appear(self):
        idea = AppIdea.new("Constrained", "app", constraints=["Budget max R$500", "No cloud"])
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        md = generate_prd(bp, req, idea)
        assert "Budget max R$500" in md
        assert "No cloud" in md

    def test_footer_present(self):
        idea = AppIdea.new("Footer", "test")
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        md = generate_prd(bp, req, idea)
        assert "OMNIS App Factory Skeleton" in md

    def test_cli_app_no_ui_components(self):
        idea = AppIdea.new("CLI Tool", "terminal app", features=["cli"])
        req = AppRequirement.from_idea(idea)
        bp = AppBlueprint.from_requirement(req)
        md = generate_prd(bp, req, idea)
        # CLI apps should not have UI component section
        # But they still get modules section
        assert "### 5.1 Modules" in md

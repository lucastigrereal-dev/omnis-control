"""W156 — Edge case hardening tests for App Factory."""
from __future__ import annotations

import pytest

from src.app_factory.diff_engine import diff_ideas, diff_schemas, diff_api_contracts
from src.app_factory.models import AppIdea, AppBlueprint, AppRequirement
from src.app_factory.quality_score import score_prd, score_schema, score_api_contract, score_task_plan
from src.app_factory.recovery import init_pipeline_state, build_recovery_plan, rollback_to_stage, STAGE_ORDER
from src.app_factory.storage_safety import matches_blocked_pattern, validate_command_safety, StorageSafetyPolicy
from src.app_factory.status_tracker import StatusTracker


class TestEmptyAndNullInputs:
    def test_empty_prd_scoring(self):
        result = score_prd("")
        assert result.score == 0.0

    def test_empty_schema_scoring(self):
        result = score_schema([])
        assert result.score == 0.0

    def test_empty_api_scoring(self):
        result = score_api_contract([])
        assert result.score == 0.0

    def test_empty_tasks_scoring(self):
        result = score_task_plan([])
        assert result.score == 0.0

    def test_diff_empty_ideas(self):
        empty = {"title": "", "description": "", "target_audience": "", "domain": "", "status": "draft", "features": [], "constraints": []}
        report = diff_ideas(empty, empty)
        assert report.has_differences is False

    def test_diff_empty_schemas(self):
        report = diff_schemas([], [])
        assert report.has_differences is False

    def test_diff_empty_api_contracts(self):
        report = diff_api_contracts([], [])
        assert report.has_differences is False


class TestBoundaryScores:
    def test_prd_max_score(self):
        prd = """# PRD: Perfect App

## Functional Requirements
- Login with OAuth
- User management

## Non-Functional Requirements
- < 200ms p95
- 99.99% uptime

## Tech Stack
| Component | Choice |
|---|---|
| Frontend | React |
| Backend | FastAPI |
| Database | PostgreSQL |

## API Endpoints
| Method | Path | Description |
|---|---|---|
| GET | /health | Health |
| POST | /api/users | Create |
"""
        result = score_prd(prd)
        assert 80 <= result.score <= 100

    def test_schema_perfect_table(self):
        tables = [{
            "name": "users",
            "fields": [
                {"name": "id", "type": "UUID", "primary_key": True},
                {"name": "email", "type": "str", "unique": True},
                {"name": "name", "type": "str"},
                {"name": "created_at", "type": "datetime"},
                {"name": "updated_at", "type": "datetime"},
            ],
            "indexes": [{"fields": ["email"]}, {"fields": ["name"]}],
            "relationships": [],
        }]
        result = score_schema(tables)
        assert result.score >= 85.0


class TestRecoveryEdgeCases:
    def test_recovery_resets_failed_and_can_resume(self):
        state = init_pipeline_state("idea_x")
        state.mark_completed("validate_idea")
        state.mark_failed("extract_requirements", "err")
        plan = build_recovery_plan(state)
        assert plan.can_resume is True
        assert plan.resume_from_stage == "extract_requirements"
        assert plan.state.stages["extract_requirements"].status.value == "pending"

    def test_rollback_to_first_stage_preserves_target(self):
        state = init_pipeline_state("idea_x")
        state.mark_completed("validate_idea")
        state.mark_completed("extract_requirements")
        state.mark_completed("design_blueprint")
        state = rollback_to_stage(state, STAGE_ORDER[0])
        # Target stage stays as-is; later stages are cleared
        assert state.stages[STAGE_ORDER[0]].status.value == "completed"
        assert state.stages[STAGE_ORDER[1]].status.value == "pending"

    def test_rollback_to_last_stage_clears_nothing(self):
        state = init_pipeline_state("idea_x")
        state.mark_completed("validate_idea")
        last = STAGE_ORDER[-1]
        state = rollback_to_stage(state, last)
        assert state.stages["validate_idea"].status.value != "pending"


class TestStorageSafetyEdgeCases:
    def test_empty_command(self):
        violations = validate_command_safety("")
        assert len(violations) == 0

    def test_case_insensitive_blocked(self):
        violations = validate_command_safety("RM -RF /tmp")
        assert len(violations) >= 1

    def test_partial_pattern_not_blocked(self):
        violations = validate_command_safety("git status")
        assert len(violations) == 0

    def test_nested_secrets_path_blocked(self):
        assert matches_blocked_pattern("deep/nested/secrets/token.txt", [".env", "secrets/", "*.key"]) is True

    def test_custom_policy(self):
        policy = StorageSafetyPolicy(blocked_patterns=["custom_blocked/*"], blocked_commands=["bad_cmd"])
        violations = validate_command_safety("bad_cmd --flag", policy)
        assert len(violations) == 1


class TestStatusTrackerEdgeCases:
    def test_rapid_start_complete_toggle(self):
        tracker = StatusTracker()
        tracker.register_idea("toggle", "Toggle App")
        for _ in range(10):
            tracker.mark_stage("toggle", "validate_idea", "started")
            tracker.mark_stage("toggle", "validate_idea", "completed")
        status = tracker.get_status("toggle")
        assert status is not None

    def test_re_register_same_idea(self):
        tracker = StatusTracker()
        s1 = tracker.register_idea("same", "Same")
        tracker.mark_stage("same", "validate_idea", "completed")
        s2 = tracker.register_idea("same", "Same Updated")
        assert s1 is s2  # Same object returned


class TestModelEdgeCases:
    def test_idea_with_unicode(self):
        idea = AppIdea.new(title="Aplicativo com acentos", description="Descrição com caractéres especiais: 日本語, café")
        assert idea.is_valid

    def test_idea_title_max_length(self):
        idea = AppIdea.new(title="A" * 200, description="Valid length at boundary")
        assert idea.is_valid

    def test_idea_title_exceeds_max(self):
        idea = AppIdea.new(title="A" * 201, description="Just over")
        assert not idea.is_valid

    def test_blueprint_deterministic_across_calls(self):
        idea = AppIdea.new(title="Det", description="Deterministic blueprint")
        req1 = AppRequirement.from_idea(idea)
        req2 = AppRequirement.from_idea(idea)
        bp1 = AppBlueprint.from_requirement(req1)
        bp2 = AppBlueprint.from_requirement(req2)
        assert bp1.tech_stack == bp2.tech_stack
        assert len(bp1.modules) == len(bp2.modules)

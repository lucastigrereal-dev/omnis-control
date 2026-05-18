"""Tests for quality score module."""
from __future__ import annotations

import pytest

from src.app_factory.quality_score import (
    DimensionScore,
    QualityScore,
    score_prd,
    score_schema,
    score_api_contract,
    score_task_plan,
    compute_quality_score,
)


class TestDimensionScore:
    def test_percentage_calculation(self):
        d = DimensionScore("test", 75.0)
        assert d.percentage == 75.0

    def test_grade_a(self):
        d = DimensionScore("test", 95.0)
        assert d.grade == "A"

    def test_grade_b(self):
        d = DimensionScore("test", 85.0)
        assert d.grade == "B"

    def test_grade_c(self):
        d = DimensionScore("test", 75.0)
        assert d.grade == "C"

    def test_grade_d(self):
        d = DimensionScore("test", 65.0)
        assert d.grade == "D"

    def test_grade_f(self):
        d = DimensionScore("test", 40.0)
        assert d.grade == "F"

    def test_to_dict(self):
        d = DimensionScore("test", 80.0, notes=["note1"])
        result = d.to_dict()
        assert result["name"] == "test"
        assert result["score"] == 80.0

    def test_zero_max_score(self):
        d = DimensionScore("zero", 0, max_score=0)
        assert d.percentage == 100.0


class TestScorePRD:
    def test_empty_prd_scores_zero(self):
        result = score_prd("")
        assert result.score == 0.0

    def test_complete_prd_scores_high(self):
        prd = """# PRD: Test App

## Functional Requirements
- Login system
- User dashboard

## Non-Functional Requirements
- Response time < 500ms
- 99.9% uptime

## Tech Stack
| Component | Choice |
|---|---|
| Backend | FastAPI |

## API Endpoints
| Method | Path | Description |
|---|---|---|
| GET | /health | Health check |
"""
        result = score_prd(prd)
        assert result.score > 70.0

    def test_missing_sections_deducted(self):
        result = score_prd("# PRD: Bare\n\nJust some text.")
        assert result.score < 70.0

    def test_bullets_and_tables_help(self):
        prd = """# PRD: Structured App

## Functional Requirements
- Feature A
- Feature B

## Non-Functional Requirements
- Fast

## Tech Stack
| Layer | Choice |
|---|---|
| BE | FastAPI |

## API Endpoints
| Method | Path |
|---|---|
| GET | /health |
"""
        result = score_prd(prd)
        assert result.score >= 80.0


class TestScoreSchema:
    def test_empty_schema_scores_zero(self):
        result = score_schema([])
        assert result.score == 0.0

    def test_table_with_pk_and_timestamps_scores_high(self):
        tables = [{
            "name": "users",
            "fields": [
                {"name": "id", "type": "UUID", "primary_key": True},
                {"name": "email", "type": "str"},
                {"name": "created_at", "type": "datetime"},
                {"name": "updated_at", "type": "datetime"},
            ],
            "indexes": [{"fields": ["email"]}],
            "relationships": [],
        }]
        result = score_schema(tables)
        assert result.score >= 80.0

    def test_table_missing_pk(self):
        tables = [{
            "name": "items",
            "fields": [
                {"name": "title", "type": "str"},
            ],
            "indexes": [],
            "relationships": [],
        }]
        result = score_schema(tables)
        assert result.score < 90.0

    def test_fk_fields_without_relationships_gets_note(self):
        tables = [{
            "name": "orders",
            "fields": [
                {"name": "id", "type": "UUID", "primary_key": True},
                {"name": "user_id", "type": "UUID"},
                {"name": "created_at", "type": "datetime"},
                {"name": "updated_at", "type": "datetime"},
            ],
            "indexes": [],
            "relationships": [],
        }]
        result = score_schema(tables)
        assert len(result.notes) >= 1


class TestScoreAPIContract:
    def test_empty_api_scores_zero(self):
        result = score_api_contract([])
        assert result.score == 0.0

    def test_api_with_health_and_crud_scores_high(self):
        endpoints = [
            {"method": "GET", "path": "/health", "error_codes": []},
            {"method": "POST", "path": "/api/users", "error_codes": [400, 500]},
            {"method": "GET", "path": "/api/users", "error_codes": [500]},
            {"method": "PUT", "path": "/api/users/{id}", "error_codes": [400, 404, 500]},
            {"method": "DELETE", "path": "/api/users/{id}", "error_codes": [404, 500]},
        ]
        result = score_api_contract(endpoints)
        assert result.score >= 70.0

    def test_api_without_health_deducted(self):
        endpoints = [
            {"method": "GET", "path": "/api/items", "error_codes": []},
        ]
        result = score_api_contract(endpoints)
        assert result.score < 90.0

    def test_verb_in_path_deducted(self):
        endpoints = [
            {"method": "GET", "path": "/api/getUsers", "error_codes": []},
        ]
        result = score_api_contract(endpoints)
        assert result.score < 95.0


class TestScoreTaskPlan:
    def test_empty_tasks_scores_zero(self):
        result = score_task_plan([])
        assert result.score == 0.0

    def test_tasks_with_all_areas_scores_high(self):
        tasks = [
            {"area": "data", "title": "Create migrations", "description": "Set up database schema with all required tables", "depends_on": []},
            {"area": "backend", "title": "API routes", "description": "Implement REST endpoints for all resources", "depends_on": ["Create migrations"]},
            {"area": "frontend", "title": "UI pages", "description": "Build React components for all pages including list, detail, and form views", "depends_on": ["API routes"]},
            {"area": "qa", "title": "E2E tests", "description": "Write comprehensive end-to-end tests covering all user flows", "depends_on": ["UI pages"]},
        ]
        result = score_task_plan(tasks)
        assert result.score >= 70.0

    def test_missing_areas_deducted(self):
        tasks = [
            {"area": "data", "title": "DB setup", "description": "Create database", "depends_on": []},
        ]
        result = score_task_plan(tasks)
        assert result.score < 90.0


class TestComputeQualityScore:
    def test_returns_quality_score(self):
        result = compute_quality_score(
            "art_001",
            "# PRD: Test App\n\n## Functional Requirements\n- Login\n\n## Non-Functional Requirements\n- Fast\n\n## Tech Stack\n| Layer | Choice |\n|---|---|\n| BE | FastAPI |\n\n## API Endpoints\n| Method | Path |\n|---|---|\n| GET | /health |\n",
            [{"name": "users", "fields": [
                {"name": "id", "type": "UUID", "primary_key": True},
                {"name": "created_at", "type": "datetime"},
                {"name": "updated_at", "type": "datetime"},
            ], "indexes": [], "relationships": []}],
            [{"method": "GET", "path": "/health", "error_codes": []}],
            [{"area": "data", "title": "DB", "description": "Set up database schema with all required tables", "depends_on": []}],
        )
        assert isinstance(result, QualityScore)
        assert result.artifact_id == "art_001"
        assert result.overall.score > 0

    def test_summary_has_all_keys(self):
        result = compute_quality_score(
            "art_002",
            "# PRD: X\n\n## Functional Requirements\n- A\n\n## Non-Functional Requirements\n- B\n\n## Tech Stack\n- C\n\n## API Endpoints\n- D\n",
            [{"name": "items", "fields": [
                {"name": "id", "type": "UUID", "primary_key": True},
                {"name": "created_at", "type": "datetime"},
                {"name": "updated_at", "type": "datetime"},
            ], "indexes": [], "relationships": []}],
            [{"method": "GET", "path": "/health", "error_codes": []}, {"method": "POST", "path": "/api/items", "error_codes": [400]}],
            [{"area": "data", "title": "Schema", "description": "Create all tables with proper indexes", "depends_on": []}],
        )
        summary = result.summary
        assert "overall_pct" in summary
        assert "overall_grade" in summary
        assert "prd_pct" in summary
        assert "schema_pct" in summary
        assert "api_pct" in summary
        assert "tasks_pct" in summary

    def test_to_dict(self):
        result = compute_quality_score(
            "art_003",
            "# PRD: Test\n\n## Functional Requirements\n- Feature\n\n## Non-Functional Requirements\n- Constraint\n\n## Tech Stack\n- Stack\n\n## API Endpoints\n- API\n",
            [{"name": "t", "fields": [
                {"name": "id", "type": "UUID", "primary_key": True},
                {"name": "created_at", "type": "datetime"},
                {"name": "updated_at", "type": "datetime"},
            ], "indexes": [], "relationships": []}],
            [{"method": "GET", "path": "/health", "error_codes": []}],
            [{"area": "data", "title": "Init", "description": "Initialize database with full schema", "depends_on": []}],
        )
        d = result.to_dict()
        assert d["score_id"] == result.score_id
        assert d["artifact_id"] == "art_003"

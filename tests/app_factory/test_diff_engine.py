"""Tests for diff engine module."""
from __future__ import annotations

import pytest

from src.app_factory.diff_engine import (
    DiffEntry,
    DiffReport,
    diff_ideas,
    diff_schemas,
    diff_api_contracts,
    diff_blueprints,
)


class TestDiffEntry:
    def test_is_change_true_for_changed(self):
        e = DiffEntry("field", "changed", "old", "new")
        assert e.is_change is True

    def test_is_change_false_for_unchanged(self):
        e = DiffEntry("field", "unchanged", "same", "same")
        assert e.is_change is False

    def test_to_dict(self):
        e = DiffEntry("title", "changed", "A", "B")
        d = e.to_dict()
        assert d["field"] == "title"
        assert d["kind"] == "changed"
        assert d["old_value"] == "A"
        assert d["new_value"] == "B"


class TestDiffReport:
    def test_has_differences(self):
        report = DiffReport("r1", "L", "R", [
            DiffEntry("a", "unchanged"),
            DiffEntry("b", "changed", "x", "y"),
        ], "2026-01-01T00:00:00Z")
        assert report.has_differences is True
        assert report.change_count == 1

    def test_no_differences(self):
        report = DiffReport("r1", "L", "R", [
            DiffEntry("a", "unchanged"),
        ], "2026-01-01T00:00:00Z")
        assert report.has_differences is False

    def test_added_removed_changed(self):
        report = DiffReport("r1", "L", "R", [
            DiffEntry("a", "added", None, "x"),
            DiffEntry("b", "removed", "x", None),
            DiffEntry("c", "changed", "x", "y"),
        ], "2026-01-01T00:00:00Z")
        assert len(report.added) == 1
        assert len(report.removed) == 1
        assert len(report.changed) == 1


class TestDiffIdeas:
    def test_identical_ideas_no_changes(self):
        idea = {"title": "App", "description": "Desc", "target_audience": "Devs", "domain": "tech", "status": "draft", "features": [], "constraints": []}
        report = diff_ideas(idea, idea)
        assert report.has_differences is False

    def test_different_titles_detected(self):
        left = {"title": "App A", "description": "Same", "target_audience": "", "domain": "", "status": "draft", "features": [], "constraints": []}
        right = {"title": "App B", "description": "Same", "target_audience": "", "domain": "", "status": "draft", "features": [], "constraints": []}
        report = diff_ideas(left, right)
        assert report.has_differences is True
        assert any(e.field == "title" and e.kind == "changed" for e in report.entries)

    def test_different_features_detected(self):
        left = {"title": "A", "description": "D", "target_audience": "", "domain": "", "status": "draft", "features": ["auth"], "constraints": []}
        right = {"title": "A", "description": "D", "target_audience": "", "domain": "", "status": "draft", "features": ["auth", "search"], "constraints": []}
        report = diff_ideas(left, right)
        assert report.has_differences is True

    def test_custom_labels(self):
        idea = {"title": "A", "description": "D", "target_audience": "", "domain": "", "status": "draft", "features": [], "constraints": []}
        report = diff_ideas(idea, idea, left_label="v1", right_label="v2")
        assert report.left_label == "v1"
        assert report.right_label == "v2"


class TestDiffSchemas:
    def test_identical_schemas(self):
        tables = [{"name": "users", "fields": [{"name": "id", "type": "UUID"}]}]
        report = diff_schemas(tables, tables)
        assert report.has_differences is False

    def test_table_added(self):
        left = [{"name": "users", "fields": []}]
        right = [{"name": "users", "fields": []}, {"name": "items", "fields": []}]
        report = diff_schemas(left, right)
        assert any(e.kind == "added" for e in report.entries)

    def test_field_changed(self):
        left = [{"name": "users", "fields": [{"name": "id", "type": "UUID"}]}]
        right = [{"name": "users", "fields": [{"name": "id", "type": "int"}]}]
        report = diff_schemas(left, right)
        has_changes = report.has_differences
        assert has_changes is True


class TestDiffAPIContracts:
    def test_identical_contracts(self):
        endpoints = [{"method": "GET", "path": "/health", "description": "Health check"}]
        report = diff_api_contracts(endpoints, endpoints)
        assert report.has_differences is False

    def test_endpoint_added(self):
        left = [{"method": "GET", "path": "/health", "description": "Health"}]
        right = [{"method": "GET", "path": "/health", "description": "Health"}, {"method": "POST", "path": "/api/users", "description": "Create"}]
        report = diff_api_contracts(left, right)
        assert any(e.kind == "added" for e in report.entries)

    def test_description_changed(self):
        left = [{"method": "GET", "path": "/health", "description": "Old"}]
        right = [{"method": "GET", "path": "/health", "description": "New"}]
        report = diff_api_contracts(left, right)
        assert any(e.kind == "changed" for e in report.entries)


class TestDiffBlueprints:
    def test_identical_blueprints(self):
        bp = {"modules": [], "data_models": [], "api_endpoints": [], "component_tree": {}, "tech_stack": {}}
        report = diff_blueprints(bp, bp)
        assert report.has_differences is False

    def test_different_modules(self):
        left = {"modules": [{"name": "core"}], "data_models": [], "api_endpoints": [], "component_tree": {}, "tech_stack": {}}
        right = {"modules": [{"name": "core"}, {"name": "auth"}], "data_models": [], "api_endpoints": [], "component_tree": {}, "tech_stack": {}}
        report = diff_blueprints(left, right)
        assert report.has_differences is True

    def test_different_tech_stack(self):
        left = {"modules": [], "data_models": [], "api_endpoints": [], "component_tree": {}, "tech_stack": {"be": "FastAPI"}}
        right = {"modules": [], "data_models": [], "api_endpoints": [], "component_tree": {}, "tech_stack": {"be": "Flask"}}
        report = diff_blueprints(left, right)
        assert report.has_differences is True

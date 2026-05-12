"""Tests for App Factory errors."""
from __future__ import annotations

import pytest

from src.app_factory.errors import (
    AppFactoryError,
    InvalidAppIdeaError,
    PlannerError,
    PRDGenerationError,
    StructureGenerationError,
)


class TestErrors:
    def test_base_error_is_exception(self):
        assert issubclass(AppFactoryError, Exception)

    def test_invalid_app_idea_is_base(self):
        assert issubclass(InvalidAppIdeaError, AppFactoryError)

    def test_planner_error_is_base(self):
        assert issubclass(PlannerError, AppFactoryError)

    def test_prd_generation_error_is_base(self):
        assert issubclass(PRDGenerationError, AppFactoryError)

    def test_structure_generation_error_is_base(self):
        assert issubclass(StructureGenerationError, AppFactoryError)

    def test_errors_can_be_raised(self):
        with pytest.raises(AppFactoryError):
            raise InvalidAppIdeaError("bad idea")

    def test_error_message_preserved(self):
        err = InvalidAppIdeaError("title missing")
        assert "title missing" in str(err)

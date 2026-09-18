"""Unit tests for models.py — validation helpers and computed fields."""
import pytest

from todo_agent.core.models import (
    validate_importance,
    validate_item_status,
    validate_project_status,
)
from todo_agent.core.store import recalculate_percent_complete


class TestValidateImportance:
    def test_zero_passes(self):
        validate_importance(0)

    def test_hundred_passes(self):
        validate_importance(100)

    def test_midpoint_passes(self):
        validate_importance(50)

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            validate_importance(-1)

    def test_over_hundred_raises(self):
        with pytest.raises(ValueError):
            validate_importance(101)


class TestValidateProjectStatus:
    def test_all_valid(self):
        for s in ["not-started", "scheduled", "in-progress", "completed"]:
            validate_project_status(s)

    def test_unknown_raises(self):
        with pytest.raises(ValueError):
            validate_project_status("done")


class TestValidateItemStatus:
    def test_all_valid(self):
        for s in ["not-started", "in-progress", "completed"]:
            validate_item_status(s)

    def test_unknown_raises(self):
        with pytest.raises(ValueError):
            validate_item_status("scheduled")


class TestRecalculatePercentComplete:
    def _project(self, statuses):
        return {
            "percent_complete": None,
            "items": [{"status": s} for s in statuses],
        }

    def test_empty_items_is_null(self):
        p = self._project([])
        recalculate_percent_complete(p)
        assert p["percent_complete"] is None

    def test_zero_of_one(self):
        p = self._project(["not-started"])
        recalculate_percent_complete(p)
        assert p["percent_complete"] == 0

    def test_one_of_one(self):
        p = self._project(["completed"])
        recalculate_percent_complete(p)
        assert p["percent_complete"] == 100

    def test_one_of_three_floors(self):
        p = self._project(["completed", "not-started", "not-started"])
        recalculate_percent_complete(p)
        assert p["percent_complete"] == 33

    def test_two_of_three_floors(self):
        p = self._project(["completed", "completed", "not-started"])
        recalculate_percent_complete(p)
        assert p["percent_complete"] == 66

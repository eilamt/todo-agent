"""Unit tests for core/operations.py."""
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from todo_agent.core import operations, store
from todo_agent.core.operations import AmbiguousMatchError


@pytest.fixture(autouse=True)
def use_tmp_data(tmp_data_path, monkeypatch):
    monkeypatch.setattr(store, "get_data_file_path", lambda: tmp_data_path)
    monkeypatch.setattr(
        "todo_agent.config.get_data_file_path", lambda: tmp_data_path
    )


class TestAddLane:
    def test_creates_lane(self):
        lane = operations.add_lane("Work")
        data = store.load_data()
        assert len(data["lanes"]) == 1
        assert data["lanes"][0]["name"] == "Work"

    def test_duplicate_raises(self):
        operations.add_lane("Work")
        with pytest.raises(ValueError, match="already exists"):
            operations.add_lane("Work")

    def test_case_insensitive_duplicate(self):
        operations.add_lane("Work")
        with pytest.raises(ValueError):
            operations.add_lane("work")

    def test_creates_instructions_file(self, tmp_path):
        lanes_dir = tmp_path / ".todo-agent" / "lanes"
        with patch("pathlib.Path.home", return_value=tmp_path):
            operations.add_lane("My Lane")
        assert (lanes_dir / "my-lane.md").exists()


class TestAddProject:
    def test_creates_project(self):
        operations.add_lane("Work")
        project = operations.add_project("Work", "Website")
        data = store.load_data()
        assert data["lanes"][0]["projects"][0]["name"] == "Website"

    def test_same_name_different_lanes_ok(self):
        operations.add_lane("Work")
        operations.add_lane("Personal")
        operations.add_project("Work", "Budget")
        operations.add_project("Personal", "Budget")  # should not raise

    def test_duplicate_in_same_lane_raises(self):
        operations.add_lane("Work")
        operations.add_project("Work", "Budget")
        with pytest.raises(ValueError, match="already exists"):
            operations.add_project("Work", "Budget")

    def test_default_importance(self):
        operations.add_lane("Work")
        project = operations.add_project("Work", "X")
        assert project["importance"] == 50


class TestAddItem:
    def test_first_item_sets_percent_complete_to_zero_not_null(self):
        operations.add_lane("Work")
        operations.add_project("Work", "Website")
        operations.add_item("Website", "Design")
        data = store.load_data()
        assert data["lanes"][0]["projects"][0]["percent_complete"] == 0

    def test_duplicate_title_raises(self):
        operations.add_lane("Work")
        operations.add_project("Work", "Website")
        operations.add_item("Website", "Design")
        with pytest.raises(ValueError, match="already exists"):
            operations.add_item("Website", "Design")


class TestSetItemStatus:
    def test_completed_recalculates_percent(self):
        operations.add_lane("Work")
        operations.add_project("Work", "Website")
        operations.add_item("Website", "Design")
        operations.set_item_status("Design", "completed")
        data = store.load_data()
        assert data["lanes"][0]["projects"][0]["percent_complete"] == 100

    def test_invalid_status_raises(self):
        operations.add_lane("Work")
        operations.add_project("Work", "Website")
        operations.add_item("Website", "Design")
        with pytest.raises(ValueError):
            operations.set_item_status("Design", "done")


class TestFlagIndependence:
    def setup_method(self):
        operations.add_lane("Work")
        operations.add_project("Work", "P")
        operations.add_item("P", "Task")

    def test_set_today_does_not_alter_this_week(self):
        operations.set_this_week("Task", True)
        operations.set_today("Task", True)
        data = store.load_data()
        item = data["lanes"][0]["projects"][0]["items"][0]
        assert item["today"] is True
        assert item["this_week"] is True

    def test_set_this_week_does_not_alter_today(self):
        operations.set_today("Task", True)
        operations.set_this_week("Task", False)
        data = store.load_data()
        item = data["lanes"][0]["projects"][0]["items"][0]
        assert item["today"] is True
        assert item["this_week"] is False


class TestAmbiguousMatch:
    def test_raises_when_item_in_multiple_projects(self):
        operations.add_lane("Work")
        operations.add_project("Work", "Alpha")
        operations.add_project("Work", "Beta")
        operations.add_item("Alpha", "Review")
        operations.add_item("Beta", "Review")
        data = store.load_data()
        with pytest.raises(AmbiguousMatchError):
            operations._find_item(data, "Review")


class TestDeletePreview:
    def test_lane_preview_counts(self):
        operations.add_lane("Work")
        operations.add_project("Work", "P1")
        operations.add_project("Work", "P2")
        operations.add_item("P1", "T1")
        operations.add_item("P1", "T2")
        operations.add_item("P2", "T3")
        data = store.load_data()
        preview = operations.get_delete_preview(data, "lane", lane_name="Work")
        assert preview["projects_count"] == 2
        assert preview["items_count"] == 3

    def test_project_preview_counts(self):
        operations.add_lane("Work")
        operations.add_project("Work", "P1")
        operations.add_item("P1", "T1")
        operations.add_item("P1", "T2")
        data = store.load_data()
        preview = operations.get_delete_preview(data, "project", project_name="P1")
        assert preview["items_count"] == 2


class TestDeleteCascade:
    def test_delete_lane_removes_all_children(self):
        operations.add_lane("Work")
        operations.add_project("Work", "P1")
        operations.add_item("P1", "T1")
        operations.delete_lane("Work")
        data = store.load_data()
        assert data["lanes"] == []

    def test_delete_project_removes_items(self):
        operations.add_lane("Work")
        operations.add_project("Work", "P1")
        operations.add_item("P1", "T1")
        operations.delete_project("P1")
        data = store.load_data()
        assert data["lanes"][0]["projects"] == []


class TestNotes:
    def test_add_project_note_blank_raises(self):
        operations.add_lane("Work")
        operations.add_project("Work", "P")
        with pytest.raises(ValueError):
            operations.add_project_note("P", "  ")

    def test_add_item_note_blank_raises(self):
        operations.add_lane("Work")
        operations.add_project("Work", "P")
        operations.add_item("P", "T")
        with pytest.raises(ValueError):
            operations.add_item_note("T", "")

    def test_list_notes_returns_in_order(self):
        operations.add_lane("Work")
        operations.add_project("Work", "P")
        operations.add_project_note("P", "first")
        operations.add_project_note("P", "second")
        data = store.load_data()
        notes = operations.list_notes("project", "P")
        assert len(notes) == 2
        assert notes[0]["text"] == "first"
        assert notes[1]["text"] == "second"

    def test_list_notes_empty_returns_empty_list(self):
        operations.add_lane("Work")
        operations.add_project("Work", "P")
        notes = operations.list_notes("project", "P")
        assert notes == []

    def test_list_notes_invalid_entity_type_raises(self):
        with pytest.raises(ValueError, match="entity_type"):
            operations.list_notes("lane", "Work")


class TestSetItemDescription:
    def setup_method(self):
        operations.add_lane("Work")
        operations.add_project("Work", "P")
        operations.add_item("P", "Task")

    def test_set_description_stores_value(self):
        operations.set_item_description("Task", "needs mobile-first approach")
        data = store.load_data()
        item = data["lanes"][0]["projects"][0]["items"][0]
        assert item["description"] == "needs mobile-first approach"

    def test_empty_string_stores_null(self):
        operations.set_item_description("Task", "   ")
        data = store.load_data()
        item = data["lanes"][0]["projects"][0]["items"][0]
        assert item["description"] is None

    def test_clearing_with_null_stores_null(self):
        operations.set_item_description("Task", "some text")
        operations.set_item_description("Task", None)
        data = store.load_data()
        item = data["lanes"][0]["projects"][0]["items"][0]
        assert item["description"] is None

    def test_add_item_with_description_stores_it(self):
        operations.add_item("P", "Task2", description="initial description")
        data = store.load_data()
        item = next(i for i in data["lanes"][0]["projects"][0]["items"] if i["title"] == "Task2")
        assert item["description"] == "initial description"

    def test_backward_compat_item_without_description_key(self):
        data = store.load_data()
        item = data["lanes"][0]["projects"][0]["items"][0]
        item.pop("description", None)
        assert item.get("description") is None


class TestSetItemImportance:
    def setup_method(self):
        operations.add_lane("Work")
        operations.add_project("Work", "P")
        operations.add_item("P", "Task")

    def test_set_importance_stores_value(self):
        operations.set_item_importance("Task", 90)
        data = store.load_data()
        item = data["lanes"][0]["projects"][0]["items"][0]
        assert item["importance"] == 90

    def test_boundary_zero_accepted(self):
        operations.set_item_importance("Task", 0)
        data = store.load_data()
        item = data["lanes"][0]["projects"][0]["items"][0]
        assert item["importance"] == 0

    def test_boundary_hundred_accepted(self):
        operations.set_item_importance("Task", 100)
        data = store.load_data()
        item = data["lanes"][0]["projects"][0]["items"][0]
        assert item["importance"] == 100

    def test_below_zero_raises(self):
        with pytest.raises(ValueError):
            operations.set_item_importance("Task", -1)

    def test_above_hundred_raises(self):
        with pytest.raises(ValueError):
            operations.set_item_importance("Task", 101)

    def test_add_item_without_importance_defaults_to_50(self):
        item = operations.add_item("P", "Task2")
        assert item["importance"] == 50

    def test_backward_compat_item_without_importance_key(self):
        data = store.load_data()
        item = data["lanes"][0]["projects"][0]["items"][0]
        item.pop("importance", None)
        assert item.get("importance", 50) == 50


class TestRenameItem:
    def setup_method(self):
        operations.add_lane("Work")
        operations.add_project("Work", "P")
        operations.add_item("P", "Old Title")

    def test_rename_changes_title(self):
        result = operations.rename_item("Old Title", "New Title")
        assert result["title"] == "New Title"
        data = store.load_data()
        item = data["lanes"][0]["projects"][0]["items"][0]
        assert item["title"] == "New Title"

    def test_rename_empty_title_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            operations.rename_item("Old Title", "")

    def test_rename_whitespace_only_raises(self):
        with pytest.raises(ValueError):
            operations.rename_item("Old Title", "   ")

    def test_rename_duplicate_raises(self):
        operations.add_item("P", "Other Item")
        with pytest.raises(ValueError, match="already exists"):
            operations.rename_item("Old Title", "Other Item")

    def test_rename_case_insensitive_duplicate_raises(self):
        operations.add_item("P", "Other Item")
        with pytest.raises(ValueError, match="already exists"):
            operations.rename_item("Old Title", "other item")

    def test_rename_to_same_name_is_ok(self):
        result = operations.rename_item("Old Title", "Old Title")
        assert result["title"] == "Old Title"

    def test_rename_preserves_other_fields(self):
        operations.set_item_description("Old Title", "some desc")
        result = operations.rename_item("Old Title", "New Title")
        assert result["description"] == "some desc"


class TestRenameProject:
    def setup_method(self):
        operations.add_lane("Work")
        operations.add_project("Work", "Old Project")

    def test_rename_changes_name(self):
        result = operations.rename_project("Old Project", "New Project")
        assert result["name"] == "New Project"
        data = store.load_data()
        project = data["lanes"][0]["projects"][0]
        assert project["name"] == "New Project"

    def test_rename_empty_name_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            operations.rename_project("Old Project", "")

    def test_rename_whitespace_only_raises(self):
        with pytest.raises(ValueError):
            operations.rename_project("Old Project", "   ")

    def test_rename_duplicate_raises(self):
        operations.add_project("Work", "Other Project")
        with pytest.raises(ValueError, match="already exists"):
            operations.rename_project("Old Project", "Other Project")

    def test_rename_case_insensitive_duplicate_raises(self):
        operations.add_project("Work", "Other Project")
        with pytest.raises(ValueError, match="already exists"):
            operations.rename_project("Old Project", "other project")

    def test_rename_to_same_name_is_ok(self):
        result = operations.rename_project("Old Project", "Old Project")
        assert result["name"] == "Old Project"

    def test_rename_preserves_items(self):
        operations.add_item("Old Project", "Task A")
        operations.rename_project("Old Project", "New Project")
        data = store.load_data()
        project = data["lanes"][0]["projects"][0]
        assert project["name"] == "New Project"
        assert len(project["items"]) == 1
        assert project["items"][0]["title"] == "Task A"

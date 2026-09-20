"""Unit tests for set_this_weekend operation and this_weekend field propagation."""
import pytest

from todo_agent.core import operations, store


@pytest.fixture(autouse=True)
def use_tmp_data(tmp_data_path, monkeypatch):
    monkeypatch.setattr(store, "get_data_file_path", lambda: tmp_data_path)
    monkeypatch.setattr("todo_agent.config.get_data_file_path", lambda: tmp_data_path)


@pytest.fixture
def seeded():
    """Create Work/Website/Fix login bug for use in each test."""
    operations.add_lane("Work")
    operations.add_project("Work", "Website")
    operations.add_item("Website", "Fix login bug", lane_name="Work")


class TestSetThisWeekend:
    def test_set_true(self, seeded):
        item = operations.set_this_weekend("Fix login bug", True)
        assert item["this_weekend"] is True

    def test_set_false(self, seeded):
        operations.set_this_weekend("Fix login bug", True)
        item = operations.set_this_weekend("Fix login bug", False)
        assert item["this_weekend"] is False

    def test_persists_after_reload(self, seeded):
        operations.set_this_weekend("Fix login bug", True)
        data = store.load_data()
        item = data["lanes"][0]["projects"][0]["items"][0]
        assert item["this_weekend"] is True

    def test_does_not_affect_today_or_this_week(self, seeded):
        operations.set_today("Fix login bug", True)
        operations.set_this_week("Fix login bug", True)
        operations.set_this_weekend("Fix login bug", True)
        data = store.load_data()
        item = data["lanes"][0]["projects"][0]["items"][0]
        assert item["today"] is True
        assert item["this_week"] is True
        assert item["this_weekend"] is True

    def test_unknown_item_raises(self, seeded):
        with pytest.raises(ValueError):
            operations.set_this_weekend("Nonexistent item", True)


class TestAddItemDefaultsThisWeekend:
    def test_new_item_has_this_weekend_false(self, seeded):
        data = store.load_data()
        item = data["lanes"][0]["projects"][0]["items"][0]
        assert item.get("this_weekend") is False


class TestListItemsIncludesThisWeekend:
    def test_this_weekend_in_list_items(self, seeded):
        operations.set_this_weekend("Fix login bug", True)
        items = operations.list_items()
        assert items[0]["this_weekend"] is True

    def test_missing_field_defaults_false_in_list_items(self, seeded):
        data = store.load_data()
        item = data["lanes"][0]["projects"][0]["items"][0]
        item.pop("this_weekend", None)
        store.save_data(data)
        items = operations.list_items()
        assert items[0]["this_weekend"] is False


class TestGetItemIncludesThisWeekend:
    def test_this_weekend_in_get_item(self, seeded):
        operations.set_this_weekend("Fix login bug", True)
        result = operations.get_item("Fix login bug")
        assert result["this_weekend"] is True

    def test_missing_field_defaults_false_in_get_item(self, seeded):
        data = store.load_data()
        item = data["lanes"][0]["projects"][0]["items"][0]
        item.pop("this_weekend", None)
        store.save_data(data)
        result = operations.get_item("Fix login bug")
        assert result["this_weekend"] is False

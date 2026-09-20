"""Unit tests for reorder_project operation."""
import pytest

from todo_agent.core import operations, store


@pytest.fixture(autouse=True)
def use_tmp_data(tmp_data_path, monkeypatch):
    monkeypatch.setattr(store, "get_data_file_path", lambda: tmp_data_path)
    monkeypatch.setattr("todo_agent.config.get_data_file_path", lambda: tmp_data_path)


@pytest.fixture
def work_with_three_projects():
    """Create Work lane with projects Alpha, Beta, Gamma and return their ids."""
    operations.add_lane("Work")
    a = operations.add_project("Work", "Alpha")
    b = operations.add_project("Work", "Beta")
    c = operations.add_project("Work", "Gamma")
    return a["id"], b["id"], c["id"]


def project_names():
    return [p["name"] for p in store.load_data()["lanes"][0]["projects"]]


class TestReorderProject:
    def test_move_to_first(self, work_with_three_projects):
        a_id, b_id, c_id = work_with_three_projects
        operations.reorder_project(c_id, 0)
        assert project_names() == ["Gamma", "Alpha", "Beta"]

    def test_move_to_last(self, work_with_three_projects):
        a_id, b_id, c_id = work_with_three_projects
        operations.reorder_project(a_id, 2)
        assert project_names() == ["Beta", "Gamma", "Alpha"]

    def test_move_to_middle(self, work_with_three_projects):
        a_id, b_id, c_id = work_with_three_projects
        operations.reorder_project(a_id, 1)
        assert project_names() == ["Beta", "Alpha", "Gamma"]

    def test_clamp_negative_index(self, work_with_three_projects):
        a_id, b_id, c_id = work_with_three_projects
        operations.reorder_project(c_id, -5)
        assert project_names()[0] == "Gamma"

    def test_clamp_excess_index(self, work_with_three_projects):
        a_id, b_id, c_id = work_with_three_projects
        operations.reorder_project(a_id, 999)
        assert project_names()[-1] == "Alpha"

    def test_persists_after_reload(self, work_with_three_projects):
        a_id, b_id, c_id = work_with_three_projects
        operations.reorder_project(b_id, 0)
        assert store.load_data()["lanes"][0]["projects"][0]["name"] == "Beta"

    def test_unknown_project_raises(self, work_with_three_projects):
        with pytest.raises(ValueError):
            operations.reorder_project("nonexistent-uuid", 0)

    def test_single_project_no_op(self):
        operations.add_lane("Work")
        p = operations.add_project("Work", "Solo")
        operations.reorder_project(p["id"], 0)
        assert project_names() == ["Solo"]

    def test_stays_in_same_lane(self, work_with_three_projects):
        """Reordering does not move projects to a different lane."""
        operations.add_lane("Personal")
        a_id, b_id, c_id = work_with_three_projects
        operations.reorder_project(a_id, 0)
        data = store.load_data()
        personal_projects = data["lanes"][1]["projects"]
        assert len(personal_projects) == 0

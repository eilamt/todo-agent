"""Unit tests for reorder_lane operation."""
import pytest

from todo_agent.core import operations, store


@pytest.fixture(autouse=True)
def use_tmp_data(tmp_data_path, monkeypatch):
    monkeypatch.setattr(store, "get_data_file_path", lambda: tmp_data_path)
    monkeypatch.setattr("todo_agent.config.get_data_file_path", lambda: tmp_data_path)


@pytest.fixture
def three_lanes():
    """Create lanes A, B, C and return their ids."""
    a = operations.add_lane("A")
    b = operations.add_lane("B")
    c = operations.add_lane("C")
    return a["id"], b["id"], c["id"]


def lane_names():
    return [l["name"] for l in store.load_data()["lanes"]]


class TestReorderLane:
    def test_move_to_first(self, three_lanes):
        a_id, b_id, c_id = three_lanes
        operations.reorder_lane(c_id, 0)
        assert lane_names() == ["C", "A", "B"]

    def test_move_to_last(self, three_lanes):
        a_id, b_id, c_id = three_lanes
        operations.reorder_lane(a_id, 2)
        assert lane_names() == ["B", "C", "A"]

    def test_move_to_middle(self, three_lanes):
        a_id, b_id, c_id = three_lanes
        operations.reorder_lane(a_id, 1)
        assert lane_names() == ["B", "A", "C"]

    def test_clamp_negative_index(self, three_lanes):
        a_id, b_id, c_id = three_lanes
        operations.reorder_lane(c_id, -5)
        assert lane_names()[0] == "C"

    def test_clamp_excess_index(self, three_lanes):
        a_id, b_id, c_id = three_lanes
        operations.reorder_lane(a_id, 999)
        assert lane_names()[-1] == "A"

    def test_persists_after_reload(self, three_lanes):
        a_id, b_id, c_id = three_lanes
        operations.reorder_lane(b_id, 0)
        assert store.load_data()["lanes"][0]["name"] == "B"

    def test_unknown_lane_raises(self, three_lanes):
        with pytest.raises(ValueError):
            operations.reorder_lane("nonexistent-uuid", 0)

    def test_single_lane_no_op(self):
        lane = operations.add_lane("Solo")
        operations.reorder_lane(lane["id"], 0)
        assert lane_names() == ["Solo"]

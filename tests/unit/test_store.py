"""Unit tests for store.py — load/save/atomic-write behaviour."""
import json
import os
from unittest.mock import patch

import pytest

from todo_agent.core import store


@pytest.fixture(autouse=True)
def use_tmp_data(tmp_data_path, monkeypatch):
    """Redirect all store calls to the tmp data file."""
    monkeypatch.setattr(store, "get_data_file_path", lambda: tmp_data_path)


class TestLoadData:
    def test_creates_empty_store_when_absent(self, tmp_data_path):
        data = store.load_data()
        assert data == {"version": "1", "lanes": []}
        assert tmp_data_path.exists()

    def test_returns_existing_data(self, tmp_data_path):
        existing = {"version": "1", "lanes": [{"id": "abc", "name": "Work", "instructions_file": "", "projects": []}]}
        tmp_data_path.write_text(json.dumps(existing))
        data = store.load_data()
        assert data["lanes"][0]["name"] == "Work"

    def test_round_trip_preserves_data(self, tmp_data_path):
        original = {"version": "1", "lanes": []}
        tmp_data_path.write_text(json.dumps(original))
        store.save_data(store.load_data())
        assert json.loads(tmp_data_path.read_text()) == original


class TestSaveData:
    def test_writes_valid_indented_json(self, tmp_data_path):
        store.save_data({"version": "1", "lanes": []})
        content = tmp_data_path.read_text()
        parsed = json.loads(content)
        assert parsed == {"version": "1", "lanes": []}
        assert "\n" in content  # indented

    def test_atomic_write_leaves_original_on_failure(self, tmp_data_path):
        original = {"version": "1", "lanes": []}
        tmp_data_path.write_text(json.dumps(original))

        with patch("os.replace", side_effect=OSError("simulated crash")):
            with pytest.raises(OSError):
                store.save_data({"version": "1", "lanes": [{"name": "NEW"}]})

        # Original file should be unchanged
        assert json.loads(tmp_data_path.read_text()) == original

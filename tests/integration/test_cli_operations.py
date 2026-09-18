"""Integration tests for the CLI — stubbed LLM, full dispatch."""
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from todo_agent.core import store
from todo_agent.cli.main import main
from tests.conftest import make_mock_tool_response, make_mock_text_response


@pytest.fixture(autouse=True)
def use_tmp_data(tmp_data_path, monkeypatch):
    monkeypatch.setattr(store, "get_data_file_path", lambda: tmp_data_path)
    monkeypatch.setattr(
        "todo_agent.config.get_data_file_path", lambda: tmp_data_path
    )
    monkeypatch.setattr(
        "todo_agent.config.load_config",
        lambda: {"data_file": str(tmp_data_path), "model": "claude-haiku-3"},
    )


def run_with_tool(tool_name, tool_input, user_text="dummy"):
    mock_tool_msg = make_mock_tool_response(tool_name, tool_input)
    mock_text_msg = make_mock_text_response()
    with patch("todo_agent.cli.agent.anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.side_effect = [mock_tool_msg, mock_text_msg]
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            main([user_text])


class TestAddLaneCLI:
    def test_adds_lane_to_data_file(self, tmp_data_path, capsys):
        run_with_tool("add_lane", {"name": "Work"})
        data = store.load_data()
        assert any(l["name"] == "Work" for l in data["lanes"])
        out = capsys.readouterr().out
        assert "Work" in out


class TestDeleteLaneCLI:
    def test_cancel_preserves_data(self, tmp_data_path):
        run_with_tool("add_lane", {"name": "Work"})
        mock_tool_msg = make_mock_tool_response("delete_lane", {"lane_name": "Work"})
        mock_text_msg = make_mock_text_response("Deletion cancelled.")
        with patch("todo_agent.cli.agent.anthropic.Anthropic") as MockClient, \
             patch("sys.stdin", StringIO("n\n")), \
             patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            MockClient.return_value.messages.create.side_effect = [mock_tool_msg, mock_text_msg]
            main(["delete Work"])
        data = store.load_data()
        assert any(l["name"] == "Work" for l in data["lanes"])

    def test_confirm_deletes_lane(self, tmp_data_path):
        run_with_tool("add_lane", {"name": "Work"})
        mock_tool_msg = make_mock_tool_response("delete_lane", {"lane_name": "Work"})
        mock_text_msg = make_mock_text_response("Lane deleted.")
        with patch("todo_agent.cli.agent.anthropic.Anthropic") as MockClient, \
             patch("sys.stdin", StringIO("y\n")), \
             patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            MockClient.return_value.messages.create.side_effect = [mock_tool_msg, mock_text_msg]
            main(["delete Work"])
        data = store.load_data()
        assert data["lanes"] == []


class TestClarificationCLI:
    def test_prints_question_without_writing_data(self, tmp_data_path, capsys):
        run_with_tool("add_lane", {"name": "Work"})
        data_before = store.load_data()
        run_with_tool(
            "request_clarification",
            {"question": "Did you mean Alpha or Beta?"},
        )
        data_after = store.load_data()
        assert data_before == data_after
        out = capsys.readouterr().out
        assert "Alpha or Beta" in out


class TestListNotesCLI:
    def test_prints_notes_without_modifying_data(self, tmp_data_path):
        run_with_tool("add_lane", {"name": "Work"})
        run_with_tool("add_project", {"lane_name": "Work", "project_name": "P"})
        run_with_tool("add_project_note", {"project_name": "P", "text": "hello"})
        data_before = store.load_data()
        run_with_tool("list_notes", {"entity_type": "project", "name": "P"})
        data_after = store.load_data()
        assert data_before == data_after

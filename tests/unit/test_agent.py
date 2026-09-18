"""Unit tests for cli/agent.py — run_agent agentic loop."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from todo_agent.cli.agent import MAX_ROUNDS, run_agent


@pytest.fixture(autouse=True)
def set_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


def _make_tool_use_block(name, tool_input, tool_id="tu_001"):
    block = SimpleNamespace()
    block.type = "tool_use"
    block.name = name
    block.input = tool_input
    block.id = tool_id
    return block


def _make_text_block(text):
    block = SimpleNamespace()
    block.type = "text"
    block.text = text
    return block


def _make_response(content, stop_reason="tool_use"):
    resp = MagicMock()
    resp.content = content
    resp.stop_reason = stop_reason
    return resp


class TestRunAgentSingleToolCall:
    def test_single_tool_executes_and_returns_summary(self):
        """One tool_use in first response, then LLM responds with text."""
        tool_block = _make_tool_use_block("add_lane", {"name": "Work"})
        text_block = _make_text_block("Done! Added 'Work' lane.")

        dispatch_fn = MagicMock(return_value="Added lane 'Work'.")

        with patch("todo_agent.cli.agent.anthropic.Anthropic") as MockClient:
            mock_client = MockClient.return_value
            mock_client.messages.create.side_effect = [
                _make_response([tool_block]),          # round 0: tool call
                _make_response([text_block], "end_turn"),  # round 1: final text
            ]
            result = run_agent("add a lane called Work", {}, {}, dispatch_fn)

        assert result == "Done! Added 'Work' lane."
        dispatch_fn.assert_called_once_with("add_lane", {"name": "Work"})

    def test_no_api_key_raises(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            run_agent("anything", {}, {}, lambda *a: "")


class TestRunAgentMultipleToolsInOneResponse:
    def test_two_tool_uses_in_one_response_both_execute(self):
        """Two tool_use blocks in a single LLM response — dispatch called twice."""
        block1 = _make_tool_use_block("add_lane", {"name": "Work"}, "tu_001")
        block2 = _make_tool_use_block("add_project", {"lane_name": "Work", "project_name": "Site"}, "tu_002")
        text_block = _make_text_block("All done.")

        dispatch_fn = MagicMock(return_value="ok")

        with patch("todo_agent.cli.agent.anthropic.Anthropic") as MockClient:
            mock_client = MockClient.return_value
            mock_client.messages.create.side_effect = [
                _make_response([block1, block2]),       # round 0: two tools
                _make_response([text_block], "end_turn"),  # round 1: text
            ]
            result = run_agent("add Work lane and Site project", {}, {}, dispatch_fn)

        assert result == "All done."
        assert dispatch_fn.call_count == 2
        calls = [c.args for c in dispatch_fn.call_args_list]
        assert calls[0] == ("add_lane", {"name": "Work"})
        assert calls[1] == ("add_project", {"lane_name": "Work", "project_name": "Site"})


class TestRunAgentTermination:
    def test_end_turn_with_no_tools_returns_text(self):
        """LLM immediately returns text with no tool calls on round 0 (tool_choice=auto path)."""
        text_block = _make_text_block("Nothing to do here.")

        with patch("todo_agent.cli.agent.anthropic.Anthropic") as MockClient:
            # Override tool_choice for this test by having the mock accept any kwargs
            mock_client = MockClient.return_value
            # Simulate: round 0 returns tool_use; round 1 returns text (normal path)
            tool_block = _make_tool_use_block("request_clarification", {"question": "What?"})
            mock_client.messages.create.side_effect = [
                _make_response([tool_block]),
                _make_response([text_block], "end_turn"),
            ]
            dispatch_fn = MagicMock(return_value="What?")
            result = run_agent("huh?", {}, {}, dispatch_fn)

        assert result == "Nothing to do here."

    def test_fallback_when_no_text_block_in_final_response(self):
        """If the final response has no text block, returns the fallback string."""
        other_block = SimpleNamespace()
        other_block.type = "unknown"

        with patch("todo_agent.cli.agent.anthropic.Anthropic") as MockClient:
            mock_client = MockClient.return_value
            tool_block = _make_tool_use_block("add_lane", {"name": "X"})
            mock_client.messages.create.side_effect = [
                _make_response([tool_block]),
                _make_response([other_block], "end_turn"),
            ]
            dispatch_fn = MagicMock(return_value="ok")
            result = run_agent("add lane X", {}, {}, dispatch_fn)

        assert result == "(No response from assistant.)"


class TestRunAgentMaxRounds:
    def test_exceeds_max_rounds_raises(self):
        """If LLM keeps returning tool_use blocks, ValueError is raised after MAX_ROUNDS."""
        tool_block = _make_tool_use_block("add_lane", {"name": "Loop"})

        with patch("todo_agent.cli.agent.anthropic.Anthropic") as MockClient:
            mock_client = MockClient.return_value
            # Always return a tool_use — never terminates
            mock_client.messages.create.return_value = _make_response([tool_block])
            dispatch_fn = MagicMock(return_value="ok")

            with pytest.raises(ValueError, match="exceeded"):
                run_agent("loop forever", {}, {}, dispatch_fn)

        assert dispatch_fn.call_count == MAX_ROUNDS


class TestRunAgentUnknownTool:
    def test_unknown_tool_name_raises(self):
        """If LLM returns an unrecognised tool name, ValueError is raised."""
        bad_block = _make_tool_use_block("nonexistent_tool", {})

        with patch("todo_agent.cli.agent.anthropic.Anthropic") as MockClient:
            mock_client = MockClient.return_value
            mock_client.messages.create.return_value = _make_response([bad_block])
            dispatch_fn = MagicMock()

            with pytest.raises(ValueError, match="unknown tool name"):
                run_agent("do the thing", {}, {}, dispatch_fn)

        dispatch_fn.assert_not_called()

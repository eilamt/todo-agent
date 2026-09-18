"""Shared test fixtures for the to-do agent test suite."""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def tmp_data_path(tmp_path):
    """Return a Path to a temporary todos.json file (not yet created)."""
    return tmp_path / "todos.json"


@pytest.fixture
def patch_config(tmp_data_path):
    """Patch load_config and get_data_file_path to use a temporary data file."""
    config = {"data_file": str(tmp_data_path), "model": "claude-haiku-3"}
    with patch("todo_agent.config.load_config", return_value=config), \
         patch("todo_agent.config.get_data_file_path", return_value=tmp_data_path):
        yield config


def make_mock_tool_response(tool_name: str, tool_input: dict):
    """
    Return a mock anthropic.types.Message with a single tool_use content block.
    Used to stub client.messages.create in CLI integration tests.
    """
    tool_use_block = MagicMock()
    tool_use_block.type = "tool_use"
    tool_use_block.name = tool_name
    tool_use_block.input = tool_input

    message = MagicMock()
    message.content = [tool_use_block]
    return message

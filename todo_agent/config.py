"""Configuration management for todo-agent.

Reads and writes ~/.todo-agent/config.json. Creates the directory and
default config on first run. The TODO_DATA_FILE environment variable
overrides the data_file value from the config.
"""
import json
import os
from pathlib import Path

_TODO_DIR = Path.home() / ".todo-agent"
_CONFIG_PATH = _TODO_DIR / "config.json"
_DEFAULTS = {
    "data_file": str(_TODO_DIR / "todos.json"),
    "model": "claude-haiku-4-5-20251001",
}


def load_config() -> dict:
    """Read config.json, creating the directory and file with defaults if absent."""
    _TODO_DIR.mkdir(parents=True, exist_ok=True)
    if not _CONFIG_PATH.exists():
        _CONFIG_PATH.write_text(json.dumps(_DEFAULTS, indent=2))
    with _CONFIG_PATH.open() as f:
        config = json.load(f)
    # Merge any missing default keys (forward-compat)
    for key, val in _DEFAULTS.items():
        config.setdefault(key, val)
    return config


def get_data_file_path() -> Path:
    """Return the resolved Path to the data file, honouring the env var override."""
    env_override = os.environ.get("TODO_DATA_FILE")
    if env_override:
        return Path(env_override).expanduser()
    config = load_config()
    return Path(config["data_file"]).expanduser()

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


def get_inbox_dir() -> Path:
    """Return the Path to the inbox directory (~/.todo-agent/inbox/)."""
    return _TODO_DIR / "inbox"


def get_log_path() -> Path:
    """Return the Path to the API call log (~/.todo-agent/api-calls.jsonl)."""
    return _TODO_DIR / "api-calls.jsonl"


# Haiku 4.5 prices in USD per million tokens, last verified 2026-09-22.
# Update last_verified when re-confirming against console.anthropic.com.
PRICE_TABLE = {
    "input": 1.00,
    "cache_write_5m": 1.25,
    "cache_write_1h": 2.00,
    "cache_read": 0.10,
    "output": 5.00,
    "last_verified": "2026-09-22",
}

# Minimum token count for a prefix to qualify for prompt caching on Haiku 4.5.
# Source: Anthropic documentation, last verified 2026-09-22.
MIN_CACHEABLE_PREFIX_TOKENS = 4096

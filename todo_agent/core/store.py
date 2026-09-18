"""Atomic JSON read/write for the to-do agent data store.

This is the ONLY module that reads from or writes to todos.json.
Neither cli/ nor gui/ may touch the data file directly.
"""
import json
import math
import os
import tempfile
from pathlib import Path

from todo_agent.config import get_data_file_path

_EMPTY_STORE = {"version": "1", "lanes": []}


def load_data() -> dict:
    """Read the data file, creating it with an empty store if it does not exist."""
    path = get_data_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(json.dumps(_EMPTY_STORE, indent=2))
        return json.loads(json.dumps(_EMPTY_STORE))  # return a fresh copy
    with path.open() as f:
        return json.load(f)


def save_data(data: dict) -> None:
    """Write data to the data file atomically using a temp file + os.replace."""
    path = get_data_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, indent=2)
    # Write to a temp file in the same directory so os.replace is atomic
    dir_ = path.parent
    with tempfile.NamedTemporaryFile(
        mode="w", dir=dir_, delete=False, suffix=".tmp", encoding="utf-8"
    ) as tf:
        tf.write(content)
        tmp_path = tf.name
    os.replace(tmp_path, path)


def recalculate_percent_complete(project: dict) -> None:
    """Mutate project['percent_complete'] in place based on current item statuses.

    Rules:
    - null  when items list is empty (not started vs truly 0%)
    - floor(completed / total * 100)  otherwise
    """
    items = project.get("items", [])
    if not items:
        project["percent_complete"] = None
        return
    completed = sum(1 for item in items if item.get("status") == "completed")
    project["percent_complete"] = math.floor(completed / len(items) * 100)

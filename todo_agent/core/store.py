"""Atomic JSON read/write for the to-do agent data store.

This is the ONLY module that reads from or writes to todos.json.
Neither cli/ nor gui/ may touch the data file directly.
"""
import json
import math
import os
import tempfile
from datetime import date
from pathlib import Path

from todo_agent.config import get_data_file_path

_EMPTY_STORE = {"version": "1", "lanes": []}


def apply_deadline_flags(data: dict) -> None:
    """Additively set today/this_week flags based on each item's deadline.

    Applied in-memory only — never written back to the JSON file.
    Manually-set flags are never cleared (additive only).
    """
    today = date.today()
    today_iso = today.isocalendar()[:2]  # (ISO year, ISO week)
    for lane in data.get("lanes", []):
        for project in lane.get("projects", []):
            for item in project.get("items", []):
                deadline_str = item.get("deadline")
                if not deadline_str:
                    continue
                try:
                    deadline = date.fromisoformat(deadline_str)
                except (ValueError, TypeError):
                    continue
                if deadline == today:
                    item["today"] = True
                if deadline.isocalendar()[:2] == today_iso:
                    item["this_week"] = True


def load_data() -> dict:
    """Read the data file, creating it with an empty store if it does not exist."""
    path = get_data_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(json.dumps(_EMPTY_STORE, indent=2))
        data = json.loads(json.dumps(_EMPTY_STORE))
        apply_deadline_flags(data)
        return data
    with path.open() as f:
        data = json.load(f)
    apply_deadline_flags(data)
    return data


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

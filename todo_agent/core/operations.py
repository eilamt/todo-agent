"""All business logic operations for the to-do agent.

This module is the sole consumer of core.store — it reads and writes data
exclusively through load_data() / save_data(). Neither cli/ nor gui/ may
call store functions directly.

Operations are grouped:
  - Name-resolution helpers (_find_*)
  - Add operations
  - Status / flag / field update operations
  - Delete operations (with preview helper)
  - Note operations
  - ID-based lookup helpers (used by GUI server)
"""
import re
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

from todo_agent.core.models import (
    PROJECT_STATUSES,
    ITEM_STATUSES,
    validate_importance,
    validate_item_status,
    validate_project_status,
)
from todo_agent.core.store import load_data, recalculate_percent_complete, save_data


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class AmbiguousMatchError(Exception):
    """Raised when a name matches more than one entity at the same level."""


# ---------------------------------------------------------------------------
# Name-resolution helpers
# ---------------------------------------------------------------------------

def _find_lane(data: dict, lane_name: str) -> dict:
    """Case-insensitive lane lookup. Raises ValueError if not found."""
    for lane in data["lanes"]:
        if lane["name"].lower() == lane_name.lower():
            return lane
    raise ValueError(f"Lane '{lane_name}' not found.")


def _find_project(data: dict, project_name: str, lane_name: str | None = None) -> tuple[dict, dict]:
    """Return (lane, project).

    If lane_name is given, search only that lane.
    If multiple lanes contain a project with the same name and lane_name is not
    given, raise AmbiguousMatchError.
    """
    target_lanes = data["lanes"]
    if lane_name is not None:
        target_lanes = [_find_lane(data, lane_name)]

    matches = []
    for lane in target_lanes:
        for project in lane["projects"]:
            if project["name"].lower() == project_name.lower():
                matches.append((lane, project))

    if len(matches) == 0:
        ctx = f" in lane '{lane_name}'" if lane_name else ""
        raise ValueError(f"Project '{project_name}' not found{ctx}.")
    if len(matches) > 1:
        locations = ", ".join(
            f"'{m[0]['name']}/{m[1]['name']}'" for m in matches
        )
        raise AmbiguousMatchError(
            f"Multiple projects named '{project_name}' found: {locations}. "
            "Please specify the lane name."
        )
    return matches[0]


def _find_item(
    data: dict,
    item_title: str,
    project_name: str | None = None,
    lane_name: str | None = None,
) -> tuple[dict, dict, dict]:
    """Return (lane, project, item).

    Narrows search by project_name and/or lane_name when provided.
    Raises AmbiguousMatchError if multiple matches exist.
    """
    if project_name is not None:
        lane, project = _find_project(data, project_name, lane_name)
        target_projects = [(lane, project)]
    elif lane_name is not None:
        lane = _find_lane(data, lane_name)
        target_projects = [(lane, p) for p in lane["projects"]]
    else:
        target_projects = [
            (lane, project)
            for lane in data["lanes"]
            for project in lane["projects"]
        ]

    matches = []
    for lane, project in target_projects:
        for item in project["items"]:
            if item["title"].lower() == item_title.lower():
                matches.append((lane, project, item))

    if len(matches) == 0:
        raise ValueError(f"Item '{item_title}' not found.")
    if len(matches) > 1:
        locations = ", ".join(
            f"'{m[0]['name']}/{m[1]['name']}/{m[2]['title']}'" for m in matches
        )
        raise AmbiguousMatchError(
            f"Multiple items named '{item_title}' found: {locations}. "
            "Please specify the project name."
        )
    return matches[0]


# ---------------------------------------------------------------------------
# Add operations
# ---------------------------------------------------------------------------

def add_lane(name: str) -> dict:
    """Create a new lane and auto-create its blank Markdown instructions file."""
    data = load_data()

    # Uniqueness check (case-insensitive)
    for lane in data["lanes"]:
        if lane["name"].lower() == name.lower():
            raise ValueError(f"Lane '{name}' already exists.")

    lane_id = str(uuid.uuid4())
    slug = re.sub(r"[^a-z0-9-]", "", name.lower().replace(" ", "-"))
    instructions_dir = Path.home() / ".todo-agent" / "lanes"
    instructions_dir.mkdir(parents=True, exist_ok=True)
    instructions_path = instructions_dir / f"{slug}.md"
    instructions_path.touch()

    new_lane = {
        "id": lane_id,
        "name": name,
        "instructions_file": str(instructions_path),
        "projects": [],
    }
    data["lanes"].append(new_lane)
    save_data(data)
    return new_lane


def add_project(lane_name: str, project_name: str, importance: int = 50) -> dict:
    """Create a new project inside a lane."""
    validate_importance(importance)
    data = load_data()
    lane = _find_lane(data, lane_name)

    # Uniqueness check within lane
    for project in lane["projects"]:
        if project["name"].lower() == project_name.lower():
            raise ValueError(f"Project '{project_name}' already exists in lane '{lane_name}'.")

    new_project = {
        "id": str(uuid.uuid4()),
        "name": project_name,
        "status": "not-started",
        "importance": importance,
        "start_date": None,
        "percent_complete": None,
        "notes": [],
        "items": [],
    }
    lane["projects"].append(new_project)
    save_data(data)
    return new_project


def add_item(project_name: str, item_title: str, lane_name: str | None = None, description: str | None = None, importance: int = 50) -> dict:
    """Create a new item inside a project."""
    data = load_data()
    lane, project = _find_project(data, project_name, lane_name)

    # Uniqueness check within project
    for item in project["items"]:
        if item["title"].lower() == item_title.lower():
            raise ValueError(
                f"Item '{item_title}' already exists in project '{project_name}'."
            )

    new_item = {
        "id": str(uuid.uuid4()),
        "title": item_title,
        "status": "not-started",
        "today": False,
        "this_week": False,
        "deadline": None,
        "push_count": 0,
        "notes": [],
        "description": description if description and description.strip() else None,
        "importance": importance,
    }
    project["items"].append(new_item)
    recalculate_percent_complete(project)
    save_data(data)
    return new_item


# ---------------------------------------------------------------------------
# Status / flag / field update operations
# ---------------------------------------------------------------------------

def set_item_status(
    item_title: str,
    status: str,
    project_name: str | None = None,
    lane_name: str | None = None,
) -> dict:
    """Change an item's status and recalculate the parent project's percent_complete."""
    validate_item_status(status)
    data = load_data()
    lane, project, item = _find_item(data, item_title, project_name, lane_name)
    item["status"] = status
    recalculate_percent_complete(project)
    save_data(data)
    return item


def set_today(
    item_title: str,
    value: bool,
    project_name: str | None = None,
    lane_name: str | None = None,
) -> dict:
    """Set or clear the today flag without touching this_week."""
    data = load_data()
    lane, project, item = _find_item(data, item_title, project_name, lane_name)
    item["today"] = bool(value)
    save_data(data)
    return item


def set_this_week(
    item_title: str,
    value: bool,
    project_name: str | None = None,
    lane_name: str | None = None,
) -> dict:
    """Set or clear the this_week flag without touching today."""
    data = load_data()
    lane, project, item = _find_item(data, item_title, project_name, lane_name)
    item["this_week"] = bool(value)
    save_data(data)
    return item


def set_deadline(
    item_title: str,
    deadline: str | None,
    project_name: str | None = None,
    lane_name: str | None = None,
) -> dict:
    """Set or clear an item's deadline. deadline must be YYYY-MM-DD or None."""
    if deadline is not None:
        date.fromisoformat(deadline)  # raises ValueError if invalid
    data = load_data()
    lane, project, item = _find_item(data, item_title, project_name, lane_name)
    item["deadline"] = deadline
    save_data(data)
    return item


def set_project_status(
    project_name: str,
    status: str,
    start_date: str | None = None,
    lane_name: str | None = None,
) -> dict:
    """Change a project's status. start_date required when status is 'scheduled'."""
    validate_project_status(status)
    if status == "scheduled":
        if not start_date:
            raise ValueError("start_date is required when status is 'scheduled'.")
        date.fromisoformat(start_date)  # validates format
    data = load_data()
    lane, project = _find_project(data, project_name, lane_name)
    project["status"] = status
    if start_date is not None:
        project["start_date"] = start_date
    save_data(data)
    return project


def set_importance(
    project_name: str,
    importance: int,
    lane_name: str | None = None,
) -> dict:
    """Set a project's importance score (0–100)."""
    validate_importance(importance)
    data = load_data()
    lane, project = _find_project(data, project_name, lane_name)
    project["importance"] = importance
    save_data(data)
    return project


# ---------------------------------------------------------------------------
# Delete operations
# ---------------------------------------------------------------------------

def get_delete_preview(
    data: dict,
    entity_type: str,
    lane_name: str | None = None,
    project_name: str | None = None,
    item_title: str | None = None,
) -> dict:
    """Return entity name and child counts without modifying data."""
    if entity_type == "lane":
        lane = _find_lane(data, lane_name)
        projects_count = len(lane["projects"])
        items_count = sum(len(p["items"]) for p in lane["projects"])
        return {"name": lane["name"], "projects_count": projects_count, "items_count": items_count}
    elif entity_type == "project":
        lane, project = _find_project(data, project_name, lane_name)
        return {"name": project["name"], "projects_count": None, "items_count": len(project["items"])}
    elif entity_type == "item":
        lane, project, item = _find_item(data, item_title, project_name, lane_name)
        return {"name": item["title"], "projects_count": None, "items_count": 0}
    else:
        raise ValueError(f"Unknown entity_type: {entity_type!r}")


def delete_lane(lane_name: str) -> dict:
    """Delete a lane and all its projects and items."""
    data = load_data()
    lane = _find_lane(data, lane_name)
    projects_deleted = len(lane["projects"])
    items_deleted = sum(len(p["items"]) for p in lane["projects"])
    data["lanes"] = [l for l in data["lanes"] if l["id"] != lane["id"]]
    save_data(data)
    return {
        "lane_name": lane["name"],
        "projects_deleted": projects_deleted,
        "items_deleted": items_deleted,
    }


def delete_project(project_name: str, lane_name: str | None = None) -> dict:
    """Delete a project and all its items."""
    data = load_data()
    lane, project = _find_project(data, project_name, lane_name)
    items_deleted = len(project["items"])
    lane["projects"] = [p for p in lane["projects"] if p["id"] != project["id"]]
    save_data(data)
    return {"project_name": project["name"], "items_deleted": items_deleted}


def delete_item(
    item_title: str,
    project_name: str | None = None,
    lane_name: str | None = None,
) -> dict:
    """Delete a single item and recalculate the parent project's percent_complete."""
    data = load_data()
    lane, project, item = _find_item(data, item_title, project_name, lane_name)
    project["items"] = [i for i in project["items"] if i["id"] != item["id"]]
    recalculate_percent_complete(project)
    save_data(data)
    return {
        "item_title": item["title"],
        "project_percent_complete": project["percent_complete"],
    }


# ---------------------------------------------------------------------------
# Description / importance update operations
# ---------------------------------------------------------------------------

def set_item_description(
    item_title: str,
    description: str | None,
    project_name: str | None = None,
    lane_name: str | None = None,
) -> dict:
    """Set or clear an item's free-text description."""
    data = load_data()
    lane, project, item = _find_item(data, item_title, project_name, lane_name)
    # Normalise: empty / whitespace string → None
    if description is not None and not description.strip():
        description = None
    item["description"] = description
    save_data(data)
    return item


def set_item_importance(
    item_title: str,
    importance: int,
    project_name: str | None = None,
    lane_name: str | None = None,
) -> dict:
    """Set an item's importance score (0–100)."""
    validate_importance(importance)
    data = load_data()
    lane, project, item = _find_item(data, item_title, project_name, lane_name)
    item["importance"] = importance
    save_data(data)
    return item


# ---------------------------------------------------------------------------
# Rename operations
# ---------------------------------------------------------------------------

def rename_item(
    item_title: str,
    new_title: str,
    project_name: str | None = None,
    lane_name: str | None = None,
) -> dict:
    """Rename an item. new_title must be non-empty and unique within its project."""
    new_title = new_title.strip() if new_title else ""
    if not new_title:
        raise ValueError("Item title must not be empty.")
    data = load_data()
    lane, project, item = _find_item(data, item_title, project_name, lane_name)
    # Case-insensitive uniqueness check within the project (skip self)
    for other in project["items"]:
        if other["id"] != item["id"] and other["title"].lower() == new_title.lower():
            raise ValueError(
                f"Item '{new_title}' already exists in project '{project['name']}'."
            )
    item["title"] = new_title
    save_data(data)
    return item


def rename_project(
    project_name: str,
    new_name: str,
    lane_name: str | None = None,
) -> dict:
    """Rename a project. new_name must be non-empty and unique within its lane."""
    new_name = new_name.strip() if new_name else ""
    if not new_name:
        raise ValueError("Project name must not be empty.")
    data = load_data()
    lane, project = _find_project(data, project_name, lane_name)
    # Case-insensitive uniqueness check within the lane (skip self)
    for other in lane["projects"]:
        if other["id"] != project["id"] and other["name"].lower() == new_name.lower():
            raise ValueError(
                f"Project '{new_name}' already exists in lane '{lane['name']}'."
            )
    project["name"] = new_name
    save_data(data)
    return project


# ---------------------------------------------------------------------------
# Note operations
# ---------------------------------------------------------------------------

def add_project_note(
    project_name: str,
    text: str,
    lane_name: str | None = None,
) -> dict:
    """Append a timestamped note to a project."""
    if not text or not text.strip():
        raise ValueError("Note text must not be empty.")
    data = load_data()
    lane, project = _find_project(data, project_name, lane_name)
    note = {
        "text": text,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    project["notes"].append(note)
    save_data(data)
    return note


def add_item_note(
    item_title: str,
    text: str,
    project_name: str | None = None,
    lane_name: str | None = None,
) -> dict:
    """Append a timestamped note to an item."""
    if not text or not text.strip():
        raise ValueError("Note text must not be empty.")
    data = load_data()
    lane, project, item = _find_item(data, item_title, project_name, lane_name)
    note = {
        "text": text,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    item["notes"].append(note)
    save_data(data)
    return note


def list_notes(
    entity_type: str,
    name: str,
    project_name: str | None = None,
    lane_name: str | None = None,
) -> list:
    """Return all notes for a project or item (read-only, no data modification)."""
    if entity_type not in ("project", "item"):
        raise ValueError(
            f"entity_type must be 'project' or 'item', got {entity_type!r}."
        )
    data = load_data()
    if entity_type == "project":
        lane, project = _find_project(data, name, lane_name)
        return project.get("notes", [])
    else:
        lane, project, item = _find_item(data, name, project_name, lane_name)
        return item.get("notes", [])


# ---------------------------------------------------------------------------
# ID-based lookup helpers (used exclusively by gui/server.py)
# ---------------------------------------------------------------------------

def _find_lane_by_id(data: dict, lane_id: str) -> dict:
    """Raise ValueError if lane not found by ID."""
    for lane in data["lanes"]:
        if lane["id"] == lane_id:
            return lane
    raise ValueError(f"Lane not found.")


def _find_project_by_id(data: dict, project_id: str) -> tuple[dict, dict]:
    """Return (lane, project). Raise ValueError if not found."""
    for lane in data["lanes"]:
        for project in lane["projects"]:
            if project["id"] == project_id:
                return lane, project
    raise ValueError(f"Project not found.")


def _find_item_by_id(data: dict, item_id: str) -> tuple[dict, dict, dict]:
    """Return (lane, project, item). Raise ValueError if not found."""
    for lane in data["lanes"]:
        for project in lane["projects"]:
            for item in project["items"]:
                if item["id"] == item_id:
                    return lane, project, item
    raise ValueError(f"Item not found.")


# ---------------------------------------------------------------------------
# Read operations (query-only, no state mutation)
# ---------------------------------------------------------------------------

def list_lanes() -> list[dict]:
    """Return all lanes with id, name, and project_count."""
    data = load_data()
    return [
        {"id": lane["id"], "name": lane["name"], "project_count": len(lane["projects"])}
        for lane in data["lanes"]
    ]


def list_projects(lane_name: str | None = None) -> list[dict]:
    """Return all projects, optionally filtered by lane name (case-insensitive)."""
    data = load_data()
    results = []
    for lane in data["lanes"]:
        if lane_name and lane["name"].lower() != lane_name.lower():
            continue
        for project in lane["projects"]:
            results.append({
                "id": project["id"],
                "name": project["name"],
                "lane": lane["name"],
                "importance": project.get("importance", 50),
                "status": project["status"],
                "percent_complete": project.get("percent_complete", 0),
                "item_count": len(project.get("items", [])),
            })
    return results


def list_items(project_name: str | None = None, lane_name: str | None = None) -> list[dict]:
    """Return all items, optionally filtered by project and/or lane name (case-insensitive)."""
    data = load_data()
    results = []
    for lane in data["lanes"]:
        if lane_name and lane["name"].lower() != lane_name.lower():
            continue
        for project in lane["projects"]:
            if project_name and project["name"].lower() != project_name.lower():
                continue
            for item in project.get("items", []):
                results.append({
                    "id": item["id"],
                    "title": item["title"],
                    "project": project["name"],
                    "lane": lane["name"],
                    "status": item["status"],
                    "today": item.get("today", False),
                    "this_week": item.get("this_week", False),
                    "deadline": item.get("deadline"),
                    "importance": item.get("importance", 50),
                    "description": item.get("description"),
                })
    return results


def get_item(item_title: str, project_name: str | None = None, lane_name: str | None = None) -> dict:
    """Return full details for a single item by title.

    Raises:
        ValueError: if no item is found with that title.
        AmbiguousMatchError: if multiple items match (use project_name/lane_name to disambiguate).
    """
    data = load_data()
    lane, project, item = _find_item(data, item_title, project_name, lane_name)
    return {
        "id": item["id"],
        "title": item["title"],
        "project": project["name"],
        "lane": lane["name"],
        "status": item["status"],
        "today": item.get("today", False),
        "this_week": item.get("this_week", False),
        "deadline": item.get("deadline"),
        "importance": item.get("importance", 50),
        "description": item.get("description"),
        "notes": item.get("notes", []),
    }

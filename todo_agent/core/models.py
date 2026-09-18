"""Pure dataclasses and validation constants for the to-do agent data model.

No ORM, no persistence — this module only defines structure and validates values.
"""
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Status enums (stored as plain strings in JSON)
# ---------------------------------------------------------------------------

PROJECT_STATUSES = ["not-started", "scheduled", "in-progress", "completed"]
ITEM_STATUSES = ["not-started", "in-progress", "completed"]


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_importance(value: int) -> None:
    """Raise ValueError if importance is outside 0–100."""
    if not isinstance(value, int) or not (0 <= value <= 100):
        raise ValueError(f"importance must be an integer 0–100, got {value!r}")


def validate_project_status(status: str) -> None:
    """Raise ValueError if status is not a valid project status."""
    if status not in PROJECT_STATUSES:
        raise ValueError(
            f"Invalid project status {status!r}. "
            f"Valid values: {PROJECT_STATUSES}"
        )


def validate_item_status(status: str) -> None:
    """Raise ValueError if status is not a valid item status."""
    if status not in ITEM_STATUSES:
        raise ValueError(
            f"Invalid item status {status!r}. "
            f"Valid values: {ITEM_STATUSES}"
        )


# ---------------------------------------------------------------------------
# Dataclasses (represent the JSON structure in memory)
# ---------------------------------------------------------------------------

@dataclass
class Note:
    text: str
    created_at: str  # ISO 8601 UTC, e.g. "2026-09-17T10:00:00Z"


@dataclass
class Item:
    id: str
    title: str
    status: str = "not-started"
    today: bool = False
    this_week: bool = False
    deadline: str | None = None
    push_count: int = 0
    notes: list = field(default_factory=list)
    description: str | None = None
    importance: int = 50


@dataclass
class Project:
    id: str
    name: str
    status: str = "not-started"
    importance: int = 50
    start_date: str | None = None
    percent_complete: int | None = None
    notes: list = field(default_factory=list)
    items: list = field(default_factory=list)


@dataclass
class Lane:
    id: str
    name: str
    instructions_file: str
    projects: list = field(default_factory=list)

# Data Model: Board Enhancements

**Date**: 2026-09-18

## Changed entity: Item

**File**: `todo_agent/core/models.py`

### New field

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `this_weekend` | `bool` | `False` | True when the item is flagged for this weekend. Independent of `today` and `this_week`. |

### Updated dataclass

```python
@dataclass
class Item:
    id: str
    title: str
    status: str = "not-started"
    today: bool = False
    this_week: bool = False
    this_weekend: bool = False   # ← new
    deadline: str | None = None
    push_count: int = 0
    notes: list = field(default_factory=list)
    description: str | None = None
    importance: int = 50
```

### Backward compatibility

Existing JSON items without `this_weekend` are safe. All read paths that access the field use `item.get("this_weekend", False)`, so missing keys default to `False` without error or migration.

---

## Changed entity: Lane (ordering)

**File**: `todo_agent/core/models.py` — no field changes

The `Lane.projects` list and the top-level `data["lanes"]` list already encode display order via array position. No new fields are needed; the two new operations (`reorder_lane`, `reorder_project`) manipulate those lists in-place.

---

## New operations in `todo_agent/core/operations.py`

### `set_this_weekend`

```
set_this_weekend(item_title, value, project_name=None, lane_name=None) -> dict
```

Sets or clears `this_weekend` on a single item. Identical implementation pattern to `set_today` and `set_this_week`.

**Validation**: `value` coerced to `bool`. Item must exist (raises `ValueError` / `AmbiguousMatchError` via `_find_item`).

---

### `reorder_lane`

```
reorder_lane(lane_id: str, new_index: int) -> None
```

Moves the lane with `lane_id` to position `new_index` in `data["lanes"]`.

**Algorithm**:
1. `load_data()`
2. Find lane by `id` field; raise `ValueError` if not found.
3. Remove lane from list; clamp `new_index` to `[0, len(lanes)]`; insert at `new_index`.
4. `save_data(data)`

**Validation**: `new_index` must be a non-negative integer; clamped (not rejected) if out of range to make the API forgiving of off-by-one from the frontend.

---

### `reorder_project`

```
reorder_project(project_id: str, new_index: int) -> None
```

Moves the project with `project_id` to position `new_index` within its parent lane's `projects` list.

**Algorithm**:
1. `load_data()`
2. `_find_project_by_id(data, project_id)` → `(lane, project)`; raise `ValueError` if not found.
3. Remove project from `lane["projects"]`; clamp `new_index`; insert at `new_index`.
4. `save_data(data)`

**Validation**: Same as `reorder_lane` — index clamped, not rejected.

---

## Read-path changes

### `list_items()` in `operations.py`

Add `"this_weekend": item.get("this_weekend", False)` to the returned dict per item (alongside existing `today` / `this_week`).

### `get_item()` in `operations.py`

Add `"this_weekend": item.get("this_weekend", False)` to the returned dict.

### `add_item()` in `operations.py`

Add `"this_weekend": False` to the `new_item` dict literal.

---

## JSON representation (unchanged structure, new field)

```json
{
  "lanes": [
    {
      "id": "uuid",
      "name": "Work",
      "instructions_file": "/path/to/work.md",
      "projects": [
        {
          "id": "uuid",
          "name": "Website",
          "items": [
            {
              "id": "uuid",
              "title": "Fix login bug",
              "status": "not-started",
              "today": false,
              "this_week": true,
              "this_weekend": false,
              "deadline": null,
              "push_count": 0,
              "notes": [],
              "description": null,
              "importance": 50
            }
          ]
        }
      ]
    }
  ]
}
```

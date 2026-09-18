# Data Model: GUI Inline Editing

This feature adds **no new fields** to the data schema. It exposes existing Item and Project fields for editing through the GUI that were previously read-only in the GUI.

## Existing Fields Now Made Editable via GUI

### Item (editable fields added in this spec)

| Field         | Type           | Validation                          | Edit UI          |
|---------------|----------------|-------------------------------------|------------------|
| `title`       | string         | Non-empty, unique within project    | Inline text input |
| `description` | string \| null | Optional; empty string → null       | Inline textarea  |
| `importance`  | integer 0–100  | Must be integer in [0, 100]         | Inline number input |
| `today`       | boolean        | true / false                        | Checkbox (immediate) |
| `this_week`   | boolean        | true / false                        | Checkbox (immediate) |
| `deadline`    | string \| null | ISO date YYYY-MM-DD or null         | Date input (immediate) |

Fields already editable in GUI before this spec (unchanged): `status` (select dropdown).

Fields remaining read-only in GUI: `id`, `push_count`, `notes`, `percent_complete` (derived).

### Project (editable fields added in this spec)

| Field         | Type           | Validation                          | Edit UI          |
|---------------|----------------|-------------------------------------|------------------|
| `name`        | string         | Non-empty, unique within lane       | Inline text input |
| `importance`  | integer 0–100  | Must be integer in [0, 100]         | Inline number input |

Fields already editable in GUI before this spec (unchanged): `status` (select dropdown).

Fields remaining read-only in GUI: `id`, `start_date`, `percent_complete` (derived), `notes`.

## New Backend Operations Required

Two new operations are added to `core/operations.py`:

### `rename_item(item_title, new_title, project_name, lane_name) → dict`

- Finds item by current title (with project/lane disambiguation)
- Validates new_title is non-empty
- Checks new_title is not already used by another item in the same project (case-insensitive)
- Updates `item["title"]` and saves
- Returns the updated item dict

### `rename_project(project_name, new_name, lane_name) → dict`

- Finds project by current name (with lane disambiguation)
- Validates new_name is non-empty
- Checks new_name is not already used by another project in the same lane (case-insensitive)
- Updates `project["name"]` and saves
- Returns the updated project dict

## UI-Only State (Not Persisted)

| State            | Scope       | Default    | Notes                              |
|------------------|-------------|------------|------------------------------------|
| Card collapsed   | Per item    | Expanded   | Reset on board re-render           |
| Global collapsed | Board-level | Expanded   | Drives "Collapse all / Expand all" |

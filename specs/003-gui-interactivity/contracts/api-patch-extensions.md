# API Contract: PATCH Extensions for GUI Inline Editing

## PATCH /api/items/:id (extended)

Existing fields accepted: `status`, `today`, `this_week`, `deadline`

**New fields added by this spec:**

| Field         | Type            | Validation                          | Backend operation           |
|---------------|-----------------|-------------------------------------|-----------------------------|
| `title`       | string          | Non-empty                           | `rename_item`               |
| `description` | string \| null  | null or non-empty string            | `set_item_description`      |
| `importance`  | integer         | 0 ≤ importance ≤ 100                | `set_item_importance`       |

**Example request body:**
```json
{ "title": "Updated title" }
```
```json
{ "description": "needs mobile-first approach" }
```
```json
{ "description": null }
```
```json
{ "importance": 90 }
```

**Response (200 OK):**
```json
{
  "item": { ...full updated item dict... },
  "project_percent_complete": 42
}
```

**Error responses:**
- `400 Bad Request` — validation failure (blank title, importance out of range, invalid deadline format)
- `404 Not Found` — item ID not found
- `409 Conflict` — new title already exists in the project

---

## PATCH /api/projects/:id (extended)

Existing fields accepted: `status`, `importance`

**New fields added by this spec:**

| Field | Type   | Validation                          | Backend operation   |
|-------|--------|-------------------------------------|---------------------|
| `name` | string | Non-empty, unique within lane       | `rename_project`    |

**Example request body:**
```json
{ "name": "New Project Name" }
```

**Response (200 OK):**
```json
{ ...full updated project dict... }
```

**Error responses:**
- `400 Bad Request` — blank name
- `404 Not Found` — project ID not found
- `409 Conflict` — new name already exists in the same lane

---

## New Backend Operations

### `rename_item(item_title, new_title, project_name, lane_name) → dict`

```
Input:  item_title (str), new_title (str), project_name (str), lane_name (str)
Output: updated item dict
Raises: ValueError if new_title is blank
        ValueError("already exists") if new_title already in project (→ 409)
```

### `rename_project(project_name, new_name, lane_name) → dict`

```
Input:  project_name (str), new_name (str), lane_name (str)
Output: updated project dict
Raises: ValueError if new_name is blank
        ValueError("already exists") if new_name already in lane (→ 409)
```

---

## Frontend Behaviour Contract

| Action                          | API call                                      | On success           | On error              |
|---------------------------------|-----------------------------------------------|----------------------|-----------------------|
| Edit item title (Enter/blur)    | `PATCH /api/items/:id { title }`              | Rerender card        | Revert to old title   |
| Edit item description           | `PATCH /api/items/:id { description }`        | Rerender card        | Revert                |
| Clear item description          | `PATCH /api/items/:id { description: null }`  | Hide description     | Revert                |
| Edit item importance            | `PATCH /api/items/:id { importance }`         | Rerender badge/highlight | Revert            |
| Toggle today                    | `PATCH /api/items/:id { today: bool }`        | Update badge         | Revert checkbox       |
| Toggle this_week                | `PATCH /api/items/:id { this_week: bool }`    | Update badge         | Revert checkbox       |
| Set/clear deadline              | `PATCH /api/items/:id { deadline }`           | Update badge         | Revert date input     |
| Edit project name (Enter/blur)  | `PATCH /api/projects/:id { name }`            | Rerender header      | Revert to old name    |
| Edit project importance         | `PATCH /api/projects/:id { importance }`      | Rerender meta        | Revert                |
| Collapse item card              | No API call (UI state only)                   | Hide card body       | N/A                   |
| Global collapse all             | No API call (UI state only)                   | Hide all card bodies | N/A                   |

# API Contract Additions: Board Enhancements

**Date**: 2026-09-18

These are the new and modified REST endpoints in `todo_agent/gui/server.py`.

---

## New: PATCH /api/lanes/<lane_id>/position

Moves a lane to a new position in the board's left-to-right order.

**Request**

```
PATCH /api/lanes/<lane_id>/position
Content-Type: application/json

{ "index": <int> }
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `index` | integer ≥ 0 | Yes | Zero-based target position. Clamped to `[0, len(lanes)-1]` if out of range. |

**Responses**

| Status | Body | When |
|--------|------|------|
| 200 | `{}` (empty JSON object) | Lane successfully moved |
| 400 | `{"error": "..."}` | `index` missing or not an integer |
| 404 | `{"error": "Lane not found."}` | `lane_id` does not match any lane |

---

## New: PATCH /api/projects/<project_id>/position

Moves a project to a new vertical position within its parent lane.

**Request**

```
PATCH /api/projects/<project_id>/position
Content-Type: application/json

{ "index": <int> }
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `index` | integer ≥ 0 | Yes | Zero-based target position within the lane. Clamped if out of range. |

**Responses**

| Status | Body | When |
|--------|------|------|
| 200 | `{}` (empty JSON object) | Project successfully moved |
| 400 | `{"error": "..."}` | `index` missing or not an integer |
| 404 | `{"error": "Project not found."}` | `project_id` does not match any project |

---

## Modified: PATCH /api/items/<item_id>

The existing endpoint handles `today` and `this_week` fields in the request body. It is extended to also handle `this_weekend`.

**Additional accepted field**

| Field | Type | Notes |
|-------|------|-------|
| `this_weekend` | boolean | Sets or clears the `this_weekend` flag. Independent of `today` and `this_week`. |

No change to status codes or response shape.

---

## Modified: GET /api/data

The full data snapshot returned by this endpoint will now include `this_weekend` in every item object (see [data-model.md](../data-model.md)). No structural change to the response — items gain one additional boolean field.

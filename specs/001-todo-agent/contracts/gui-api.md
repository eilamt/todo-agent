# GUI API Contract: Local HTTP Endpoints

**Feature**: `specs/001-todo-agent`
**Date**: 2026-09-17

---

## Overview

The GUI is a local Flask web application. The browser-side JavaScript communicates with it
via a small REST-style JSON API. All mutation endpoints call `core/operations.py` functions —
they do NOT access the JSON data file directly (constitution Principle II).

The server binds to `127.0.0.1` only and is never reachable from outside the local machine
(constitution Principle I).

**Base URL**: `http://127.0.0.1:<PORT>` (default port TBD in implementation; documented in
`quickstart.md`).

**Content-Type**: All request and response bodies are `application/json` unless noted.

---

## Endpoints

### `GET /`

Serve the single-page GUI HTML. Returns the `templates/index.html` file.

---

### `GET /api/data`

Return the full current data store state for polling.

**Response**: `200 OK`
```json
{
  "version": "1",
  "lanes": [ /* full nested structure — see data-model.md */ ]
}
```

**Polling support**: Includes a `Last-Modified` header derived from the data file's
modification timestamp. Clients SHOULD send `If-Modified-Since` on subsequent requests;
the server returns `304 Not Modified` when the file has not changed.

---

### `POST /api/lanes`

Create a new lane.

**Request body**:
```json
{ "name": "Health" }
```

**Response**: `201 Created`
```json
{
  "id": "<uuid>",
  "name": "Health",
  "instructions_file": "/Users/alice/.todo-agent/lanes/health.md",
  "projects": []
}
```

**Errors**:
- `400` — name missing or empty
- `409` — lane name already exists

---

### `DELETE /api/lanes/<lane_id>`

Delete a lane and cascade-delete all its projects and items.

**Note**: The GUI is responsible for showing a confirmation dialog (with entity name +
project/item counts) before calling this endpoint. The endpoint does not re-confirm; it
executes immediately on receipt (constitution Principle VII is enforced in the UI layer for
the GUI).

**Response**: `200 OK`
```json
{
  "deleted": {
    "lane_name": "Health",
    "projects_deleted": 2,
    "items_deleted": 7
  }
}
```

**Errors**:
- `404` — lane not found

---

### `POST /api/lanes/<lane_id>/projects`

Create a new project in a lane.

**Request body**:
```json
{
  "name": "Marathon Training",
  "importance": 80
}
```

**Response**: `201 Created`
```json
{
  "id": "<uuid>",
  "name": "Marathon Training",
  "status": "not-started",
  "importance": 80,
  "start_date": null,
  "percent_complete": null,
  "notes": [],
  "items": []
}
```

**Errors**:
- `400` — name missing or invalid importance value
- `404` — lane not found
- `409` — project name already exists in this lane

---

### `PATCH /api/projects/<project_id>`

Update a project's mutable fields. Send only the fields to change.

**Request body** (all fields optional):
```json
{
  "status": "in-progress",
  "start_date": null,
  "importance": 90
}
```

**Response**: `200 OK` — returns the updated project object (same shape as the project
within `GET /api/data`).

**Errors**:
- `400` — invalid field value (e.g., status not in enum, importance out of range)
- `404` — project not found

**Note**: `percent_complete`, `id`, `name`, `notes`, and `items` are not writable via this
endpoint. `name` changes are not supported in Phase 1.

---

### `DELETE /api/projects/<project_id>`

Delete a project and cascade-delete all its items. GUI confirms before calling.

**Response**: `200 OK`
```json
{
  "deleted": {
    "project_name": "Marathon Training",
    "items_deleted": 3
  }
}
```

**Errors**:
- `404` — project not found

---

### `POST /api/projects/<project_id>/items`

Create a new item in a project.

**Request body**:
```json
{
  "title": "Buy running shoes"
}
```

**Response**: `201 Created`
```json
{
  "id": "<uuid>",
  "title": "Buy running shoes",
  "status": "not-started",
  "today": false,
  "this_week": false,
  "deadline": null,
  "push_count": 0,
  "notes": []
}
```

**Errors**:
- `400` — title missing or empty
- `404` — project not found
- `409` — item title already exists in this project

---

### `PATCH /api/items/<item_id>`

Update an item's mutable fields. Send only the fields to change.

**Request body** (all fields optional):
```json
{
  "status": "completed",
  "today": false,
  "this_week": true,
  "deadline": "2026-10-01",
  "push_count": 1
}
```

**Response**: `200 OK` — returns the updated item object. Also returns the parent project's
updated `percent_complete` in a top-level field:

```json
{
  "item": { /* updated item */ },
  "project_percent_complete": 33
}
```

**Errors**:
- `400` — invalid field value (e.g., status not in enum, negative push_count)
- `404` — item not found

**Note**: `id`, `title`, and `notes` are not writable via this endpoint.

---

### `DELETE /api/items/<item_id>`

Delete a single item. GUI confirms before calling.

**Response**: `200 OK`
```json
{
  "deleted": {
    "item_title": "Buy running shoes"
  },
  "project_percent_complete": null
}
```

**Errors**:
- `404` — item not found

---

## Error Response Shape

All `4xx` errors return:
```json
{
  "error": "Human-readable description of the problem"
}
```

---

## Polling Contract

The browser polls `GET /api/data` on a fixed 5-second interval using:

```
GET /api/data
If-Modified-Since: <value from previous Last-Modified response header>
```

When the data file is unchanged, the server responds `304 Not Modified` with no body.
The browser keeps its current in-memory state unchanged.

When the data file has changed, the server responds `200 OK` with the full data payload.
The browser replaces its entire in-memory state and re-renders.

---

## Security Notes

- The Flask server MUST bind to `127.0.0.1` only, never `0.0.0.0`.
- No authentication is implemented (single-user, local-only tool).
- CORS is not configured; browser-to-localhost requests from the same origin require no CORS.

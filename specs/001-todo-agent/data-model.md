# Data Model: Personal To-Do Agent

**Feature**: `specs/001-todo-agent`
**Date**: 2026-09-17

---

## Overview

All state lives in a single JSON file (path configured in `~/.todo-agent/config.json`).
The file uses a nested structure — lanes contain projects, projects contain items — for
human readability (constitution Principle V). All access is exclusively through the shared
`core.store` module (constitution Principle II).

---

## JSON Schema

```json
{
  "version": "1",
  "lanes": [
    {
      "id": "<uuid4>",
      "name": "Work",
      "instructions_file": "/Users/alice/.todo-agent/lanes/work.md",
      "projects": [
        {
          "id": "<uuid4>",
          "name": "Website Redesign",
          "status": "in-progress",
          "importance": 75,
          "start_date": null,
          "percent_complete": 33,
          "notes": [
            {
              "text": "Kickoff meeting completed",
              "created_at": "2026-09-17T10:00:00Z"
            }
          ],
          "items": [
            {
              "id": "<uuid4>",
              "title": "Design homepage",
              "status": "not-started",
              "today": false,
              "this_week": true,
              "deadline": null,
              "push_count": 0,
              "notes": []
            }
          ]
        }
      ]
    }
  ]
}
```

---

## Entity Definitions

### Root

| Field | Type | Description |
|---|---|---|
| `version` | string | Schema version; `"1"` for Phase 1. Enables future migration. |
| `lanes` | array[Lane] | Ordered list of all lanes. |

---

### Lane

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `id` | string (UUID4) | yes | auto-generated | Stable identifier; never shown to user. |
| `name` | string | yes | — | Unique across all lanes. Non-empty. |
| `instructions_file` | string (path) | yes | auto-set | Absolute path to the lane's Markdown file. Auto-created as a blank file when the lane is added. User edits freely. |
| `projects` | array[Project] | yes | `[]` | Ordered list; order preserved as added. |

**Uniqueness**: Lane names are unique across the entire data store (case-insensitive comparison
for ambiguity resolution; stored as entered).

**Lane instructions file path convention**:
`{todo_agent_dir}/lanes/{slug}.md` where `slug` is the lane name lowercased with spaces
replaced by hyphens and non-alphanumeric characters removed.
Example: lane "Work & Life" → `~/.todo-agent/lanes/work-life.md`.

---

### Project

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `id` | string (UUID4) | yes | auto-generated | Stable identifier. |
| `name` | string | yes | — | Unique within its lane. Non-empty. |
| `status` | string (enum) | yes | `"not-started"` | See Status Enums below. |
| `importance` | integer | yes | `50` | Range 0–100 inclusive. |
| `start_date` | string \| null | yes | `null` | ISO 8601 date (`YYYY-MM-DD`). Meaningful only when `status == "scheduled"`; stored but not acted on in Phase 1. |
| `percent_complete` | integer \| null | yes | `null` | **Computed field** — never set directly. `null` when `items` is empty; otherwise `floor(completed_items / total_items * 100)`. Recalculated on every item status change. |
| `notes` | array[Note] | yes | `[]` | Append-only in Phase 1. |
| `items` | array[Item] | yes | `[]` | Ordered list. |

**Uniqueness**: Project names are unique within a lane (case-insensitive for resolution).

**Computed field rule**: Whenever any item in a project changes status, `percent_complete`
is recalculated immediately within the same write operation. The value stored in JSON always
reflects the true current state.

---

### Item

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `id` | string (UUID4) | yes | auto-generated | Stable identifier. |
| `title` | string | yes | — | Unique within its project. Non-empty. |
| `status` | string (enum) | yes | `"not-started"` | See Status Enums below. |
| `today` | boolean | yes | `false` | Work-on-today flag. Independent of `this_week`. |
| `this_week` | boolean | yes | `false` | Work-on-this-week flag. Independent of `today`. |
| `deadline` | string \| null | yes | `null` | ISO 8601 date (`YYYY-MM-DD`). |
| `push_count` | integer | yes | `0` | Number of times item was carried over (Phase 2 auto-increment; manually settable in Phase 1). Must be ≥ 0. |
| `notes` | array[Note] | yes | `[]` | Append-only in Phase 1. |

**Uniqueness**: Item titles are unique within a project (case-insensitive for resolution).

---

### Note

| Field | Type | Required | Notes |
|---|---|---|---|
| `text` | string | yes | Non-empty free text. |
| `created_at` | string | yes | ISO 8601 datetime with UTC timezone (`YYYY-MM-DDTHH:MM:SSZ`). Set at append time; never modified. |

Notes are immutable once written. No edit or delete operation exists in Phase 1.

---

## Status Enums

### Project Status

| Value | Meaning |
|---|---|
| `not-started` | Work has not begun. Default. |
| `scheduled` | Work is planned to begin on `start_date`. |
| `in-progress` | Work is actively underway. |
| `completed` | Work is done. |

Valid transitions: any status → any status (no enforced state machine; the user controls this).
`start_date` is meaningful only when status is `scheduled`. If status changes away from
`scheduled`, `start_date` is preserved in storage but ignored.

### Item Status

| Value | Meaning |
|---|---|
| `not-started` | Work has not begun. Default. |
| `in-progress` | Work is actively underway. |
| `completed` | Work is done. Contributes to `percent_complete` calculation. |

---

## Uniqueness & Name Resolution Rules

1. **Lane names**: unique across the entire store (case-insensitive match).
2. **Project names**: unique within a lane (case-insensitive match).
3. **Item titles**: unique within a project (case-insensitive match).
4. **Ambiguity resolution**: when the LLM-resolved action names an entity that matches
   more than one record at the target level, the `request_clarification` tool is used — no
   destructive action is taken.

---

## Computed Field: `percent_complete`

```
if len(project.items) == 0:
    percent_complete = null
else:
    completed = count of items where status == "completed"
    percent_complete = floor(completed / len(project.items) * 100)
```

This calculation is performed in `core.operations` on every write that modifies item status.
The result is stored back into the JSON so the file is always a consistent snapshot.

---

## File System Layout

```
~/.todo-agent/
├── config.json          # { "data_file": "...", "model": "..." }
├── todos.json           # main data store (path configurable in config.json)
└── lanes/
    ├── work.md          # lane instructions — auto-created blank, user-edited
    ├── personal.md
    └── health.md
```

The `~/.todo-agent/` directory and `config.json` are created on first run if absent.
Each lane's Markdown file is created (blank) when the lane is added via `add_lane`.

---

## Phase 2 Fields (stored now, not acted on)

The following fields are present in the Phase 1 schema specifically to avoid a migration later:

| Entity | Field | Phase 2 Use |
|---|---|---|
| Project | `importance` | Drive reminder frequency/tone |
| Project | `start_date` | Trigger reminder eligibility |
| Item | `push_count` | Track carry-over count; drive urgency signal |
| Lane | `instructions_file` | Source of reminder schedule/tone instructions |

None of these fields are read by any automated process in Phase 1.

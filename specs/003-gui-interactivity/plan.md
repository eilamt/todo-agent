# Implementation Plan: GUI Inline Editing

**Branch**: `003-gui-interactivity` | **Date**: 2026-09-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-gui-interactivity/spec.md`

## Summary

Add full inline-editing capability to the local web GUI for all mutable item and project fields. This is a pure frontend + thin backend-extension change: new `rename_item` and `rename_project` operations in the core, two new field handlers in the PATCH endpoints, and updated vanilla-JS rendering in `app.js` / `style.css` / `index.html`. No new dependencies, no schema changes.

## Technical Context

**Language/Version**: Python 3.11+ (backend), vanilla JavaScript ES2020 (frontend)

**Primary Dependencies**: Flask (existing), no new dependencies

**Storage**: Plain JSON file via existing `core/store.py` — no schema changes

**Testing**: pytest (existing) for new backend operations; manual browser validation per quickstart.md

**Target Platform**: Local desktop browser, served on 127.0.0.1 by Flask

**Project Type**: Local web GUI backed by Flask REST API

**Performance Goals**: All GUI saves complete within 1 second on localhost

**Constraints**: No new npm/JS dependencies; no new Python packages; pure CSS for animations

**Scale/Scope**: Single-user local tool; no concurrency concerns

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Local-first, no hosting | ✓ PASS | All changes are local; no network calls |
| II. Single source of truth | ✓ PASS | Server uses `core/operations.py` for all writes; GUI never touches the data file |
| III. Deterministic core | ✓ PASS | No LLM involvement; all operations are deterministic |
| IV. Simplicity over frameworks | ✓ PASS | No new dependencies; vanilla JS only |
| V. Human-readable state | ✓ PASS | No schema changes; data stays plain JSON |
| VI. Staged scope | ✓ PASS | No Phase 2 components |
| VII. User stays in control | ✓ PASS | Destructive actions still require confirmation; inline edits are non-destructive and reversible on error |

## Project Structure

### Documentation (this feature)

```text
specs/003-gui-interactivity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── api-patch-extensions.md
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (files modified by this feature)

```text
todo_agent/
├── core/
│   └── operations.py         # New: rename_item, rename_project
├── gui/
│   ├── server.py             # Extended: PATCH /api/items/:id + /api/projects/:id
│   └── static/
│       ├── app.js            # Major update: inline edit, flags, collapse
│       └── style.css         # New: edit-mode highlight, collapse toggle, bold names
└── templates/
    └── index.html            # Add: global Collapse all / Expand all button

tests/
└── unit/
    └── test_operations.py    # New: rename_item and rename_project tests
```

**Structure Decision**: Single-project layout unchanged from existing codebase. All GUI changes are in the existing `todo_agent/gui/static/` directory.

## Implementation Details

### Backend Changes

#### `core/operations.py` — two new operations

**`rename_item(item_title, new_title, project_name, lane_name)`**
- Find item via `_find_item(data, item_title, project_name, lane_name)`
- Validate `new_title.strip()` is non-empty
- Case-insensitive uniqueness check: no other item in the same project may have the same title
- `item["title"] = new_title.strip()`
- `save_data(data)`; return updated item

**`rename_project(project_name, new_name, lane_name)`**
- Find project via `_find_project(data, project_name, lane_name)`
- Validate `new_name.strip()` is non-empty
- Case-insensitive uniqueness check: no other project in the same lane may have the same name
- `project["name"] = new_name.strip()`
- `save_data(data)`; return updated project

#### `gui/server.py` — extend existing PATCH handlers

**`PATCH /api/items/:id`** — add three new field branches:
```python
if "title" in body:
    operations.rename_item(item["title"], body["title"], project["name"], lane["name"])
if "description" in body:
    operations.set_item_description(item["title"], body.get("description"), project["name"], lane["name"])
if "importance" in body:
    operations.set_item_importance(item["title"], body["importance"], project["name"], lane["name"])
```
Note: after rename, `item["title"]` changes — each handler must use the *current* item title at the time of call. Process `title` first if multiple fields are patched simultaneously.

**`PATCH /api/projects/:id`** — add one new field branch:
```python
if "name" in body:
    operations.rename_project(project["name"], body["name"], lane["name"])
```

Map `ValueError("already exists")` → HTTP 409; other `ValueError` → HTTP 400.

### Frontend Changes

#### `index.html`
- Add `<button id="collapse-all-btn">Collapse all</button>` to the `add-lane-area` section in the header.

#### `app.js` — inline edit helpers + card rebuild

**Inline edit factory** (`makeInlineEdit(displayEl, inputTag, getVal, saveAsync)`):
- Replaces `displayEl` with an `input` or `textarea` on click
- On Enter or blur: validates, calls `saveAsync(val)`, on success re-renders; on failure reverts
- Adds CSS class `editing` to the input for styling

**Item card changes in `buildItemCard`**:
- Title: wrap title text in a `<span>` with click → inline text input; PATCH `{title}`
- Description: if set, show editable `<p class="item-description">`; if null, show a small `+ add description` link that activates an inline textarea; clear button sets `description: null`
- Importance badge: click → inline number input (min 0, max 100); PATCH `{importance}`
- Today checkbox: `<input type="checkbox">` bound to `item.today`; `change` → PATCH `{today: bool}`
- This-week checkbox: same for `item.this_week`
- Deadline: `<input type="date">` pre-filled with `item.deadline || ""`; `change` → PATCH `{deadline}`; clear button → PATCH `{deadline: null}`
- Collapse toggle: `<button class="collapse-toggle">▼</button>` in the title row; toggles a `card-body` wrapper visibility; updates arrow direction

**Global collapse in `DOMContentLoaded`**:
- `document.getElementById("collapse-all-btn")` alternates between "Collapse all" / "Expand all" and sets all `.card-body` elements hidden/visible accordingly.

**Project header changes in `buildProjectSection`**:
- Project name: wrap in `<span>` with click → inline text input; PATCH `{name}`; display in bold (`font-weight: 700`)
- Project importance: show importance value as clickable number; click → inline number input; PATCH `{importance}`

#### `style.css` — new rules

```css
/* Inline edit input highlight */
.inline-edit-input { border: 2px solid #4299e1; border-radius: 3px; outline: none; padding: 0.1rem 0.3rem; }

/* Collapse toggle */
.collapse-toggle { background: none; border: none; cursor: pointer; font-size: 0.75rem; color: #888; padding: 0 0.3rem; }

/* Bold project name */
.project-title { font-weight: 700; color: #111; }

/* Saved flash */
@keyframes saved-flash { 0% { border-color: #4299e1; } 50% { border-color: #48bb78; } 100% { border-color: transparent; } }
.saved-flash { animation: saved-flash 1.5s ease-out; }
```

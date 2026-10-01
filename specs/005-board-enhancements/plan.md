# Implementation Plan: Board Enhancements

**Branch**: `005-board-enhancements` | **Date**: 2026-09-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/005-board-enhancements/spec.md`

## Summary

Three orthogonal board enhancements: (1) a `this_weekend` boolean flag on items — mirroring the existing `today`/`this_week` pattern end-to-end through the data model, operations, LLM tools, and GUI; (2) HTML5 drag-and-drop on lane column headers to reorder lanes left/right, persisted via a new `PATCH /api/lanes/<id>/position` endpoint; (3) HTML5 drag-and-drop on project cards within a lane to reorder them up/down, persisted via a new `PATCH /api/projects/<id>/position` endpoint. No new dependencies are introduced; all three share the existing Flask + vanilla-JS + plain-JSON stack.

## Technical Context

**Language/Version**: Python 3.11 (backend), ES2020 vanilla JavaScript (frontend)

**Primary Dependencies**: Flask 3.0 (web server), Anthropic SDK (LLM tool dispatch) — no new dependencies

**Storage**: Plain JSON file at `~/.todo-agent/data.json` via `todo_agent/core/store.py`. Lane and project ordering is already implicit in array position; no schema migration required for the drag-and-drop features.

**Testing**: pytest (unit tests in `tests/`)

**Target Platform**: Local desktop — server binds to 127.0.0.1 only

**Project Type**: Local web app (Flask backend + vanilla JS SPA frontend) with a natural-language CLI

**Performance Goals**: Standard local-app responsiveness — drag operations and flag toggles should feel instant (no perceptible delay for local file I/O)

**Constraints**: No new pip dependencies (Principle IV); no cloud/network calls; `core/operations.py` must remain the sole writer to the data store (Principle II)

**Scale/Scope**: Single-user, personal productivity tool; data file is typically under 1 MB

## Constitution Check

| Gate | Status | Notes |
|------|--------|-------|
| I. Local-First | ✅ Pass | All three features are purely local; no network calls introduced |
| II. Single Source of Truth | ✅ Pass | New `reorder_lane`/`reorder_project`/`set_this_weekend` operations go through `operations.py` → `store.py` |
| III. Deterministic Core | ✅ Pass | No LLM involvement in drag-and-drop; `set_this_weekend` is a plain flag-setter |
| IV. Simplicity Over Frameworks | ✅ Pass | HTML5 native drag-and-drop — no new JS library; no new Python package |
| V. Human-Readable State | ✅ Pass | No format changes; array order in JSON is human-readable |
| VI. Staged Scope | ✅ Pass | All three features are Phase 1 GUI/data-model additions |
| VII. User Stays in Control | ✅ Pass | Drag-and-drop is non-destructive; `this_weekend` toggle is reversible |

## Project Structure

### Documentation (this feature)

```text
specs/005-board-enhancements/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── quickstart.md        ← Phase 1 output
├── contracts/
│   ├── api-endpoints.md ← REST API contract additions
│   └── tool-schemas.md  ← LLM tool schema additions
└── tasks.md             ← Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
todo_agent/
├── core/
│   ├── models.py          ← add this_weekend: bool = False to Item
│   ├── operations.py      ← add set_this_weekend(), reorder_lane(), reorder_project()
│   └── store.py           ← no changes (load/save pattern unchanged)
├── tools.py               ← add set_this_weekend tool definition
├── cli/
│   ├── agent.py           ← add set_this_weekend branch in tool dispatch
│   └── main.py            ← no changes
└── gui/
    ├── server.py          ← add PATCH /api/lanes/<id>/position,
    │                         PATCH /api/projects/<id>/position,
    │                         handle this_weekend in PATCH /api/items/<id>
    ├── static/
    │   ├── app.js         ← this-weekend tab + checkbox; drag-and-drop for
    │   │                     lane columns and project sections
    │   └── style.css      ← drag-over highlight, grab cursor, handle styles
    └── templates/
        └── index.html     ← add "This Weekend" nav button

tests/
├── test_this_weekend.py   ← unit tests for set_this_weekend + list_items filter
├── test_reorder_lane.py   ← unit tests for reorder_lane
└── test_reorder_project.py ← unit tests for reorder_project
```

**Structure Decision**: Single-project layout unchanged. All backend additions go into the existing `todo_agent/` package; no new modules required except test files.

## Complexity Tracking

No constitution violations. No complexity justification required.

# Implementation Plan: Filter Empty Lanes

**Branch**: `006-filter-empty-lanes` | **Date**: 2026-09-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/006-filter-empty-lanes/spec.md`

## Summary

In filtered tabs (Today, This Week, This Weekend), skip rendering any lane that has zero items matching the active filter across all its projects. The check is a one-line guard added to the `render()` loop in `app.js` — no backend, data model, or API changes required.

## Technical Context

**Language/Version**: ES2020 vanilla JavaScript (frontend only)

**Primary Dependencies**: None — uses the existing `filteredItems()` helper already present in `app.js`

**Storage**: N/A — display-only change; no reads or writes to the data store

**Testing**: Manual validation via browser; existing pytest suite covers unaffected backend

**Target Platform**: Local browser (127.0.0.1)

**Project Type**: Local web app — frontend adjustment only

**Performance Goals**: No measurable impact — the filter check is O(items) per lane, identical to what already happens per project

**Constraints**: No new dependencies; no backend changes (Principles I, II, IV); change confined to a single function in one file

**Scale/Scope**: Single-user tool; lane/project/item counts are small

## Constitution Check

| Gate | Status | Notes |
|------|--------|-------|
| I. Local-First | ✅ Pass | Pure frontend display change; no network calls |
| II. Single Source of Truth | ✅ Pass | No data writes; rendering only |
| III. Deterministic Core | ✅ Pass | No LLM involvement |
| IV. Simplicity Over Frameworks | ✅ Pass | One conditional added to existing loop; no new library |
| V. Human-Readable State | ✅ Pass | No data format changes |
| VI. Staged Scope | ✅ Pass | Phase 1 GUI enhancement |
| VII. User Stays in Control | ✅ Pass | Non-destructive; hidden lanes reappear in All tab |

## Project Structure

### Documentation (this feature)

```text
specs/006-filter-empty-lanes/
├── plan.md        ← this file
├── quickstart.md  ← Phase 1 output
└── tasks.md       ← Phase 2 output (/speckit-tasks)
```

No `data-model.md`, `research.md`, or `contracts/` — feature introduces no new entities, no unknowns, and no API endpoints.

### Source Code

```text
todo_agent/
└── gui/
    └── static/
        └── app.js   ← sole change: lane-visibility guard in render()
```

**Structure Decision**: Single-project layout unchanged. The entire change is one guard condition in the `render()` function's lane loop in `app.js`.

## Complexity Tracking

No constitution violations. No complexity justification required.

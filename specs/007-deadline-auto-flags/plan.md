# Implementation Plan: Deadline Auto-Flags

**Branch**: `007-deadline-auto-flags` | **Date**: 2026-09-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/007-deadline-auto-flags/spec.md`

## Summary

On every `load_data()` call in `todo_agent/core/store.py`, iterate over all items and additively set `today=True` when the item's deadline equals today's date, and `this_week=True` when the deadline falls within the current Monday–Sunday ISO calendar week. Flags are applied in-memory to the returned snapshot only — nothing is written back to the JSON file, and manually-set flags are never cleared.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: stdlib `datetime` only — no new packages required

**Storage**: Plain JSON at `~/.todo-agent/data.json` (via `todo_agent/core/store.py`)

**Testing**: pytest

**Target Platform**: macOS / local desktop

**Project Type**: CLI + local web GUI (Flask)

**Performance Goals**: Negligible — computation is O(items) at read time; well under 1 ms for any realistic dataset

**Constraints**: In-memory only — flag state MUST NOT be written back to the JSON file (Principle V: human-readable state)

**Scale/Scope**: Single user; tens to low hundreds of items

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I — Local-First | PASS | No network, no hosting |
| II — Single Source of Truth | PASS | Computation added to `store.load_data()`, the only read entry point |
| III — Deterministic Core | PASS | `datetime.date.today()` is deterministic relative to wall clock; no LLM involvement |
| IV — Simplicity | PASS | stdlib `datetime` only; no new dependencies |
| V — Human-Readable State | PASS | Flags applied in-memory only; JSON file stays clean |
| VI — Staged Scope | PASS | No scheduler or Phase 2 components |
| VII — User Stays in Control | PASS | Additive only — user flags are never cleared |

No violations.

## Project Structure

### Documentation (this feature)

```text
specs/007-deadline-auto-flags/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (files touched by this feature)

```text
todo_agent/
└── core/
    └── store.py          # ADD apply_deadline_flags(); call from load_data()

tests/
└── unit/
    └── test_deadline_flags.py   # NEW — unit tests for apply_deadline_flags()
```

No new files outside these two. No schema changes. No GUI changes.

## Complexity Tracking

No constitution violations — section not applicable.

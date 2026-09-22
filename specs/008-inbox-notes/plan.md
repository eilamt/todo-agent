# Implementation Plan: Inbox Notes

**Branch**: `008-inbox-notes` | **Date**: 2026-09-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/008-inbox-notes/spec.md`

## Summary

Add a dedicated inbox for capturing freeform markdown ideas. Notes are stored as `.md` files with YAML frontmatter in `~/.todo-agent/inbox/`. The LLM agent gains four new tools (`add_inbox_note`, `list_inbox_notes`, `get_inbox_note`, `mark_note_promoted`). Promotion is an agent-driven workflow: the LLM reads the `## Promote to` section and calls existing board tools, then calls `mark_note_promoted` on success. The GUI gains an Inbox tab that lists notes with promoted/unpromoted status and shows note body on selection.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: stdlib only — frontmatter parsed manually (no PyYAML needed for the constrained format); `pathlib`, `datetime`, `re`, `uuid` already in use

**Storage**: `~/.todo-agent/inbox/` directory; one `.md` file per note. Board data file (`~/.todo-agent/data.json`) unchanged.

**Testing**: pytest (existing suite)

**Target Platform**: macOS / local desktop

**Project Type**: CLI + local web GUI (Flask)

**Performance Goals**: Negligible — inbox directory expected to contain < 100 files

**Constraints**: No new PyPI dependencies (Principle IV); inbox files MUST remain human-readable plaintext (Principle V); no writes to the board JSON file from inbox module (Principle II — inbox has its own storage layer)

**Scale/Scope**: Single user; tens of notes

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I — Local-First | PASS | Inbox stored in `~/.todo-agent/inbox/`; no network |
| II — Single Source of Truth | PASS | New `core/inbox.py` is the sole reader/writer of inbox files; GUI/CLI call it exclusively |
| III — Deterministic Core | PASS | Frontmatter parsing is deterministic; LLM interprets `## Promote to` at the generative edge only |
| IV — Simplicity | PASS | No new dependencies; stdlib parsing for constrained frontmatter format |
| V — Human-Readable State | PASS | Notes are plain markdown; frontmatter is minimal YAML-subset readable in any editor |
| VI — Staged Scope | PASS | No Phase 2 components (no scheduler, no SMS) |
| VII — User Stays in Control | PASS | Lane creation during promotion requires user confirmation; note files never auto-deleted |

No violations.

## Project Structure

### Documentation (this feature)

```text
specs/008-inbox-notes/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── inbox.md         # Tool and API contracts
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (files created or modified)

```text
todo_agent/
├── config.py                        # ADD get_inbox_dir()
├── core/
│   └── inbox.py                     # NEW — all inbox CRUD + mark_promoted
├── tools.py                         # ADD 4 inbox tools (23 → 27)
├── cli/
│   └── main.py                      # ADD inbox dispatch branches
└── gui/
    ├── server.py                    # ADD /api/inbox routes
    ├── static/
    │   ├── app.js                   # ADD Inbox tab + note list/detail
    │   └── style.css                # ADD inbox tab + promoted badge styles
    └── templates/
        └── index.html               # ADD "Inbox" nav button

tests/
├── contract/
│   └── test_tool_schemas.py         # UPDATE tool count 23 → 27
└── unit/
    └── test_inbox.py                # NEW — unit tests for core/inbox.py
```

## Complexity Tracking

No constitution violations — section not applicable.

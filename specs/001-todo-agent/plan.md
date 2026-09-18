# Implementation Plan: Personal To-Do Agent

**Branch**: `001-todo-agent` | **Date**: 2026-09-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-todo-agent/spec.md`

---

## Summary

Build a personal to-do management agent with two interfaces — a natural-language CLI and a
local browser GUI — sharing a single JSON data store via a shared core module. The CLI uses
the Anthropic tool-calling API to resolve free text into one of 16 declared operations; all
subsequent logic is deterministic Python. The GUI is a local Flask server with a polling-based
live-update mechanism. No external hosting, database, or agent framework is used.

---

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**:
- `anthropic` — LLM SDK for tool-calling intent resolution (CLI only)
- `flask` — local web server for GUI
- `pytest` — test runner

**Storage**: Single JSON file at a user-configured path (default `~/.todo-agent/todos.json`).
Configuration stored in `~/.todo-agent/config.json`. Lane instructions in
`~/.todo-agent/lanes/<slug>.md`. All stdlib; no database engine.

**Testing**: `pytest` + `unittest.mock` (stdlib). LLM calls are stubbed via `patch` on
`client.messages.create`; no network calls in tests.

**Target Platform**: macOS / Linux (local machine, single-user). Python 3.11+ required.

**Project Type**: CLI tool + local web application (hybrid)

**Performance Goals**: CLI round-trip (LLM call + file write) acceptable up to ~5 seconds.
GUI polling every 5 seconds; data changes reflected within 10 seconds.

**Constraints**: Fully offline capable (except for the LLM API call). No external hosting.
All data must remain on the user's machine.

**Scale/Scope**: Single user, one active session at a time. Dozens of lanes, hundreds of
projects, thousands of items — well within the performance range of a JSON file.

---

## Constitution Check

*Evaluated before Phase 0 research. Re-evaluated after Phase 1 design. All gates pass.*

| Principle | Check | Notes |
|---|---|---|
| I. Local-First, No Hosting | ✅ PASS | Flask binds to `127.0.0.1` only. No cloud services. LLM API call is the only outbound network call (user-controlled key). |
| II. Single Source of Truth | ✅ PASS | `core/store.py` is the only module that reads or writes `todos.json`. CLI and GUI call `core/operations.py` functions; neither touches the file directly. |
| III. Deterministic Core, Generative Edges | ✅ PASS | LLM call is isolated to `cli/agent.py`. It selects from 16 declared tools; all subsequent logic in `core/operations.py` is plain deterministic Python. |
| IV. Simplicity Over Frameworks | ✅ PASS | No LangChain, CrewAI, or equivalent. No database. `argparse` (stdlib) for CLI. Flask for GUI. `anthropic` SDK for LLM. Three well-understood dependencies. |
| V. Human-Readable State | ✅ PASS | `todos.json` is indented, nested, plain JSON. Lane instructions are plain Markdown files. |
| VI. Staged Scope | ✅ PASS | Phase 2 fields (`importance`, `start_date`, `push_count`, `instructions_file`) present in schema but no scheduler, SMS, or reminder logic implemented. |
| VII. User Stays in Control | ✅ PASS | CLI delete operations require `y/n` confirmation with cascade count. GUI delete operations show a count-aware confirmation modal before calling the API. |

**Complexity Tracking**: No constitution violations. No justification table required.

---

## Project Structure

### Documentation (this feature)

```
specs/001-todo-agent/
├── plan.md              # This file
├── research.md          # Phase 0: technology decisions
├── data-model.md        # Phase 1: full data schema
├── quickstart.md        # Phase 1: end-to-end validation guide
├── contracts/
│   ├── cli-tools.md     # Phase 1: 15 LLM-callable tool definitions
│   └── gui-api.md       # Phase 1: local HTTP REST API contract
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```
todo_agent/
├── __init__.py
├── config.py                  # reads/writes ~/.todo-agent/config.json; first-run setup
├── core/
│   ├── __init__.py
│   ├── models.py              # Lane, Project, Item, Note dataclasses + validation
│   ├── store.py               # atomic JSON read/write — ONLY module touching todos.json
│   └── operations.py          # all 15 business logic functions + get_delete_preview()
├── cli/
│   ├── __init__.py
│   ├── main.py                # argparse entry point; routes subcommands vs NL free text
│   └── agent.py               # LLM tool-call layer — ONLY file that calls anthropic SDK
├── gui/
│   ├── __init__.py
│   ├── server.py              # Flask app + all API routes; calls core.operations only
│   ├── static/
│   │   ├── app.js             # polling logic + DOM updates + UI interactions
│   │   └── style.css
│   └── templates/
│       └── index.html         # single-page GUI shell
└── tools.py                   # static list of 15 tool definitions (passed to LLM)

tests/
├── conftest.py                # shared fixtures: tmp data file, mock LLM response builder
├── unit/
│   ├── test_models.py         # dataclass validation, status enums, percent_complete
│   ├── test_store.py          # read/write/atomic-update, concurrent safety
│   └── test_operations.py     # all 15 operations + delete cascade + clarification path
├── integration/
│   ├── test_cli_operations.py # CLI end-to-end with stubbed LLM
│   └── test_gui_api.py        # Flask test client for all API endpoints
└── contract/
    └── test_tool_schemas.py   # validates tool JSON schemas are valid JSON Schema
```

**Structure Decision**: Hybrid CLI + web app. `core/` is the shared module enforcing
constitution Principle II. `cli/` and `gui/` are thin front-ends. `tools.py` at the package
root keeps the tool contract visible and separate from dispatch logic.

---

## Design Artifacts

All Phase 1 artifacts are complete and cross-checked against the constitution:

| Artifact | Path | Status |
|---|---|---|
| Technology decisions | `research.md` | ✅ Complete |
| Data model + JSON schema | `data-model.md` | ✅ Complete |
| LLM tool call contract (15 tools) | `contracts/cli-tools.md` | ✅ Complete |
| GUI HTTP API contract | `contracts/gui-api.md` | ✅ Complete |
| End-to-end validation guide | `quickstart.md` | ✅ Complete |

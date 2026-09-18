# Tasks: Personal To-Do Agent

**Input**: Design documents from `specs/001-todo-agent/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-tools.md,
contracts/gui-api.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and
testing of each story. Tests are included in the Polish phase (constitution Quality Standards
mandate testability; spec does not request TDD).

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US5)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, package skeleton, and test harness.

- [X] T001 Create package directory skeleton: `todo_agent/__init__.py`, `todo_agent/core/__init__.py`, `todo_agent/cli/__init__.py`, `todo_agent/gui/__init__.py`, `todo_agent/gui/static/` (empty), `todo_agent/gui/templates/` (empty), `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py`, `tests/contract/__init__.py`
- [X] T002 Create `pyproject.toml` declaring package `todo_agent`, dependencies `anthropic>=0.34`, `flask>=3.0`, `pytest>=8.0`, python_requires `>=3.11`, and console_scripts entry point `todo = todo_agent.cli.main:main`
- [X] T003 [P] Create `tests/conftest.py` with: `tmp_data_path(tmp_path)` fixture returning a `pathlib.Path` to a temp `todos.json`; `make_mock_tool_response(tool_name, tool_input)` helper that returns an `anthropic.types.Message`-shaped object with a `tool_use` content block (for stubbing `client.messages.create` in tests); `patch_config(tmp_data_path)` fixture that patches `todo_agent.config.load_config` to return `{"data_file": str(tmp_data_path), "model": "claude-haiku-3"}`
- [X] T004 [P] Create `README.md` documenting: prerequisites (Python 3.11+, `ANTHROPIC_API_KEY` env var), installation (`pip install -e .`), and first-run behavior (config auto-created at `~/.todo-agent/config.json`)

**Checkpoint**: Package installs, `todo --help` prints usage (even if no-op), `pytest` collects 0 tests without error.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data layer that every user story depends on. MUST complete before any user
story work begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T005 Create `todo_agent/config.py` — `load_config()`: resolves `~/.todo-agent/` via `pathlib.Path.home()`, creates dir and `config.json` with defaults `{"data_file": "~/.todo-agent/todos.json", "model": "claude-haiku-3"}` if absent, reads and returns the dict; `TODO_DATA_FILE` env var overrides `data_file` value; `get_data_file_path()` returns `pathlib.Path` from `load_config()["data_file"]` with `~` expanded
- [X] T006 Create `todo_agent/core/models.py` — pure Python dataclasses (no ORM): `Note(text: str, created_at: str)`; `Item(id: str, title: str, status: str = "not-started", today: bool = False, this_week: bool = False, deadline: str | None = None, push_count: int = 0, notes: list = field(default_factory=list))`; `Project(id: str, name: str, status: str = "not-started", importance: int = 50, start_date: str | None = None, percent_complete: int | None = None, notes: list = field(default_factory=list), items: list = field(default_factory=list))`; `Lane(id: str, name: str, instructions_file: str, projects: list = field(default_factory=list))`; validation constants: `PROJECT_STATUSES = ["not-started","scheduled","in-progress","completed"]`, `ITEM_STATUSES = ["not-started","in-progress","completed"]`; `validate_importance(v)` raises `ValueError` if not `0 <= v <= 100`; `validate_project_status(s)` and `validate_item_status(s)` raise `ValueError` if not in enum
- [X] T007 Create `todo_agent/core/store.py` — `load_data()`: reads JSON from `get_data_file_path()`, creates `{"version": "1", "lanes": []}` if file absent, returns dict; `save_data(data)`: writes to data file atomically using `tempfile.NamedTemporaryFile` + `os.replace()` (prevents corruption on crash), serialises with `json.dumps(data, indent=2)`; `recalculate_percent_complete(project: dict)`: mutates `project["percent_complete"]` in place — `null` if `project["items"]` is empty, else `math.floor(count(item["status"]=="completed") / len(items) * 100)` — called internally before every `save_data` that touches item status

**Checkpoint**: `from todo_agent.config import load_config` works; `load_data()` creates a valid JSON file; `save_data(load_data())` round-trips without data loss.

---

## Phase 3: User Story 1 — Natural Language CLI (Priority: P1) 🎯 MVP

**Goal**: A user can type natural-language commands to add lanes/projects/items, change item
status, set today/this-week flags, set deadlines, and get clarification prompts — all
persisted to the shared JSON data store.

**Independent Test**: Run `todo "add a new lane called Work"`, `todo "add a project to Work called Website Redesign"`, `todo "add a task to Website Redesign called Design homepage"`, `todo "mark Design homepage as done"` and verify `todos.json` reflects all changes and `percent_complete` recalculated. Run ambiguous command and verify clarification printed with no data change.

- [X] T008 Create `todo_agent/tools.py` — `TOOLS` list of 15 tool definition dicts matching `contracts/cli-tools.md` exactly: `add_lane`, `add_project`, `add_item`, `delete_lane`, `delete_project`, `delete_item`, `set_project_status`, `set_item_status`, `set_today`, `set_this_week`, `set_deadline`, `set_importance`, `add_project_note`, `add_item_note`, `request_clarification`; each dict has keys `name`, `description`, `input_schema` with `type`, `properties`, `required` per contracts
- [X] T009 [P] [US1] Implement name-resolution helpers in `todo_agent/core/operations.py` — `_find_lane(data, lane_name)`: case-insensitive match across `data["lanes"]`, raises `ValueError("Lane '{lane_name}' not found")` if absent; `_find_project(data, project_name, lane_name=None)`: if `lane_name` given search that lane only, else search all lanes, raise `ValueError` if not found, raise `AmbiguousMatchError(question)` if multiple lanes contain a project with that name; `_find_item(data, item_title, project_name=None, lane_name=None)`: similar disambiguation, raise `AmbiguousMatchError` with specific question if multiple matches; define `class AmbiguousMatchError(Exception): pass`
- [X] T010 [P] [US1] Implement `add_lane(name: str)` in `todo_agent/core/operations.py` — case-insensitive duplicate check across `data["lanes"]`, raise `ValueError` if duplicate; generate `str(uuid.uuid4())` id; compute slug: `re.sub(r"[^a-z0-9-]", "", name.lower().replace(" ", "-"))`; create blank file at `Path.home()/".todo-agent"/"lanes"/f"{slug}.md"` via `path.touch()`; append `{"id": id, "name": name, "instructions_file": str(path), "projects": []}` to `data["lanes"]`; call `save_data(data)`; return the new lane dict
- [X] T011 [P] [US1] Implement `add_project(lane_name: str, project_name: str, importance: int = 50)` in `todo_agent/core/operations.py` — call `_find_lane`; case-insensitive duplicate check within `lane["projects"]`, raise `ValueError` if duplicate; `validate_importance(importance)`; append `{"id": uuid4, "name": project_name, "status": "not-started", "importance": importance, "start_date": null, "percent_complete": null, "notes": [], "items": []}` to `lane["projects"]`; save; return new project dict
- [X] T012 [P] [US1] Implement `add_item(project_name: str, item_title: str, lane_name: str = None)` in `todo_agent/core/operations.py` — call `_find_project`; case-insensitive duplicate title check within `project["items"]`, raise `ValueError` if duplicate; append `{"id": uuid4, "title": item_title, "status": "not-started", "today": false, "this_week": false, "deadline": null, "push_count": 0, "notes": []}` to `project["items"]`; call `recalculate_percent_complete(project)` (first item → percent_complete becomes 0, not null); save; return new item dict
- [X] T013 [P] [US1] Implement `set_item_status(item_title: str, status: str, project_name: str = None, lane_name: str = None)` in `todo_agent/core/operations.py` — `validate_item_status(status)`; call `_find_item` to get `(lane, project, item)` tuple; set `item["status"] = status`; call `recalculate_percent_complete(project)`; save; return updated item dict
- [X] T014 [P] [US1] Implement `set_today(item_title, value, project_name=None, lane_name=None)` and `set_this_week(item_title, value, project_name=None, lane_name=None)` in `todo_agent/core/operations.py` — call `_find_item`; set `item["today"] = bool(value)` or `item["this_week"] = bool(value)` independently — MUST NOT modify the other flag; save; return updated item dict
- [X] T015 [P] [US1] Implement `set_deadline(item_title, deadline, project_name=None, lane_name=None)` in `todo_agent/core/operations.py` — call `_find_item`; if `deadline` is not None validate it matches `YYYY-MM-DD` via `datetime.date.fromisoformat(deadline)`; set `item["deadline"] = deadline`; save; return updated item dict
- [X] T016 Create `todo_agent/cli/agent.py` — `resolve_intent(user_text: str, data: dict, config: dict) -> tuple[str, dict]`: builds system prompt with today's date (`date.today().isoformat()`), a structured summary of current lane/project/item names for context, and instruction "Prefer `request_clarification` over destructive guessing when ambiguous"; calls `anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"]).messages.create(model=config["model"], max_tokens=1024, tools=TOOLS, tool_choice={"type": "any"}, messages=[{"role": "user", "content": user_text}])`; extracts first `tool_use` content block; returns `(block.name, block.input)`; raises `ValueError` if no `tool_use` block found or if `block.name` not in the 15 declared tool names
- [X] T017 [US1] Create `todo_agent/cli/main.py` — `main()` entry point: set up `argparse.ArgumentParser`; add `visualize` subparser with optional positional `scope` (`all`/`today`/`this-week`, default `all`); default path: join remaining args as `free_text`; if `visualize`: print "GUI not yet implemented" and exit 0 (stub); else: load data via `store.load_data()`, load config via `config.load_config()`, call `agent.resolve_intent(free_text, data, config)` to get `(tool_name, tool_input)`; dispatch to operations for US1 tools (`add_lane`, `add_project`, `add_item`, `set_item_status`, `set_today`, `set_this_week`, `set_deadline`); for `request_clarification`: print `tool_input["question"]` and exit 0; for `AmbiguousMatchError`: print error message and exit 1; for other unimplemented tools: print "Not yet implemented: {tool_name}" and exit 1; on success print confirmation (e.g. "Added lane 'Work'")

**Checkpoint**: All quickstart.md Scenarios 1–5 and Scenario 8 pass end-to-end with a real or stubbed Anthropic API key.

---

## Phase 4: User Story 2 — Safe Delete with Cascade Confirmation (Priority: P2)

**Goal**: Deleting a lane, project, or item from the CLI shows a prompt naming the entity and
the exact count of all cascade-deleted children, then requires explicit y/n confirmation.

**Independent Test**: Create a lane with 2 projects and 5 items total. Run `todo "delete the lane"`. Verify prompt shows correct name, project count (2), item count (5). Answer `n` → data unchanged. Repeat, answer `y` → lane and all children removed.

- [X] T018 [P] [US2] Implement `get_delete_preview(data, entity_type, lane_name=None, project_name=None, item_title=None) -> dict` in `todo_agent/core/operations.py` — for `entity_type="lane"`: find lane, count `len(lane["projects"])` and sum of `len(p["items"])` for each project; for `entity_type="project"`: find project, count `len(project["items"])`; for `entity_type="item"`: find item; return `{"name": str, "projects_count": int|None, "items_count": int}`; does NOT modify data
- [X] T019 [P] [US2] Implement `delete_lane(lane_name: str)` in `todo_agent/core/operations.py` — call `_find_lane`; record counts (projects, total items) for return value; remove lane from `data["lanes"]`; save; return `{"lane_name": name, "projects_deleted": N, "items_deleted": M}`
- [X] T020 [P] [US2] Implement `delete_project(project_name: str, lane_name: str = None)` in `todo_agent/core/operations.py` — call `_find_project` returning `(lane, project)`; record `len(project["items"])`; remove project from `lane["projects"]`; save; return `{"project_name": name, "items_deleted": N}`
- [X] T021 [P] [US2] Implement `delete_item(item_title: str, project_name: str = None, lane_name: str = None)` in `todo_agent/core/operations.py` — call `_find_item` returning `(lane, project, item)`; remove item from `project["items"]`; call `recalculate_percent_complete(project)`; save; return `{"item_title": title, "project_percent_complete": project["percent_complete"]}`
- [X] T022 [US2] Update `todo_agent/cli/main.py` — add delete dispatch: for `delete_lane` tool call `get_delete_preview(data, "lane", lane_name=tool_input["lane_name"])`, print `"This will permanently delete '{name}', {N} projects, and {M} items. Confirm? (y/n): "` then `sys.stdin.readline().strip().lower()`; only call `delete_lane(...)` if `"y"`; else print `"Deletion cancelled."` and exit 0; analogous flows for `delete_project` (`"...and {N} items"`) and `delete_item` (`"...Confirm? (y/n): "`); print success message with counts on confirm

**Checkpoint**: Quickstart.md Scenario 9 passes — correct counts in prompt, cancel preserves data, confirm deletes.

---

## Phase 5: User Story 3 — Local Browser Visualisation (Priority: P3)

**Goal**: `todo visualize [scope]` launches a local web server, opens the browser, shows
lanes/projects/items in the correct layout, supports view filters, allows status changes and
deletions from the GUI, and auto-refreshes within 10 seconds of CLI changes.

**Independent Test**: Run `todo visualize`, confirm browser opens showing all data. Change an item status in the GUI, verify `todos.json` updated. In a second terminal run `todo "add a task ..."`, verify GUI shows new task within 10 seconds without reload. Switch view filters and verify correct items shown.

- [X] T023 [P] [US3] Add ID-based lookup helpers in `todo_agent/core/operations.py` — `_find_lane_by_id(data, lane_id) -> dict`: raises `ValueError("Lane not found")` if absent; `_find_project_by_id(data, project_id) -> tuple[dict, dict]` returning `(lane, project)`; `_find_item_by_id(data, item_id) -> tuple[dict, dict, dict]` returning `(lane, project, item)`; used exclusively by `gui/server.py` endpoints that receive UUIDs from HTML
- [X] T024 [US3] Create `todo_agent/gui/server.py` — Flask `app`; all routes call `core.operations` functions only (never touch data file directly); `GET /` → `render_template("index.html")`; `GET /api/data` → `load_data()`, compute `Last-Modified` from `os.path.getmtime(get_data_file_path())`, check `If-Modified-Since` header and return `304` with empty body if file unmodified else `jsonify(data)` with `Last-Modified` header; `POST /api/lanes` → `add_lane(body["name"])`, return 201/400/409; `DELETE /api/lanes/<lane_id>` → `delete_lane` (find by id first), return 200/404; `POST /api/lanes/<lane_id>/projects` → `add_project`, return 201/400/404/409; `PATCH /api/projects/<project_id>` → apply supplied fields (`status`, `start_date`, `importance`) via corresponding operations, return 200/400/404; `DELETE /api/projects/<project_id>` → `delete_project` by id, return 200/404; `POST /api/projects/<project_id>/items` → `add_item`, return 201/400/404/409; `PATCH /api/items/<item_id>` → apply supplied fields (`status`, `today`, `this_week`, `deadline`, `push_count`) via corresponding operations, return `{"item": ..., "project_percent_complete": ...}`/400/404; `DELETE /api/items/<item_id>` → `delete_item` by id, return 200/404; all `4xx` return `{"error": "message"}`; `launch(scope="all")`: bind to `127.0.0.1`, find available port starting at `5173` using `socket`, open browser via `webbrowser.open(f"http://127.0.0.1:{port}/?view={scope}")`, start `app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)`
- [X] T025 [P] [US3] Create `todo_agent/gui/templates/index.html` — single-page app shell; `<link>` to `style.css`; `<script>` loading `app.js` deferred; structure: `<header>` with three filter buttons (`All` / `Today` / `This Week`) and app title; `<main id="board">` placeholder populated by JS; `<div id="modal" class="hidden">` overlay with `<p id="modal-message">`, `<button id="modal-confirm">Confirm</button>`, `<button id="modal-cancel">Cancel</button>`; no inline styles or scripts
- [X] T026 [US3] Create `todo_agent/gui/static/app.js` — `let lastModified = null`; `setInterval(poll, 5000)` + immediate `poll()` on load; `poll()`: `fetch("/api/data", {headers: lastModified ? {"If-Modified-Since": lastModified} : {}})` → if 200 set `lastModified` from response `Last-Modified` header, store full data, call `render(data, currentView)`; if 304 no-op; `render(data, view)`: clear `#board`, for each lane create column with lane header (name, delete button, add-project form toggle), for each project create collapsible section showing name, status `<select>`, importance badge, percent-complete (display "—" if null), delete button, add-item form toggle; for each item (filtered by view: `all`=all, `today`=item.today===true, `this-week`=item.this_week===true): create card with title, status `<select>`, today/this-week badge if true, deadline if set, delete button; status `<select>` onChange → `PATCH` endpoint; delete button onClick → `showModal(message, () => fetch(DELETE endpoint))` where message includes child counts; add-lane form in header → `POST /api/lanes`; add-project/item inline forms → corresponding POST endpoints; filter buttons → set `currentView`, re-render; read initial `?view=` param from `window.location.search` on load
- [X] T027 [P] [US3] Create `todo_agent/gui/static/style.css` — `#board`: `display: flex; flex-direction: row; gap: 1rem; overflow-x: auto; padding: 1rem`; lane column: `min-width: 280px; background: #f5f5f5; border-radius: 8px; padding: 1rem`; project section: `margin-bottom: 0.75rem`; item card: `background: white; border-radius: 4px; padding: 0.5rem; margin: 0.25rem 0; box-shadow: 0 1px 2px rgba(0,0,0,0.1)`; status color via `data-status` attribute: `[data-status="not-started"]` gray, `[data-status="in-progress"]` blue, `[data-status="completed"]` green; badges for today/this-week: small pill labels; modal overlay: `position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center`; modal box: `background: white; padding: 2rem; border-radius: 8px; max-width: 400px`; `.hidden { display: none }`
- [X] T028 [US3] Update `todo_agent/cli/main.py` — replace `visualize` stub: import `gui.server`; call `gui.server.launch(scope=args.scope or "all")`; catch `OSError` (port conflict) and print "Could not start GUI server: port unavailable. Try closing other instances." and exit 1

**Checkpoint**: Quickstart.md Scenarios 10–12 pass — GUI launches, live sync works within 10 seconds, view filters work, GUI delete shows correct modal.

---

## Phase 6: User Story 4 — Append Timestamped Notes (Priority: P4)

**Goal**: A user can append free-text notes with automatic UTC timestamps to any project or
item via the CLI; notes appear in chronological order and cannot be edited or deleted.

**Independent Test**: Run `todo "note on the Budget project: waiting on finance"`, verify `todos.json` contains note with non-empty text and valid ISO 8601 UTC timestamp. Run second note command, verify both notes present in order.

- [X] T029 [P] [US4] Implement `add_project_note(project_name: str, text: str, lane_name: str = None)` in `todo_agent/core/operations.py` — call `_find_project`; validate `text` is non-empty (raise `ValueError` if blank); append `{"text": text, "created_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}` to `project["notes"]`; save; return the new note dict
- [X] T030 [P] [US4] Implement `add_item_note(item_title: str, text: str, project_name: str = None, lane_name: str = None)` in `todo_agent/core/operations.py` — call `_find_item`; validate `text` non-empty; append `{"text": text, "created_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}` to `item["notes"]`; save; return the new note dict
- [X] T031 [P] [US4] Implement `list_notes(entity_type: str, name: str, project_name: str = None, lane_name: str = None) -> list` in `todo_agent/core/operations.py` — validate `entity_type` is `"project"` or `"item"` (raise `ValueError` otherwise); if `"project"`: call `_find_project`, return `project["notes"]` (empty list if none); if `"item"`: call `_find_item`, return `item["notes"]` (empty list if none); this is a read-only operation — MUST NOT call `save_data`
- [X] T032 [US4] Update `todo_agent/cli/main.py` — add `add_project_note`, `add_item_note`, and `list_notes` to dispatcher; for add operations: on success print `"Note added to {entity} '{name}' at {created_at}"`; on `ValueError` (blank text or entity not found) print error and exit 1; for `list_notes`: if notes list is empty print `"No notes for {entity_type} '{name}'"`, else print each note as `"[{created_at}] {text}"` with a blank line between entries; on entity not found print error and exit 1

**Checkpoint**: Quickstart.md Scenario 6 passes — notes appended with timestamps, listed in chronological order, no mechanism to edit or delete.

---

## Phase 7: User Story 5 — Scheduling Fields and Importance (Priority: P5)

**Goal**: A user can set a project's status to `scheduled` with a start date, set its
importance score (0–100), and read those values back from the data store. No automated
logic acts on these fields in Phase 1.

**Independent Test**: Run `todo "schedule Q4 Planning to start on 2026-10-01"`, verify `todos.json` has `status: "scheduled"` and `start_date: "2026-10-01"`. Run `todo "set importance of Q4 Planning to 80"`, verify `importance: 80`. Verify project with zero items shows `percent_complete: null`.

- [X] T033 [P] [US5] Implement `set_project_status(project_name: str, status: str, start_date: str = None, lane_name: str = None)` in `todo_agent/core/operations.py` — `validate_project_status(status)`; call `_find_project`; if `status == "scheduled"`: validate `start_date` is non-None and parses via `datetime.date.fromisoformat(start_date)`, raise `ValueError` if missing or invalid; set `project["status"] = status`; if `start_date` provided set `project["start_date"] = start_date` (if status changes away from scheduled, preserve `start_date` value in storage — it carries no semantic meaning in that state); save; return updated project dict
- [X] T034 [P] [US5] Implement `set_importance(project_name: str, importance: int, lane_name: str = None)` in `todo_agent/core/operations.py` — call `_find_project`; `validate_importance(importance)` (raises `ValueError` if not `0 <= importance <= 100`); set `project["importance"] = importance`; save; return updated project dict
- [X] T035 [US5] Update `todo_agent/cli/main.py` — add `set_project_status` and `set_importance` to dispatcher; print confirmation with new values on success

**Checkpoint**: Quickstart.md Scenarios 5 and 7 pass — deadline, importance, and scheduled status+start_date all stored and readable.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Test suite, constitution Quality Standards compliance, and final validation.

- [X] T036 [P] Create `tests/unit/test_models.py` — test `validate_importance`: 0 and 100 pass, -1 and 101 raise `ValueError`; test `validate_project_status`: all four values pass, unknown raises `ValueError`; test `validate_item_status`: three values pass, unknown raises; test `recalculate_percent_complete`: empty items list → `null`, 0 of 1 completed → `0`, 1 of 1 → `100`, 1 of 3 → `33` (floor), 2 of 3 → `66`
- [X] T037 [P] Create `tests/unit/test_store.py` — test `load_data()` creates file with `{"version":"1","lanes":[]}` if absent; test `load_data()` returns existing data without modification; test `save_data()` writes valid indented JSON readable by `json.loads`; test atomic write: simulate mid-write crash by patching `os.replace` to raise after tempfile write, verify original file unchanged
- [X] T038 [P] Create `tests/unit/test_operations.py` — using `patch_config` fixture: test `add_lane` duplicate raises `ValueError`; test `add_lane` creates `~/.todo-agent/lanes/work.md` (via tmp dir); test `add_project` unique within lane (same name in different lanes OK); test `add_item` percent_complete after adding first item is `0` not `null`; test `set_item_status` to `completed` sets percent_complete to 100 with one item; test `set_today` does not alter `this_week`; test `set_this_week` does not alter `today`; test `_find_item` raises `AmbiguousMatchError` when two projects contain same item title; test `get_delete_preview` returns correct lane/project/item counts; test delete cascade removes all children; test `add_project_note` and `add_item_note` with blank text raise `ValueError`; test `list_notes` returns notes in insertion order; test `list_notes` with invalid `entity_type` raises `ValueError`; test `list_notes` on entity with no notes returns empty list
- [X] T039 [P] Create `tests/integration/test_cli_operations.py` — using `patch_config` and `make_mock_tool_response`; patch `anthropic.Anthropic` so `messages.create` returns mocked `tool_use` responses; test full CLI round-trip: `main(["add a new lane called Work"])` → data file contains lane; test delete confirmation: patch `sys.stdin` to return `"n\n"` → data unchanged; patch to return `"y\n"` → lane deleted; test `request_clarification` response prints question and exits 0 without writing data; test `list_notes` response prints notes and does not modify data file
- [X] T040 [P] Create `tests/integration/test_gui_api.py` — using Flask `app.test_client()` and `patch_config`: test `GET /api/data` returns 200 with `{"version":"1","lanes":[]}`; test `GET /api/data` returns 304 when `If-Modified-Since` matches current mtime; test `POST /api/lanes` with `{"name":"Work"}` returns 201 and lane appears in subsequent `GET /api/data`; test `POST /api/lanes` duplicate returns 409; test `DELETE /api/lanes/<id>` for existing lane returns 200 with correct `projects_deleted`/`items_deleted`; test `PATCH /api/items/<id>` with `{"status":"completed"}` returns `project_percent_complete` in response body; test `DELETE /api/items/<id>` returns updated `project_percent_complete`
- [X] T041 [P] Create `tests/contract/test_tool_schemas.py` — assert `len(TOOLS) == 16`; for each tool dict in `TOOLS`: assert `"name"` key present and non-empty string; assert `"description"` key present; assert `"input_schema"` is dict with `"type": "object"`, `"properties"` dict, and `"required"` list; assert all values in `"required"` exist as keys in `"properties"`; assert tools with `"enum"` in properties validate against expected values from `data-model.md` (project status and item status enums; `entity_type` enum on `list_notes`)
- [X] T042 Run quickstart.md validation scenarios S1–S12 end-to-end with a real `ANTHROPIC_API_KEY` and confirm all 12 scenarios pass per the validation checklist in `quickstart.md`

**Checkpoint**: `pytest` passes, all quickstart scenarios green — feature complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — **blocks all user stories**
- **US1 (Phase 3)**: Depends on Phase 2 — can start as soon as Foundational is done
- **US2 (Phase 4)**: Depends on Phase 3 (needs `_find_*` helpers and CLI dispatcher)
- **US3 (Phase 5)**: Depends on Phase 2; can run in parallel with US2 after Foundational
- **US4 (Phase 6)**: Depends on Phase 3 (needs `_find_project`, `_find_item` helpers)
- **US5 (Phase 7)**: Depends on Phase 3 (needs `_find_project` helper)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: No story dependencies — start after Foundational
- **US2 (P2)**: Needs `_find_*` helpers from US1 (T009) — start after US1 helpers done
- **US3 (P3)**: Needs Foundational only; `_find_*_by_id` added in T023 — can run in parallel with US2
- **US4 (P4)**: Needs `_find_project` / `_find_item` from US1 (T009) — start after T009; T029–T031 [P] then T032 dispatch
- **US5 (P5)**: Needs `_find_project` from US1 (T009) — start after T009; T033–T034 [P] then T035 dispatch

### Parallel Opportunities Within Each Story

**US1**: T009–T015 (helpers + 6 operations) are all [P] — create operations.py once, then implement all 7 functions in parallel since they are independent functions in the same file. T016 (agent.py) and T017 (main.py) depend on T008 and T009.

**US2**: T018–T021 (4 operations) are all [P] — implement in parallel once helpers exist. T022 (main.py update) depends on T018–T021.

**US3**: T023 [P] (helpers), T025 [P] (HTML), T027 [P] (CSS) can run in parallel. T024 (server.py) depends on T023. T026 (app.js) depends on T024 structure. T028 (main.py) depends on T024.

**US4**: T029 [P], T030 [P], and T031 [P] can run in parallel. T032 depends on all three.

**US5**: T033 [P] and T034 [P] can run in parallel. T035 depends on both.

**Polish**: T036–T041 are all [P] — write all test files in parallel.

---

## Parallel Example: US1 Core Operations

```bash
# After T009 (helpers), launch all in parallel:
Task: "Implement add_lane in todo_agent/core/operations.py"         # T010
Task: "Implement add_project in todo_agent/core/operations.py"     # T011
Task: "Implement add_item in todo_agent/core/operations.py"        # T012
Task: "Implement set_item_status in todo_agent/core/operations.py" # T013
Task: "Implement set_today/set_this_week in todo_agent/core/operations.py" # T014
Task: "Implement set_deadline in todo_agent/core/operations.py"    # T015
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (**critical — blocks everything**)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run quickstart.md Scenarios 1–5 and Scenario 8
5. Ship/demo the natural-language CLI — it is independently usable

### Incremental Delivery

1. Phase 1 + 2 → data layer working
2. Phase 3 (US1) → **MVP**: add/update/query via natural language
3. Phase 4 (US2) → safe deletes; deploy/demo
4. Phase 5 (US3) → browser visualisation; deploy/demo
5. Phase 6 (US4) → note appending + listing; deploy/demo
6. Phase 7 (US5) → scheduling fields; all quickstart scenarios pass
7. Phase 8 → full test suite green; feature complete (42 tasks total)

### Parallel Team Strategy

With multiple developers after Phase 2 completes:
- Developer A: US1 (Phase 3)
- Developer B: US3 GUI scaffold (Phases 5 can start on HTML/CSS/server while A builds operations)
- Once T009 is done: Developer C can begin US4 and US5 in parallel with Developer A finishing US1

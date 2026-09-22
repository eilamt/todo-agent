# Tasks: Inbox Notes

**Input**: Design documents from `specs/008-inbox-notes/`

**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/inbox.md ✓, quickstart.md ✓

---

## Phase 1: Setup

- [x] T001 Add `get_inbox_dir() -> Path` to `todo_agent/config.py`: returns `Path.home() / ".todo-agent" / "inbox"`

---

## Phase 2: Foundational — Core Inbox Module

**Purpose**: `todo_agent/core/inbox.py` is the single reader/writer of inbox files — all stories depend on it.

- [x] T002 Create `todo_agent/core/inbox.py` with frontmatter parser: `_parse_note(path: Path) -> dict | None` — reads file, splits on first `---`/`---` block, parses `title` (str), `promoted` (bool, coerce `"true"` → `True`, else `False`), `created_at` (str|None); body is everything after closing `---`; returns `{"slug", "title", "promoted", "created_at", "body"}` or `None` if malformed/unreadable

- [x] T003 Add `_write_frontmatter(path: Path, title: str, promoted: bool, created_at: str) -> None` to `todo_agent/core/inbox.py`: writes/rewrites the frontmatter block while preserving the body; format is exactly `---\ntitle: {title}\npromoted: {str(promoted).lower()}\ncreated_at: {created_at}\n---\n{body}`

- [x] T004 Add `add_inbox_note(title: str, body: str = "") -> dict` to `todo_agent/core/inbox.py`: validates title non-empty; slugifies title using `re.sub(r"[^a-z0-9-]", "", title.lower().replace(" ", "-"))`; if slug collision appends `-{uuid4()[:8]}`; creates `get_inbox_dir()` (mkdir parents ok_exist=True); writes file with frontmatter (`promoted: false`, `created_at` = now UTC ISO); returns parsed note dict (without body for listing; include body here)

- [x] T005 Add `list_inbox_notes() -> list[dict]` to `todo_agent/core/inbox.py`: scans `get_inbox_dir()` for `*.md` files; calls `_parse_note()` on each; skips `None` results silently; returns list of `{"slug", "title", "promoted", "created_at"}` (no body) sorted by `created_at` descending (nulls last)

- [x] T006 Add `get_inbox_note(title: str) -> dict` to `todo_agent/core/inbox.py`: calls `list_inbox_notes()` to find first case-insensitive title match; loads full file to include body; raises `ValueError` if not found; returns full dict including `"body"`

- [x] T007 Add `mark_note_promoted(title: str) -> dict` to `todo_agent/core/inbox.py`: finds note by title (case-insensitive); calls `_write_frontmatter()` with `promoted=True`; returns updated note dict (no body); idempotent — no error if already promoted

**Checkpoint**: `core/inbox.py` complete — all stories can now build on it.

---

## Phase 3: User Story 1 — Capture an Idea as an Inbox Note (Priority: P1) 🎯

**Goal**: User can create and list inbox notes via CLI; notes appear in the correct file format.

**Independent Test**: `todo inbox add "My Idea" "Some text"` creates `~/.todo-agent/inbox/my-idea.md` with correct frontmatter. `todo list inbox notes` shows it with `[not promoted]`.

### Implementation

- [x] T008 [US1] Add 4 inbox tools to `todo_agent/tools.py` (tool count 23 → 27): `add_inbox_note` (required: `title`; optional: `body`), `list_inbox_notes` (no required fields), `get_inbox_note` (required: `title`), `mark_note_promoted` (required: `title`) — use schemas from `contracts/inbox.md`

- [x] T009 [US1] Add inbox tool dispatch to `todo_agent/cli/main.py`: in the tool-result handler add branches for `add_inbox_note` (print slug + title), `list_inbox_notes` (print each note's title + `[promoted]`/`[not promoted]`), `get_inbox_note` (print title, status, body), `mark_note_promoted` (print confirmation)

- [x] T010 [US1] Add `GET /api/inbox` route to `todo_agent/gui/server.py`: calls `inbox.list_inbox_notes()`; returns JSON array; no `If-Modified-Since` logic needed (filesystem polling is acceptable)

- [x] T011 [US1] Add `POST /api/inbox` route to `todo_agent/gui/server.py`: reads `{"title", "body"}`; validates title non-empty (400 if missing); calls `inbox.add_inbox_note()`; returns 201 with note dict

- [x] T012 [US1] Update `tests/contract/test_tool_schemas.py`: change `assert len(TOOLS) == 23` to `assert len(TOOLS) == 27`

**Checkpoint**: CLI can add and list inbox notes; GUI server exposes `/api/inbox`.

---

## Phase 4: User Story 2 — Promote a Note to the Board (Priority: P2)

**Goal**: LLM agent reads `## Promote to`, calls existing board tools, then calls `mark_note_promoted`.

**Independent Test**: Create a note with a `## Promote to` section. Run `todo promote inbox note "My Idea"`. Verify board actions executed and `promoted: true` in file.

### Implementation

- [x] T013 [US2] Add `GET /api/inbox/<slug>` route to `todo_agent/gui/server.py`: finds file by slug, returns full note dict including body; 404 if not found

- [x] T014 [US2] Add `PATCH /api/inbox/<slug>` route to `todo_agent/gui/server.py`: accepts `{"promoted": true}`; calls `inbox.mark_note_promoted()` (looked up by slug→title); returns updated note dict; 404 if not found; 400 if body invalid

- [x] T015 [US2] Update LLM agent system prompt in `todo_agent/cli/agent.py` to include inbox promotion guidance: when user asks to promote a note, the agent should (1) call `get_inbox_note` to read it, (2) check if already promoted and warn if so, (3) call existing board tools per `## Promote to` instructions, (4) call `mark_note_promoted` on success — add this as a short paragraph in the system prompt

**Checkpoint**: Full promotion flow works via CLI agent.

---

## Phase 5: User Story 3 — View and Browse Inbox Notes in GUI (Priority: P3)

**Goal**: GUI Inbox tab lists all notes with title + promoted badge; clicking a note shows full body.

**Independent Test**: Open GUI, navigate to Inbox tab, verify notes listed. Click a note, verify body shown.

### Implementation

- [x] T016 [US3] Add "Inbox" nav button to `todo_agent/gui/templates/index.html` alongside existing tab buttons (All, Today, This Week, This Weekend)

- [x] T017 [US3] Add inbox tab styles to `todo_agent/gui/static/style.css`: `.inbox-list` (note list container), `.inbox-item` (individual note row), `.badge-promoted` (green badge), `.badge-unpromoted` (grey badge), `.inbox-detail` (note body panel), `.inbox-detail pre` or `.inbox-body` (body text display)

- [x] T018 [US3] Add inbox state and rendering to `todo_agent/gui/static/app.js`:
  - Add `inboxNotes = []` state variable
  - Add `fetchInbox()` function: `GET /api/inbox`, store results in `inboxNotes`, call `renderInbox()` if current view is `"inbox"`
  - Add `renderInbox()` function: renders `.inbox-list` of note rows showing title + promoted/unpromoted badge; clicking a row calls `showNoteDetail(note)`
  - Add `showNoteDetail(note)` function: fetches `GET /api/inbox/<slug>` for full body, renders body in a detail panel (plain text or pre-formatted)
  - When view switches to `"inbox"`, call `fetchInbox()`; set up polling `setInterval(fetchInbox, 5000)` only while inbox tab active; clear interval when switching away
  - Wire the "Inbox" nav button to set `view = "inbox"` and call `renderInbox()`

**Checkpoint**: GUI Inbox tab fully functional.

---

## Phase 6: Polish & Validation

- [x] T019 Write unit tests in `tests/unit/test_inbox.py` covering: (a) `add_inbox_note` creates file with correct frontmatter; (b) `list_inbox_notes` returns sorted list, skips malformed files; (c) `get_inbox_note` returns body, raises ValueError if not found; (d) `mark_note_promoted` sets `promoted: true` and is idempotent; (e) slug collision appends suffix; (f) empty title raises ValueError; (g) note without `created_at` in frontmatter is handled gracefully; (h) non-.md files in inbox dir are ignored

- [x] T020 Run full test suite `pytest -v` — all 168 existing tests plus new inbox tests must pass

- [x] T021 Manual validation of quickstart.md scenarios S1–S8 via CLI and GUI

---

## Dependencies

- T001 must complete before T002–T007 (config needed by core module)
- T002 must complete before T003–T007 (parser needed by all other core functions)
- T003 must complete before T007 (write helper needed by mark_promoted)
- T004–T007 depend on T002–T003; can otherwise run in sequence
- T008 depends on T001–T007 (tools call core functions)
- T009 depends on T008 (dispatch calls tools)
- T010–T011 depend on T001–T007 (server routes call core)
- T012 depends on T008 (count changes when tools added)
- T013–T014 depend on T010–T011 (extends server)
- T015 depends on T008 (system prompt references tool names)
- T016–T018 depend on T010–T011 (GUI fetches server routes)
- T019 depends on T001–T007 (tests core functions)
- T020 depends on T019 + all implementation tasks
- T021 depends on T020

## Parallel Opportunities

- T010 and T011 can be written together (same file, same session — sequential)
- T016 and T017 can run in parallel (different files)
- T008 and T010–T011 can run in parallel (different files: tools.py vs server.py)
- T019 can be written alongside T002–T007 (tests the same functions, different file)

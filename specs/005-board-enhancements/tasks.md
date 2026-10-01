# Tasks: Board Enhancements

**Input**: Design documents from `specs/005-board-enhancements/`

**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths are included in every description

---

## Phase 1: Setup

**Purpose**: Verify project infrastructure is ready — no new dependencies or scaffolding required.

- [x] T001 Verify `.gitignore` covers Python patterns (`__pycache__/`, `*.pyc`, `.venv/`, `*.egg-info/`) in `.gitignore`

**Checkpoint**: Project is ready for feature implementation.

---

## Phase 2: Foundational (Blocking Prerequisite for US1)

**Purpose**: Data-model change that US1 depends on. US2 and US3 are independent of this phase.

- [x] T002 Add `this_weekend: bool = False` field to the `Item` dataclass in `todo_agent/core/models.py` (immediately after the `this_week` field)

**Checkpoint**: `Item` dataclass has `this_weekend`. US1 backend work can now begin. US2 and US3 may begin in parallel with US1 from here.

---

## Phase 3: User Story 1 — Mark Items for This Weekend (Priority: P1) 🎯 MVP

**Goal**: Users can flag any item as "this weekend", toggle it in the GUI, see all flagged items in a dedicated This Weekend tab, and set it via the CLI agent.

**Independent Test**: Mark an item via CLI, toggle the checkbox in the GUI item card, switch to the This Weekend tab — item appears. Uncheck — item disappears. Reload the page — state persists.

### Implementation for User Story 1

- [x] T00X [US1] In `todo_agent/core/operations.py`: add `set_this_weekend(item_title, value, project_name=None, lane_name=None) -> dict` (mirrors `set_today`/`set_this_week`); add `"this_weekend": False` to the `new_item` dict in `add_item()`; add `"this_weekend": item.get("this_weekend", False)` to the returned dict in both `list_items()` and `get_item()`
- [x] T00X [P] [US1] Add `set_this_weekend` tool definition to `todo_agent/tools.py` (same schema shape as `set_today` and `set_this_week`; description: "Mark or unmark an item as something to work on this weekend. Does not affect the today or this_week flags.")
- [x] T00X [P] [US1] In `todo_agent/cli/agent.py`: add `elif tool_name == "set_this_weekend":` dispatch branch calling `operations.set_this_weekend(**tool_input)`
- [x] T00X [US1] In `todo_agent/gui/server.py` `update_item()` route: add `if "this_weekend" in body: operations.set_this_weekend(...)` handling, parallel to the existing `today` and `this_week` blocks
- [x] T00X [P] [US1] In `todo_agent/gui/templates/index.html`: add `<button class="filter-btn" data-view="this-weekend">This Weekend</button>` to the `<nav class="filters">` block, after the "This Week" button
- [x] T00X [US1] In `todo_agent/gui/static/app.js`: (a) add `"this-weekend"` to the valid views list in the URL-param check; (b) add `filteredItems()` support for `"this-weekend"` view (filter `item.this_weekend === true`); (c) add the this-weekend checkbox/label to `buildItemCard()` (same pattern as the `todayLabel` / `weekLabel` blocks); (d) wire `apiPatch` on checkbox change to send `{ this_weekend: checked }`
- [x] T00X [P] [US1] In `todo_agent/gui/static/style.css`: add `.badge-weekend` style (same pattern as `.badge-today` / `.badge-week`)

**Checkpoint**: User Story 1 is fully functional. `todo "mark X for this weekend"` works; This Weekend tab shows correct items; toggling the checkbox persists across reloads.

---

## Phase 4: User Story 2 — Reorder Lanes Left/Right (Priority: P2)

**Goal**: Users can drag a lane column header left or right to reorder lanes; the new order persists across page reloads.

**Independent Test**: Drag a lane header to a new position — lane moves immediately. Reload the page — order is preserved. Release outside a valid drop zone — lane returns to original position, no data change.

### Implementation for User Story 2

- [x] T01X [US2] In `todo_agent/core/operations.py`: add `reorder_lane(lane_id: str, new_index: int) -> None` — `load_data()`, find lane by `id` (raise `ValueError` if not found), remove from list, clamp `new_index` to `[0, len(lanes)-1]`, insert at `new_index`, `save_data(data)`
- [x] T01X [US2] In `todo_agent/gui/server.py`: add `PATCH /api/lanes/<lane_id>/position` route — parse `{ "index": int }` from body (400 if missing/non-integer), call `operations.reorder_lane(lane_id, index)` (404 on `ValueError`), return `{}` with 200
- [x] T01X [US2] In `todo_agent/gui/static/app.js`: make lane columns draggable — set `col.draggable = true` in `buildLaneCol()`; add `dragstart` handler storing the dragged lane's id; add `dragover` (preventDefault) and `drop` handlers on each lane column that compute the drop index and call `apiPatch("/api/lanes/<id>/position", { index })` then `poll()`; a drop outside a lane column is a no-op (no API call)
- [x] T01X [P] [US2] In `todo_agent/gui/static/style.css`: add `.lane-col[draggable]` cursor style (`grab`), `.lane-col.drag-over` highlight style (e.g., outline or opacity change), and `.lane-col.dragging` opacity style

**Checkpoint**: User Story 2 is fully functional. Dragging lanes reorders them and the order survives page reload. Dropping outside a valid target is a safe no-op.

---

## Phase 5: User Story 3 — Reorder Projects Within a Lane (Priority: P3)

**Goal**: Users can drag a project card up or down within its lane to reorder it; the new order persists across page reloads. Dropping a project outside its origin lane is a safe no-op.

**Independent Test**: Drag a project card above or below another project in the same lane — card moves immediately. Reload the page — order is preserved. Drag a card to a different lane and release — card returns to original position, no data change.

### Implementation for User Story 3

- [x] T01X [US3] In `todo_agent/core/operations.py`: add `reorder_project(project_id: str, new_index: int) -> None` — `load_data()`, `_find_project_by_id(data, project_id)` → `(lane, project)` (raise `ValueError` if not found), remove project from `lane["projects"]`, clamp `new_index` to `[0, len(lane["projects"])]`, insert at `new_index`, `save_data(data)`
- [x] T01X [US3] In `todo_agent/gui/server.py`: add `PATCH /api/projects/<project_id>/position` route — parse `{ "index": int }` from body (400 if missing/non-integer), call `operations.reorder_project(project_id, index)` (404 on `ValueError`), return `{}` with 200
- [x] T01X [US3] In `todo_agent/gui/static/app.js`: make project sections draggable within their lane — set `section.draggable = true` in `buildProjectSection()`; add `dragstart` handler on `section` storing the dragged project's id and its parent lane's id; add `dragover` (preventDefault) and `drop` handlers on each project section that: (a) verify the dragged project's lane id matches the drop target's lane id — if different, reject with no API call; (b) compute new index within the lane and call `apiPatch("/api/projects/<id>/position", { index })` then `poll()`
- [x] T01X [P] [US3] In `todo_agent/gui/static/style.css`: add `.project-section[draggable]` cursor style, `.project-section.drag-over` highlight style, `.project-section.dragging` opacity style

**Checkpoint**: User Story 3 is fully functional. Dragging projects reorders them within a lane and the order survives page reload. Cross-lane drops are a safe no-op.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Tests, validation, and regression check across all three stories.

- [x] T01X [P] Write unit tests for `set_this_weekend` (set, clear, default-false on missing field, ambiguous match) in `tests/test_this_weekend.py`
- [x] T01X [P] Write unit tests for `reorder_lane` (move to first, move to last, clamp out-of-range, unknown id) in `tests/test_reorder_lane.py`
- [x] T02X [P] Write unit tests for `reorder_project` (move to first, move to last, clamp out-of-range, unknown id) in `tests/test_reorder_project.py`
- [x] T02X Run quickstart.md validation scenarios S1–S9 end-to-end against the running GUI
- [x] T02X Run full test suite `pytest -v` and confirm all tests pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — blocks US1 backend only
- **US1 (Phase 3)**: Depends on Phase 2 (`Item.this_weekend` field must exist first)
- **US2 (Phase 4)**: Depends on Phase 1 only — can start in parallel with Phase 3
- **US3 (Phase 5)**: Depends on Phase 1 only — can start in parallel with Phase 3 and 4
- **Polish (Phase 6)**: Depends on Phases 3, 4, 5 all complete

### Within Each User Story

- T003 (operations update) must complete before T006 (server route update) for US1, because the route calls the operation
- T004 and T005 are independent of T006 and T007 — can run in parallel with them
- T010 (reorder_lane operation) must complete before T011 (server route) for US2
- T014 (reorder_project operation) must complete before T015 (server route) for US3
- JS changes (T008, T012, T016) depend on their respective server endpoints being in place to function end-to-end, but can be written independently

### Parallel Opportunities

Within US1: T004, T005, T007, T009 can all run in parallel once T002 and T003 are done.
Within US2: T013 can run in parallel with T010+T011.
Within US3: T017 can run in parallel with T014+T015.
US2 and US3 as wholes can run in parallel with US1 (different files except `operations.py` and `server.py` — those must be written sequentially within each story).
Polish tests T018, T019, T020 can all run in parallel.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002)
3. Complete Phase 3: User Story 1 (T003–T009)
4. **STOP and VALIDATE**: `todo "mark X for this weekend"` + GUI This Weekend tab
5. Ship US1 independently

### Incremental Delivery

1. Setup + Foundational → US1 (This Weekend flag) → validate independently → ship
2. US2 (Lane drag-and-drop) → validate independently → ship
3. US3 (Project drag-and-drop) → validate independently → ship

### Parallel Team Strategy

After Phase 2:
- Developer A: US1 (T003–T009)
- Developer B: US2 (T010–T013)
- Developer C: US3 (T014–T017)

Note: `operations.py` and `server.py` are shared across all three stories. Coordinate to avoid merge conflicts — each story's additions are non-overlapping function additions, so merging is straightforward.

---

## Notes

- No new Python packages or JS libraries — Principle IV compliance
- `this_weekend` reads use `.get("this_weekend", False)` for backward compatibility with existing JSON data
- Cross-lane project drops must be explicitly rejected in the JS `drop` handler (compare stored `laneId` with drop target's `laneId`)
- All drag-and-drop uses native HTML5 events — no CDN, no bundler needed

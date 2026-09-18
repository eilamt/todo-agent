# Tasks: GUI Inline Editing

**Input**: Design documents from `specs/003-gui-interactivity/`

**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/api-patch-extensions.md ✓, quickstart.md ✓

**Organization**: Tasks grouped by user story. US1 (item field editing) is the MVP; US2 (flag checkboxes), US3 (project editing), US4 (collapse) build on it.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to

---

## Phase 2: Foundational (Blocking Prerequisite for All Stories)

**Purpose**: Backend rename operations required by US1 (item title) and US3 (project name).

**⚠️ CRITICAL**: T001 blocks T003; T002 blocks T011.

- [X] T001 Add `rename_item(item_title, new_title, project_name, lane_name) → dict` to `todo_agent/core/operations.py` — find item via `_find_item(data, item_title, project_name, lane_name)`; if `new_title.strip()` is empty raise `ValueError("Item title must not be empty.")`; check no other item in same project has the same name case-insensitively (raise `ValueError("Item 'X' already exists in project 'Y'.")` on collision); set `item["title"] = new_title.strip()`; call `save_data(data)`; return updated item dict
- [X] T002 Add `rename_project(project_name, new_name, lane_name) → dict` to `todo_agent/core/operations.py` — find project via `_find_project(data, project_name, lane_name)`; if `new_name.strip()` is empty raise `ValueError("Project name must not be empty.")`; check no other project in same lane has same name case-insensitively (raise `ValueError("Project 'X' already exists in lane 'Y'.")` on collision); set `project["name"] = new_name.strip()`; call `save_data(data)`; return updated project dict

**Checkpoint**: `rename_item` and `rename_project` pass direct unit tests before any server or GUI work begins.

---

## Phase 3: User Story 1 — Edit Item Fields Inline (Priority: P1) 🎯 MVP

**Goal**: Users can click any item field (title, description, importance, deadline) to edit it inline; changes save automatically on Enter or blur.

**Independent Test**: Run quickstart.md Scenarios 1–5. Each field saves on Enter/blur and persists after page reload.

### Implementation for User Story 1

- [X] T003 [P] [US1] Extend `PATCH /api/items/:id` in `todo_agent/gui/server.py` — after the existing `if "deadline" in body` block add: `if "title" in body: operations.rename_item(item["title"], body["title"], project["name"], lane["name"])` (process title first — subsequent handlers re-fetch or use item id); `if "description" in body: operations.set_item_description(item["title"] if "title" not in body else body["title"].strip(), body.get("description"), project["name"], lane["name"])`; `if "importance" in body: operations.set_item_importance(...)` similarly; map `ValueError` containing "already exists" to HTTP 409, other `ValueError` to HTTP 400
- [X] T004 [P] [US1] Add `makeInlineEdit(displayEl, inputTag, currentVal, validate, onSave)` factory to `todo_agent/gui/static/app.js` — `displayEl.addEventListener("click", ...)` replaces the element with `document.createElement(inputTag)` with class `"inline-edit-input"`, pre-filled with `currentVal`; on `keydown` Enter or `blur` event: if `!validate(input.value)` restore displayEl; else `try { await onSave(input.value); await poll(); } catch { restore displayEl; }`; factor out a `restore()` closure that puts the original element back; textarea variant handles multi-line input
- [X] T005 [US1] Update `buildItemCard` in `todo_agent/gui/static/app.js` — replace `titleEl.textContent = item.title` with a `<span class="item-title-text">` child; call `makeInlineEdit(span, "input", item.title, v => v.trim().length > 0, async v => { const r = await apiPatch("/api/items/"+item.id, {title: v.trim()}); if (!r.ok) throw r; })` — blank title must be rejected client-side before any API call
- [X] T006 [US1] Update `buildItemCard` in `todo_agent/gui/static/app.js` — if `item.description` is non-null: render `<p class="item-description">` and call `makeInlineEdit` on it (textarea, validate = always true since null is allowed, onSave = `apiPatch({description: val.trim() || null})`); if null: render `<span class="add-desc-link">+ add description</span>` that when clicked appends an inline textarea; in both cases add `<button class="btn-clear-desc">✕</button>` that calls `apiPatch({description: null})` then `poll()`
- [X] T007 [US1] Update `buildItemCard` in `todo_agent/gui/static/app.js` — make the importance badge `<span class="badge badge-importance">` editable: call `makeInlineEdit(impBadge, "input", String(imp), v => Number.isInteger(+v) && +v >= 0 && +v <= 100, async v => { const r = await apiPatch("/api/items/"+item.id, {importance: +v}); if (!r.ok) throw r; })` with `type="number"` and `min=0 max=100` on the created input; importance 0–100 validated client-side; badge updates via poll after save
- [X] T008 [US1] Update `buildItemCard` in `todo_agent/gui/static/app.js` — replace the static deadline badge span with `<input type="date" class="deadline-input" value="${item.deadline || ''}">` that triggers `apiPatch("/api/items/"+item.id, {deadline: e.target.value || null})` then `poll()` on `change`; add `<button class="btn-clear-deadline">✕</button>` next to it that calls `apiPatch({deadline: null})` then `poll()`; the input is always visible (no click-to-reveal needed)
- [X] T009 [P] [US1] Add to `todo_agent/gui/static/style.css`: `.inline-edit-input { border: 2px solid #4299e1; border-radius: 3px; outline: none; padding: 0.1rem 0.3rem; background: #fff; font-size: inherit; width: 100%; box-sizing: border-box; }` and `.add-desc-link { font-size: 0.75rem; color: #aaa; cursor: pointer; display: block; margin: 0.1rem 0; }` and `.add-desc-link:hover { color: #555; }` and `.deadline-input { font-size: 0.78rem; border: 1px solid #ccc; border-radius: 3px; padding: 0.1rem 0.2rem; }` and `.btn-clear-desc, .btn-clear-deadline { background: none; border: none; cursor: pointer; color: #aaa; font-size: 0.75rem; padding: 0 0.2rem; }` and `.btn-clear-desc:hover, .btn-clear-deadline:hover { color: #c00; }`

**Checkpoint**: Items can be clicked to edit title, description, importance, deadline. Changes persist on reload. Blank title reverts without server call. Importance outside 0–100 reverts without server call.

---

## Phase 4: User Story 2 — Toggle Item Flags (Priority: P2)

**Goal**: Today and this-week flags are togglable via checkboxes directly on item cards; each toggle saves immediately.

**Independent Test**: Run quickstart.md Scenario 4. Check/uncheck each flag and confirm badge appears/disappears and persists on reload.

### Implementation for User Story 2

- [X] T010 [US2] Update `buildItemCard` in `todo_agent/gui/static/app.js` — replace the static `item.today` badge span with `<label class="badge badge-today flag-label"><input type="checkbox" class="flag-cb" ${item.today ? "checked" : ""}> today</label>`; on `change` event: `apiPatch("/api/items/"+item.id, {today: e.target.checked})` then `poll()`; do the same for `item.this_week` with class `badge-week` and `{this_week: e.target.checked}`; checkboxes inherit badge styling so the badge appears when checked and remains styled when unchecked but visually muted via CSS

**Checkpoint**: Checking "today" checkbox immediately shows "today" badge and saves; unchecking removes it. Same for this-week. Both flags are independent.

---

## Phase 5: User Story 3 — Edit Project Fields Inline (Priority: P3)

**Goal**: Project name is click-to-edit inline (bold black); project importance is click-to-edit inline.

**Independent Test**: Run quickstart.md Scenario 6. Rename a project and change its importance; both persist on reload.

### Implementation for User Story 3

- [X] T011 [P] [US3] Extend `PATCH /api/projects/:id` in `todo_agent/gui/server.py` — after the existing `if "importance" in body` block add `if "name" in body: operations.rename_project(project["name"], body["name"], lane["name"])`; map `ValueError` containing "already exists" → 409; other `ValueError` → 400; re-fetch and return fresh project dict as before
- [X] T012 [US3] Update `buildProjectSection` in `todo_agent/gui/static/app.js` — wrap project title in `<span class="project-title">`; call `makeInlineEdit(titleEl, "input", project.name, v => v.trim().length > 0, async v => { const r = await apiPatch("/api/projects/"+project.id, {name: v.trim()}); if (!r.ok) throw r; })` — blank name rejected client-side; after poll, card re-renders with new bold name
- [X] T013 [US3] Update `buildProjectSection` in `todo_agent/gui/static/app.js` — in the meta span, extract the importance value and make it click-to-edit: create a `<span class="project-importance-val">${project.importance}</span>` inside meta; call `makeInlineEdit(importanceSpan, "input", String(project.importance), v => Number.isInteger(+v) && +v >= 0 && +v <= 100, async v => { const r = await apiPatch("/api/projects/"+project.id, {importance: +v}); if (!r.ok) throw r; })` with `type="number"` and min=0 max=100; meta text format becomes `${pct} · imp <editable importance>`
- [X] T014 [P] [US3] Update `.project-title` rule in `todo_agent/gui/static/style.css` — change `font-weight: 600` to `font-weight: 700` and add `color: #111` (bold black project names per FR-008)

**Checkpoint**: Click project name to rename; click importance number to change. Both persist on reload. Blank name reverts. Duplicate name shows error state and reverts.

---

## Phase 6: User Story 4 — Collapsible Item Cards (Priority: P4)

**Goal**: Each item card has a per-card collapse toggle hiding all fields except the title. A global "Collapse all / Expand all" button controls all cards at once.

**Independent Test**: Run quickstart.md Scenario 7. Collapse one card (title only visible). Click "Collapse all" — all cards collapse. Click "Expand all" — all expand.

### Implementation for User Story 4

- [X] T015 [US4] Update `buildItemCard` in `todo_agent/gui/static/app.js` — wrap the existing `controls` div and description element in a `<div class="card-body">` wrapper; add `<button class="collapse-toggle" title="Collapse/expand">▼</button>` in the title row (before the delete button); on click: `cardBody.classList.toggle("hidden")`; update button text to `▲` when collapsed and `▼` when expanded; the title row (including collapse toggle and delete button) MUST remain visible when collapsed
- [X] T016 [US4] Add `<button id="collapse-all-btn" class="filter-btn">Collapse all</button>` inside the `<nav class="filters">` in `todo_agent/gui/templates/index.html`; in `DOMContentLoaded` in `todo_agent/gui/static/app.js` bind `#collapse-all-btn` click → toggle all `.card-body` elements between hidden/visible; update button label to "Expand all" when collapsed and "Collapse all" when expanded; `storeData` re-renders reset all cards to expanded (default)
- [X] T017 [P] [US4] Add `.collapse-toggle { background: none; border: none; cursor: pointer; font-size: 0.75rem; color: #999; padding: 0 0.25rem; flex-shrink: 0; }` and `.collapse-toggle:hover { color: #333; }` and `.flag-label { display: inline-flex; align-items: center; gap: 0.2rem; cursor: pointer; }` and `.flag-cb { cursor: pointer; }` to `todo_agent/gui/static/style.css`

**Checkpoint**: Individual and global collapse/expand both work. Collapsed card shows only title row (title + status + collapse toggle + delete). Page reload resets all to expanded.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T018 Add tests for `rename_item` and `rename_project` to `tests/unit/test_operations.py` — test rename_item stores new title; test blank new title raises ValueError; test duplicate title (case-insensitive) raises ValueError containing "already exists"; test rename_project stores new name; test blank new name raises ValueError; test duplicate project name in same lane raises ValueError containing "already exists"; test renaming to own current name should succeed (no false duplicate)

---

## Dependencies & Execution Order

- **T001**: No deps — start here. Blocks T003 (server.py title handler).
- **T002**: No deps — can run after or alongside T001 (same file, sequential). Blocks T011.
- **T003 [P]**: Requires T001. Parallel with T004.
- **T004 [P]**: No deps (new function in app.js). Parallel with T003.
- **T005–T008**: Each requires T004; sequential in app.js.
- **T009 [P]**: No deps; parallel with all app.js work (different file).
- **T010**: Requires T008 (continues app.js changes); sequential.
- **T011 [P]**: Requires T002; parallel with T012 (different file: server.py vs app.js).
- **T012–T013**: Sequential in app.js; require T010 to complete.
- **T014 [P]**: No deps (style.css); parallel with T012-T013.
- **T015–T016**: Sequential in app.js + index.html; require T013.
- **T017 [P]**: style.css; parallel with T015–T016.
- **T018**: Requires T001 + T002 complete.

### Parallel Opportunities

```
T001 → T002  (both in operations.py, sequential)
    │
    ├─ T003 [server.py] ─┐
    │                    │ parallel
    └─ T004 [app.js]  ───┤
                         │
                 T005 → T006 → T007 → T008 → T010 → T012 → T013 → T015 → T016  (app.js chain)
                 T009 [style.css - parallel throughout]
                 T011 [server.py, parallel with T012]
                 T014 [style.css, parallel with T012-T013]
                 T017 [style.css, parallel with T015-T016]
                 T018 [tests, parallel with frontend work after T001+T002]
```

## Implementation Strategy

### MVP (US1 — Item Field Editing Only)
1. T001 (rename_item operation)
2. T003 (server title/description/importance handlers) + T004 (makeInlineEdit helper) in parallel
3. T005 → T006 → T007 → T008 (title, description, importance, deadline in app.js)
4. T009 (CSS for edit inputs)
5. Validate with quickstart Scenarios 1–5

### Incremental Delivery
- US1 (T001–T009) → validate → US2 (T010) → US3 (T011–T014) → US4 (T015–T017) → Tests (T018)
- Each phase is independently testable before moving to the next

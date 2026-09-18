# Tasks: Item Data Model Enhancements

**Input**: Design documents from `specs/002-item-data-model/`

**Prerequisites**: plan.md ✓, spec.md ✓, data-model.md ✓, contracts/cli-tools-patch.md ✓

**Organization**: Tasks grouped by user story. US1 (description) and US2 (importance) share a
foundational schema change but can otherwise be implemented and tested independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Foundational (Blocking Prerequisite for Both Stories)

**Purpose**: Extend the item schema so both US1 and US2 can be implemented independently.

**⚠️ CRITICAL**: Both user stories depend on this phase.

- [X] T001 Update `todo_agent/core/operations.py` `add_item` function — add optional parameters `description: str | None = None` and `importance: int = 50`; include them in the `new_item` dict as `"description": description if description and description.strip() else None` and `"importance": importance`; also update the `Item` dataclass in `todo_agent/core/models.py` to add `description: str | None = None` and `importance: int = 50` fields

**Checkpoint**: `add_item` now stores `description` and `importance` in every new item dict; existing items load fine via `.get("description")` → None and `.get("importance", 50)` → 50.

---

## Phase 2: User Story 1 — Add Description to an Item (Priority: P1) 🎯 MVP

**Goal**: Users can set, update, and clear a free-text description on any item via the CLI; description appears below the title in the GUI board.

**Independent Test**: Run `todo "set description of Design homepage to: needs mobile-first approach"`, verify JSON, open `todo visualize` and confirm description appears on the card.

### Implementation for User Story 1

- [X] T002 [P] [US1] Implement `set_item_description(item_title: str, description: str | None, project_name: str | None = None, lane_name: str | None = None)` in `todo_agent/core/operations.py` — call `_find_item`; normalize: if description is a non-None empty/whitespace string set to None; set `item["description"] = description`; call `save_data(data)`; return updated item dict
- [X] T003 [P] [US1] Update `todo_agent/tools.py` — add optional `"description"` property (type string) to the `add_item` tool's `input_schema.properties`; add new tool 17 `set_item_description` per `specs/002-item-data-model/contracts/cli-tools-patch.md` with required fields `["item_title", "description"]` and optional `project_name`, `lane_name`; total TOOLS count becomes 17
- [X] T004 [US1] Add `set_item_description` dispatcher in `todo_agent/cli/main.py` — call `operations.set_item_description(item_title=tool_input["item_title"], description=tool_input.get("description"), project_name=tool_input.get("project_name"), lane_name=tool_input.get("lane_name"))`; if result `item["description"]` is non-null print `"Description for '{title}' set."` else print `"Description for '{title}' cleared."`
- [X] T005 [P] [US1] Update item card rendering in `todo_agent/gui/static/app.js` — after creating the title element, check `item.description`; if truthy create a `<p>` element with class `"item-description"` containing the description text and append to the card; if falsy/null omit the element entirely; use `item.description ?? null` to handle missing field from old items

**Checkpoint**: `todo "set description of Design homepage to: needs mobile-first"` stores description; `todo visualize` shows it below the title; items without description show no description area.

---

## Phase 3: User Story 2 — Set and View Item Importance (Priority: P2)

**Goal**: Users can set an item's importance score (0–100) via the CLI; the GUI board highlights items with importance > 80 with a distinct visual style.

**Independent Test**: Set importance of an item to 90 via CLI, open `todo visualize`, confirm that item has a coloured left border and a default-importance item does not.

### Implementation for User Story 2

- [X] T006 [P] [US2] Implement `set_item_importance(item_title: str, importance: int, project_name: str | None = None, lane_name: str | None = None)` in `todo_agent/core/operations.py` — call `_find_item`; call `validate_importance(importance)` (raises `ValueError` if not `0 <= importance <= 100`); set `item["importance"] = importance`; call `save_data(data)`; return updated item dict
- [X] T007 [P] [US2] Add new tool 18 `set_item_importance` to `todo_agent/tools.py` per `specs/002-item-data-model/contracts/cli-tools-patch.md` with `input_schema` requiring `["item_title", "importance"]` (importance type integer, minimum 0, maximum 100) and optional `project_name`, `lane_name`; total TOOLS count becomes 18
- [X] T008 [US2] Add `set_item_importance` dispatcher in `todo_agent/cli/main.py` — call `operations.set_item_importance(item_title=tool_input["item_title"], importance=tool_input["importance"], project_name=tool_input.get("project_name"), lane_name=tool_input.get("lane_name"))`; print `"Importance for '{item['title']}' set to {item['importance']}."`
- [X] T009 [P] [US2] Update item card rendering in `todo_agent/gui/static/app.js` — compute `const imp = item.importance ?? 50`; add `data-importance` attribute to card element; add `<span class="badge badge-importance">{imp}</span>` badge; add CSS class `item-high-importance` to card element when `imp > 80` (strictly greater than); class MUST NOT be applied when `imp === 80`
- [X] T010 [P] [US2] Update `todo_agent/gui/static/style.css` — add `.item-high-importance { border-left: 4px solid #e53e3e; background-color: #fff5f5; }` for the highlight; add `.badge-importance { background: #805ad5; color: white; font-size: 0.7rem; padding: 1px 5px; border-radius: 9999px; margin-left: 4px; }`

**Checkpoint**: `todo "set importance of Design homepage to 90"` persists value; `todo visualize` shows red left border on that card and purple importance badge; an item with importance 50 has no border and standard badge.

---

## Phase 4: Polish & Cross-Cutting Concerns

- [X] T011 [P] Add tests for description operations in `tests/unit/test_operations.py` — test `set_item_description` stores value; test empty string input stores null; test clearing (passing null) stores null; test `add_item` with `description="some text"` stores it; test loading item dict without `description` key uses `.get("description")` → None (backward compat check via direct dict access)
- [X] T012 [P] Add tests for importance operations in `tests/unit/test_operations.py` — test `set_item_importance` stores value; test boundary values 0 and 100 are accepted; test -1 and 101 raise `ValueError`; test `add_item` without importance arg → item dict has `"importance": 50`; test loading item dict without `importance` key defaults to 50 via `.get("importance", 50)`
- [X] T013 Update `tests/contract/test_tool_schemas.py` — change `assert len(TOOLS) == 16` to `assert len(TOOLS) == 18`; verify `set_item_description` tool has `required == ["item_title", "description"]`; verify `set_item_importance` tool has `required == ["item_title", "importance"]` and importance property has `minimum: 0, maximum: 100`

---

## Dependencies & Execution Order

- **Phase 1 (T001)**: No dependencies — start here. Blocks both US1 and US2.
- **US1 (T002–T005)**: All depend on T001. T002, T003, T005 are [P] (different files). T004 depends on T002 and T003.
- **US2 (T006–T010)**: All depend on T001. T006, T007, T009, T010 are [P]. T008 depends on T006 and T007.
- **Polish (T011–T013)**: T011 and T012 are [P]. T013 depends on T003 and T007 being complete.

### Parallel Opportunities

```
T001 (schema) → done, then:

  US1 in parallel:
    T002 (operations)  T003 (tools)  T005 (app.js)  →  T004 (main.py dispatch)

  US2 in parallel:
    T006 (operations)  T007 (tools)  T009 (app.js)  T010 (style.css)  →  T008 (main.py dispatch)

  Polish in parallel:
    T011 (desc tests)  T012 (importance tests)  T013 (contract test count)
```

## Implementation Strategy

### MVP (US1 only)
1. T001 (schema)
2. T002–T004 (description operations + CLI)
3. T005 (GUI display)
4. Validate with quickstart scenarios S1–S5

### Full delivery
Complete US2 (T006–T010) after US1 is verified, then run all polish tasks (T011–T013).

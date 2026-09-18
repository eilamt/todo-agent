# Tasks: CLI Multi-Tool Dispatch and Read Tools

**Input**: Design documents from `specs/004-cli-read-tools/`

**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/new-tool-schemas.md ✓, quickstart.md ✓

**Organization**: Foundational read operations first (both stories depend on them), then US1 (dispatch loop), then US2 (read tool dispatch branches and tests).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to

---

## Phase 2: Foundational (Blocking Prerequisites for Both Stories)

**Purpose**: Add four read operations to `core/operations.py` and register their tool schemas in `tools.py`. These are required before either user story's implementation can begin.

**⚠️ CRITICAL**: T001–T004 block T007 (read dispatch branches). T005 blocks T007 (agent needs tool schemas) and T010 (dispatch needs schemas for routing).

- [X] T001 Add `list_lanes() -> list[dict]` to `todo_agent/core/operations.py` — call `load_data()`; iterate `data["lanes"]`; return list of `{"id": lane["id"], "name": lane["name"], "project_count": len(lane["projects"])}` for each lane; return empty list if no lanes
- [X] T002 Add `list_projects(lane_name=None) -> list[dict]` to `todo_agent/core/operations.py` — call `load_data()`; iterate lanes and projects; if `lane_name` given skip lanes whose name doesn't match case-insensitively; return list of `{"id", "name", "lane", "importance" (default 50), "status", "percent_complete" (default 0), "item_count"}` for each project; return empty list if no match
- [X] T003 Add `list_items(project_name=None, lane_name=None) -> list[dict]` to `todo_agent/core/operations.py` — call `load_data()`; iterate lanes/projects/items; filter by `lane_name` and/or `project_name` case-insensitively when provided; return list of `{"id", "title", "project", "lane", "status", "today" (default False), "this_week" (default False), "deadline" (default None), "importance" (default 50), "description" (default None)}` for each item; return empty list if no match
- [X] T004 Add `get_item(item_title, project_name=None, lane_name=None) -> dict` to `todo_agent/core/operations.py` — call `load_data()` then `_find_item(data, item_title, project_name, lane_name)` (reuse existing helper; let `AmbiguousMatchError` and `ValueError` propagate); return `{"id", "title", "project", "lane", "status", "today", "this_week", "deadline", "importance", "description", "notes"}` where `notes = item.get("notes", [])`
- [X] T005 Add four new tool schemas to `todo_agent/tools.py` (append before `request_clarification`): `list_lanes` (no required fields), `list_projects` (optional `lane_name` string), `list_items` (optional `project_name` and `lane_name` strings), `get_item` (required `item_title` string, optional `project_name` and `lane_name`) — update module docstring from "18" to "22 LLM-callable tool definitions"; use exact schemas from `contracts/new-tool-schemas.md`

**Checkpoint**: `list_lanes`, `list_projects`, `list_items`, `get_item` exist in `operations.py` and all four appear in `tools.py` with correct schemas. `python3 -m pytest tests/ -q` still passes (93 tests).

---

## Phase 3: User Story 1 — Multi-Tool Dispatch (Priority: P1) 🎯 MVP

**Goal**: The CLI agent executes ALL tool calls returned in a single LLM response turn, loops until the LLM produces a final text response, enforces a 10-round limit, and returns the LLM's text summary to main.

**Independent Test**: Run quickstart.md Scenarios 1–2. A compound command ("add a project and three items") completes in a single invocation with all entities created.

### Implementation for User Story 1

- [X] T006 [US1] Modify `_dispatch(tool_name, tool_input)` in `todo_agent/cli/main.py` to return `str` from every existing branch — add `return` to the end of each `if/elif` block returning a brief confirmation string (e.g., `return f"Added lane '{lane['name']}'"` for `add_lane`); delete branches must still print the confirmation AND return the same string; `request_clarification` branch returns the question string; unknown-tool branch returns `f"ERROR: Unknown tool '{tool_name}'."` instead of `sys.exit(1)`; the function signature changes from `-> None` to `-> str`
- [X] T007 [US1] Rewrite `todo_agent/cli/agent.py` — replace `resolve_intent()` with `run_agent(user_text: str, data: dict, config: dict, dispatch_fn) -> str`; add `MAX_ROUNDS = 10` constant; implement the loop per `plan.md` §Implementation Details §3: first call uses `tool_choice={"type": "any"}`, subsequent calls use `{"type": "auto"}`; collect all `tool_use` blocks from each response; call `dispatch_fn(block.name, block.input)` for each; accumulate `tool_result` messages; loop until no `tool_use` blocks in response then return the text content; raise `ValueError` if `MAX_ROUNDS` exceeded; update system prompt: remove "use 'request_clarification' for display requests — do NOT use 'list_notes'..." sentence; add "You may call multiple tools in sequence. When done, respond with a brief summary."
- [X] T008 [US1] Update `main()` in `todo_agent/cli/main.py` — replace `from todo_agent.cli.agent import resolve_intent` with `from todo_agent.cli.agent import run_agent`; replace the `tool_name, tool_input = resolve_intent(...)` + `_dispatch(...)` block with `summary = run_agent(free_text, data, config, _dispatch)` followed by `print(summary)`; keep the existing `except` handlers but add `except ValueError` for the max-rounds case
- [X] T009 [US1] Create `tests/unit/test_agent.py` — test `run_agent` with mocked `anthropic.Anthropic`: (1) single tool call completes in one round and returns LLM's text summary; (2) two tool_use blocks in one response both execute and dispatch_fn is called twice; (3) LLM returns `end_turn` with no tool_use — returns text immediately; (4) LLM returns tool_use every round exceeding `MAX_ROUNDS` — raises `ValueError`; use `unittest.mock.patch` to mock `anthropic.Anthropic` and `client.messages.create`; set `ANTHROPIC_API_KEY` env var in tests via `monkeypatch`

**Checkpoint**: Run quickstart.md Scenarios 1–2 manually. Run `python3 -m pytest tests/unit/test_agent.py -q`. The dispatch loop works end-to-end for compound write commands.

---

## Phase 4: User Story 2 — List and Inspect Board State (Priority: P2)

**Goal**: `list_lanes`, `list_projects`, `list_items`, and `get_item` are callable by the LLM via the dispatch loop; the agent can answer read queries by calling these tools and returning structured results the LLM summarises into natural language.

**Independent Test**: Run quickstart.md Scenarios 3–9. A user asking "what's on my board?" gets a complete, accurate text summary.

### Implementation for User Story 2

- [X] T010 [US2] Add four read tool branches to `_dispatch()` in `todo_agent/cli/main.py` — each branch calls the corresponding `operations.*` function, prints a human-readable summary (e.g., count of items), and returns the `json.dumps(result)` string for the LLM tool_result: `list_lanes` → `operations.list_lanes()`; `list_projects` → `operations.list_projects(lane_name=tool_input.get("lane_name"))`; `list_items` → `operations.list_items(project_name=tool_input.get("project_name"), lane_name=tool_input.get("lane_name"))`; `get_item` → call `operations.get_item(...)` wrapped in try/except `AmbiguousMatchError` and `ValueError` to return error string instead of raising (so the LLM receives the error and can ask for clarification); add `import json` at top if not already present
- [X] T011 [US2] Add read operation tests to `tests/unit/test_operations.py` — add `TestListLanes` (empty board returns empty list; populated board returns correct project_count), `TestListProjects` (all projects; filtered by lane_name case-insensitively; nonexistent lane returns empty list), `TestListItems` (all items; filtered by project_name; filtered by lane_name; filtered by both; nonexistent project returns empty list), `TestGetItem` (returns correct item dict; nonexistent title raises ValueError; ambiguous title raises AmbiguousMatchError; disambiguation by project_name works)

**Checkpoint**: Run quickstart.md Scenarios 3–9. Run `python3 -m pytest tests/ -q`. All read tools return correct data.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [X] T012 Update `tests/contract/test_tool_schemas.py` — change `assert len(TOOLS) == 18` to `assert len(TOOLS) == 22`; update module docstring; add `test_list_lanes_no_required_fields()` (assert `required == []`); add `test_list_projects_optional_lane_name()` (assert `lane_name` in properties, not in required); add `test_list_items_optional_filters()` (assert `project_name` and `lane_name` in properties, neither in required); add `test_get_item_required_fields()` (assert `required == ["item_title"]`, `project_name` and `lane_name` optional)

---

## Dependencies & Execution Order

- **T001–T004**: No deps — sequential within `operations.py` (same file). Block T010.
- **T005**: No deps (different file: `tools.py`). Block T007 (agent needs TOOLS list updated).
- **T006**: Requires T005 complete (agent loop depends on dispatch returning str). Sequential in `main.py`.
- **T007**: Requires T005 + T006 (imports dispatch_fn, needs TOOLS updated). Sequential in `agent.py`.
- **T008**: Requires T007 (imports `run_agent`). Sequential in `main.py`.
- **T009**: Requires T007 (tests `run_agent`). Can run [P] after T007, parallel with T008.
- **T010**: Requires T001–T004 + T006 (adds branches to _dispatch, calls operations). Sequential in `main.py`.
- **T011**: Requires T001–T004. Can run [P] with T010.
- **T012**: Requires T005. Can run [P] with T006.

### Parallel Opportunities

```
T001 → T002 → T003 → T004  (operations.py, sequential same file)
T005  (tools.py, parallel with T001-T004)
    │
    ├─ T006 (main.py dispatch returns str)
    │      │
    │      └─ T007 (agent.py run_agent loop) ─── T009 [test_agent.py — parallel with T008]
    │                 │
    │                 └─ T008 (main.py main() uses run_agent)
    │
T001-T004 done + T006 done:
    ├─ T010 (main.py read dispatch branches)
    └─ T011 [test_operations.py — parallel with T010]

T005 done:
    └─ T012 [test_tool_schemas.py — parallel with T006+]
```

---

## Implementation Strategy

### MVP (US1 — Multi-Tool Dispatch Only)

1. T001–T005 (foundational operations + schemas)
2. T006 (dispatch returns str)
3. T007 (run_agent loop)
4. T008 (main wiring)
5. Validate with quickstart Scenarios 1–2

### Incremental Delivery

- US1 (T001–T009) → validate → US2 (T010–T011) → Polish (T012)
- After T008 the agent handles multi-tool write commands; US2 adds read tool answers

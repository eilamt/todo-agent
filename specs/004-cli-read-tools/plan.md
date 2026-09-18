# Implementation Plan: CLI Multi-Tool Dispatch and Read Tools

**Branch**: `004-cli-read-tools` | **Date**: 2026-09-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/004-cli-read-tools/spec.md`

## Summary

The CLI agent currently processes only the first LLM tool call per user turn and cannot answer read queries. This feature adds: (1) a full agentic dispatch loop that executes all tool calls returned in a single LLM response turn, loops until the LLM terminates with text, and enforces a 10-round safety limit; (2) four new read tools (`list_lanes`, `list_projects`, `list_items`, `get_item`) backed by pure-query operations in `core/operations.py`. No schema changes, no new dependencies.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `anthropic` SDK (already installed), `pytest` (already installed). No new dependencies.

**Storage**: Single JSON file via `core/store.py` (unchanged).

**Testing**: `pytest` — existing test suite (93 tests); new unit tests added for read operations and the dispatch loop.

**Target Platform**: Local macOS/Linux CLI (unchanged).

**Project Type**: CLI tool with LLM intent layer.

**Performance Goals**: Conversational — latency is dominated by LLM API calls; no additional latency targets.

**Constraints**: No new dependencies. No schema changes. No regressions in existing 93 tests.

**Scale/Scope**: Personal use — small data set. No pagination needed for read tools.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|-----------|-------|--------|
| I. Local-First | No network calls added beyond existing Anthropic SDK. | ✓ PASS |
| II. Single Source of Truth | All four read operations go through `core/operations.py` using `load_data()`. No direct file access in agent or main. | ✓ PASS |
| III. Deterministic Core | Read operations are pure functions over the data dict. The agentic loop is deterministic; only the LLM calls are generative. | ✓ PASS |
| IV. Simplicity | No new frameworks or libraries. The loop is a plain `while` with a counter. | ✓ PASS |
| V. Human-Readable State | No schema changes. JSON file unchanged. | ✓ PASS |
| VI. Staged Scope | No Phase 2 components. No scheduler, SMS, or push integration. | ✓ PASS |
| VII. User Control | Destructive-action confirmation path in `_dispatch()` is unchanged; it still blocks and prompts before deleting. | ✓ PASS |

**Post-design re-check**: All principles pass. No violations.

## Project Structure

### Documentation (this feature)

```text
specs/004-cli-read-tools/
├── plan.md              # This file
├── research.md          # Phase 0 decisions
├── data-model.md        # Return shapes for read operations
├── quickstart.md        # Validation scenarios
├── contracts/
│   └── new-tool-schemas.md  # 4 new tool schemas + run_agent() interface
└── tasks.md             # Phase 2 output (not yet created)
```

### Source Code Changes (repository root)

```text
todo_agent/
├── tools.py                    # Add 4 new tool schemas (18 → 22 tools)
├── core/
│   └── operations.py           # Add list_lanes, list_projects, list_items, get_item
└── cli/
    ├── agent.py                # Rewrite resolve_intent → run_agent (agentic loop)
    └── main.py                 # _dispatch returns str; main calls run_agent; prints result

tests/
├── unit/
│   ├── test_operations.py      # Add TestListLanes, TestListProjects, TestListItems, TestGetItem
│   └── test_agent.py           # Add tests for run_agent loop (mocked LLM)
└── contract/
    └── test_tool_schemas.py    # Update: 18 → 22 tools; add tests for 4 new schemas
```

## Implementation Details

### 1. `core/operations.py` — Four Read Functions

```python
def list_lanes() -> list[dict]:
    data = load_data()
    return [
        {"id": lane["id"], "name": lane["name"], "project_count": len(lane["projects"])}
        for lane in data["lanes"]
    ]

def list_projects(lane_name: str | None = None) -> list[dict]:
    data = load_data()
    results = []
    for lane in data["lanes"]:
        if lane_name and lane["name"].lower() != lane_name.lower():
            continue
        for project in lane["projects"]:
            results.append({
                "id": project["id"],
                "name": project["name"],
                "lane": lane["name"],
                "importance": project.get("importance", 50),
                "status": project["status"],
                "percent_complete": project.get("percent_complete", 0),
                "item_count": len(project.get("items", [])),
            })
    return results

def list_items(project_name: str | None = None, lane_name: str | None = None) -> list[dict]:
    data = load_data()
    results = []
    for lane in data["lanes"]:
        if lane_name and lane["name"].lower() != lane_name.lower():
            continue
        for project in lane["projects"]:
            if project_name and project["name"].lower() != project_name.lower():
                continue
            for item in project.get("items", []):
                results.append({
                    "id": item["id"],
                    "title": item["title"],
                    "project": project["name"],
                    "lane": lane["name"],
                    "status": item["status"],
                    "today": item.get("today", False),
                    "this_week": item.get("this_week", False),
                    "deadline": item.get("deadline"),
                    "importance": item.get("importance", 50),
                    "description": item.get("description"),
                })
    return results

def get_item(item_title: str, project_name: str | None = None, lane_name: str | None = None) -> dict:
    data = load_data()
    lane, project, item = _find_item(data, item_title, project_name, lane_name)
    return {
        "id": item["id"],
        "title": item["title"],
        "project": project["name"],
        "lane": lane["name"],
        "status": item["status"],
        "today": item.get("today", False),
        "this_week": item.get("this_week", False),
        "deadline": item.get("deadline"),
        "importance": item.get("importance", 50),
        "description": item.get("description"),
        "notes": item.get("notes", []),
    }
```

### 2. `tools.py` — Four New Tool Definitions

Add `list_lanes`, `list_projects`, `list_items`, `get_item` to the end of the `TOOLS` list before `request_clarification`. See `contracts/new-tool-schemas.md` for the exact schema JSON.

Update module docstring: "18" → "22 LLM-callable tool definitions".

### 3. `agent.py` — Agentic Loop

Replace `resolve_intent()` with `run_agent(user_text, data, config, dispatch_fn) -> str`:

```python
MAX_ROUNDS = 10

def run_agent(user_text: str, data: dict, config: dict, dispatch_fn) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set.")

    client = anthropic.Anthropic(api_key=api_key)
    model = config.get("model", "claude-haiku-4-5-20251001")

    system_prompt = (
        f"You are a to-do management assistant. Today's date is {date.today().isoformat()}.\n\n"
        "Current to-do state:\n"
        f"{_build_data_summary(data)}\n\n"
        "Use the available tools to fulfill the user's request. "
        "You may call multiple tools in sequence. "
        "When you have finished all actions, respond with a brief summary of what was done. "
        "Prefer 'request_clarification' over any destructive action when the intent is ambiguous."
    )

    messages = [{"role": "user", "content": user_text}]

    for round_num in range(MAX_ROUNDS):
        tool_choice = {"type": "any"} if round_num == 0 else {"type": "auto"}
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,
            tools=TOOLS,
            tool_choice=tool_choice,
            messages=messages,
        )

        # Collect tool_use blocks
        tool_uses = [b for b in response.content if b.type == "tool_use"]

        if not tool_uses:
            # LLM finished — extract final text
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return "(No response from assistant.)"

        # Validate and execute all tool calls
        tool_results = []
        for block in tool_uses:
            if block.name not in _VALID_TOOL_NAMES:
                raise ValueError(f"LLM returned unknown tool name: {block.name!r}.")
            result_str = dispatch_fn(block.name, block.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result_str,
            })

        # Add assistant turn + tool results to messages
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    raise ValueError(
        f"Agent exceeded {MAX_ROUNDS} tool-call rounds. "
        "Partial results were printed above."
    )
```

### 4. `main.py` Changes

- `_dispatch(tool_name, tool_input) -> str`: Add `return` statement to every branch returning a brief result string. Read tool branches (`list_lanes`, `list_projects`, `list_items`, `get_item`) serialize result to JSON string and return it; they also print a human-readable summary.
- `main()`: Replace `resolve_intent` call with `run_agent(free_text, data, config, _dispatch)`. Print the returned string as the LLM's final summary.

### 5. System Prompt Change

Remove: "For requests to display, list, show, or view data... use 'request_clarification' to tell the user to run 'todo visualize' instead."

Add: Instruction that multiple tools may be called; brief summary expected after completion.

### 6. `tests/unit/test_operations.py` — Read Operation Tests

Add `TestListLanes`, `TestListProjects`, `TestListItems`, `TestGetItem` classes with:
- Empty board edge cases
- Filtering by lane/project name
- `get_item` not-found raises `ValueError`
- `get_item` ambiguous raises `AmbiguousMatchError`

### 7. `tests/unit/test_agent.py` — Agent Loop Tests

New file with mocked LLM (`unittest.mock.patch`):
- Single tool call completes in one round
- Two tool calls in one LLM response, both executed
- LLM terminates with end_turn text response
- Max rounds exceeded raises `ValueError`

### 8. `tests/contract/test_tool_schemas.py`

Update: `assert len(TOOLS) == 18` → `assert len(TOOLS) == 22`. Add schema tests for each of the four new tools.

## Complexity Tracking

No constitution violations. No complexity justification needed.

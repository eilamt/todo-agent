# Research: CLI Multi-Tool Dispatch and Read Tools

## Decision 1: Agentic Loop Ownership

**Decision**: The conversation loop lives in `agent.py`. `resolve_intent()` is replaced by `run_agent(user_text, data, config, dispatch_fn)`, which maintains the message history, calls the LLM in a loop, and returns the LLM's final text summary.

**Rationale**: Keeping the loop in `agent.py` isolates all LLM-related code in the one file that is already designated as the LLM boundary (constitution Principle III). `main.py` stays thin: it builds data/config, calls `run_agent()`, and prints the result.

**Alternatives considered**:
- Loop in `main.py`: Would bloat the entry point and mix LLM concerns with I/O concerns. Rejected.
- Separate `loop.py` module: Adds a file without adding clarity. Rejected.

---

## Decision 2: `tool_choice` Per Turn

**Decision**: First LLM call uses `tool_choice={"type": "any"}` to force at least one action. Subsequent calls (after tool results are fed back) use `tool_choice={"type": "auto"}` to allow the LLM to respond with text when it is done.

**Rationale**: The agentic loop must terminate. `"any"` on every turn would prevent the LLM from ever producing a final text response. `"auto"` on the first call would allow the LLM to skip all tools and just chat — which breaks the current behaviour for ambiguous input (today handled by `request_clarification`).

**Alternatives considered**:
- Always `"auto"`: Breaks existing single-tool behaviour for simple commands. Rejected.
- Always `"any"`: Loop never terminates via normal text response. Rejected.

---

## Decision 3: Dispatch Return Value

**Decision**: `_dispatch(tool_name, tool_input)` is modified to return a brief result string in addition to printing to stdout. The returned string is used as the `content` in the `tool_result` message sent back to the LLM.

**Rationale**: The LLM needs structured confirmation of each tool result to decide what to do next. Printing side-effects are kept for the user; the return value is for the LLM. No new function is needed.

**Alternatives considered**:
- Separate `_dispatch_for_llm()` returning only strings: Duplicates logic. Rejected.
- Capturing stdout: Fragile and non-obvious. Rejected.

---

## Decision 4: Read Operations in `core/operations.py`

**Decision**: `list_lanes()`, `list_projects()`, `list_items()`, and `get_item()` are implemented in `core/operations.py` using `load_data()` and the existing `_find_item` helper. They do not mutate state.

**Rationale**: Constitution Principle II requires all data reads to go through the shared core module. Putting read functions directly in `agent.py` or `main.py` would violate this principle.

**Alternatives considered**:
- Read data directly in the dispatch handler: Violates Principle II. Rejected.
- Separate `read_operations.py` module: Adds a file without benefit; existing operations.py is the single source of truth. Rejected.

---

## Decision 5: Max Rounds Limit

**Decision**: The dispatch loop enforces a hard cap of 10 tool-call rounds per user turn. If the cap is reached, `run_agent()` raises a `ValueError` with a summary of what was completed.

**Rationale**: FR-004 requires this limit to prevent infinite loops. 10 rounds is generous for any real user request (most will need 1–3 rounds) while providing a safety net against pathological LLM behaviour.

**Alternatives considered**:
- No limit: Could loop indefinitely on a misbehaving LLM. Rejected.
- 5 rounds: May be too restrictive for large compound commands. Rejected.
- Configurable via config.json: Adds complexity without user value. Rejected.

---

## Decision 6: System Prompt Update

**Decision**: Remove the instruction "For requests to display, list, show, or view data, use `request_clarification` to tell the user to run `todo visualize` instead." Add brief descriptions of the four new read tools to the system prompt context.

**Rationale**: With native read tools available, redirecting to the GUI is no longer necessary or helpful. The LLM should be able to answer data queries directly via the read tools.

**Alternatives considered**:
- Keep the redirect instruction: Would suppress the new read tools. Rejected.
- Add elaborate read-tool guidance to the system prompt: The tool descriptions themselves are sufficient. Rejected.

---

## Decision 7: `get_item` Ambiguity Handling

**Decision**: `get_item` calls the existing `_find_item(data, title, project_name=None, lane_name=None)` helper. If the helper raises `AmbiguousMatchError`, the tool result contains the error message listing all matches. If no item is found, the result contains an error message.

**Rationale**: The existing ambiguity-detection logic is already tested and correct. Reusing it avoids duplication.

**Alternatives considered**:
- New lookup logic in `get_item`: Redundant with `_find_item`. Rejected.

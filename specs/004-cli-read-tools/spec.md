# Feature Specification: CLI Multi-Tool Dispatch and Read Tools

**Feature Branch**: `004-cli-read-tools`

**Created**: 2026-09-17

**Status**: Draft

**Input**: User description: "Add multi-tool dispatch and proper read/list tools to the CLI agent."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Multi-Tool Dispatch (Priority: P1)

A user types a compound instruction like "add a project called Website to Work lane and add three items: Homepage, About page, and Contact form". The agent understands this as multiple sequential actions and completes all of them in a single turn, reporting each result back without requiring additional prompts.

**Why this priority**: The current limitation of processing only the first tool call breaks the most natural way people give instructions. A user who says "add a project and three items" expects all of it to happen. Fixing this unlocks the full value of natural-language command-line interaction and is the most common source of user frustration.

**Independent Test**: A board with one lane can be populated with a project and multiple items using a single compound free-text command. After the command completes, all created entities are visible on the board.

**Acceptance Scenarios**:

1. **Given** a board with a "Work" lane, **When** the user types "add a project called Website to Work and add three tasks: Homepage, About, and Contact", **Then** the CLI creates the project and all three items, reporting success for each one.
2. **Given** a board with an existing item, **When** the user types "mark Task A as in-progress and set its deadline to next Friday", **Then** both the status and deadline are updated in one turn.
3. **Given** any board state, **When** the LLM's response includes multiple actions, **Then** each action is executed in sequence and all results are returned together before the LLM produces its final text summary.
4. **Given** the LLM issues three actions and the second one fails (e.g., duplicate name), **Then** the first action's result and the second action's error are both reported, and the third action is still attempted.

---

### User Story 2 - List and Inspect Board State (Priority: P2)

A user types "what's on my board?" or "show me all items in the Work lane" and the agent responds with a structured, readable summary of the requested data. The agent can answer questions about the current state without the user needing to open the GUI.

**Why this priority**: Without read tools, the agent can only mutate state — it cannot answer any question about what already exists. Read tools are what transform the CLI from a write-only command interface into a conversational assistant that can also help the user understand and navigate their tasks.

**Independent Test**: After populating a board via the CLI, a user can ask "list all items due today" and receive a correct, readable list without opening the GUI.

**Acceptance Scenarios**:

1. **Given** a board with two lanes and several projects, **When** the user asks "what lanes do I have?", **Then** the agent returns each lane's name and how many projects it contains.
2. **Given** a board with projects across multiple lanes, **When** the user asks "list all projects in the Work lane", **Then** only projects in that lane are returned, each showing name, importance, status, and completion percentage.
3. **Given** a board with items scattered across projects, **When** the user asks "what items are due today?", **Then** all items flagged as today are returned, each with their title, project, and status.
4. **Given** a board with an item called "Homepage", **When** the user asks "tell me about the Homepage task", **Then** the agent returns full details including title, description, status, deadline, importance, and which project/lane it belongs to.
5. **Given** an empty board, **When** the user asks "what's on my board?", **Then** the agent responds that no lanes or items exist yet.
6. **Given** an ambiguous item title (multiple items share a similar name), **When** the user asks "show me the budget task", **Then** the agent reports the ambiguity and asks the user to be more specific.

---

### Edge Cases

- What happens when a compound command mixes read and write actions (e.g., "add a task and then show me all tasks")?  The write actions execute first, then the read actions run — all in the same turn.
- What happens when `list_items` is called with a lane or project name that does not exist? The agent returns an empty list and notes that no matching items were found.
- What happens when `get_item` is called with a title that matches zero items? The tool returns an error result and the agent reports "no item found with that title".
- What happens when `get_item` is called with a title that matches more than one item? The tool returns an error result listing all matches, and the agent prompts the user to be more specific (e.g., by specifying the project).
- What happens if the LLM keeps requesting more tool calls than a reasonable limit? The dispatch loop enforces a maximum of 10 tool-call rounds per user turn to prevent infinite loops, then stops and reports partial results.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The CLI agent MUST execute all tool calls returned by the LLM in a single response turn, not just the first one.
- **FR-002**: After executing all tool calls in a turn, the CLI agent MUST send all tool results back to the LLM in a single follow-up message before awaiting the LLM's next response.
- **FR-003**: The dispatch loop MUST continue until the LLM returns a final response with no pending tool calls (stop condition: no tool-use blocks in response).
- **FR-004**: The dispatch loop MUST enforce a maximum of 10 tool-call rounds per user turn to prevent infinite loops; if the limit is reached, the agent MUST stop and report what was completed so far.
- **FR-005**: The system MUST expose a `list_lanes` read tool that returns all lanes with their id, name, and project count.
- **FR-006**: The system MUST expose a `list_projects` read tool that returns all projects optionally filtered by lane name; each result includes id, name, lane name, importance, status, percent complete, and item count.
- **FR-007**: The system MUST expose a `list_items` read tool that returns all items optionally filtered by project name and/or lane name; each result includes id, title, project name, lane name, status, today flag, this_week flag, deadline, importance, and description.
- **FR-008**: The system MUST expose a `get_item` read tool that returns full details for a single item identified by title; if no item matches, the tool returns an error; if multiple items match, the tool returns an error listing all matches.
- **FR-009**: All four read tools MUST be callable by the LLM via the same tool-call mechanism used for existing write tools — no special-casing or separate path.
- **FR-010**: Read tool results MUST be derived exclusively from the shared core data module; no read tool may query the data file directly.
- **FR-011**: The data schema and file format MUST remain unchanged; no new fields, no migration required.
- **FR-012**: Read tools MUST be registered in the same tool definitions list used to build the LLM tool schema, so the LLM is aware of them and can choose to call them.

### Key Entities

- **Tool Result**: The structured response returned by executing one tool call — contains the tool use id, success/error status, and the result payload (list of records or error message).
- **Tool Round**: One iteration of the dispatch loop — one LLM response containing N tool calls, followed by N tool results sent back to the LLM.
- **Read Tool**: A tool that queries the in-memory data and returns structured data without mutating state — list_lanes, list_projects, list_items, get_item.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A compound free-text command requesting N distinct actions results in exactly N operations being performed in a single CLI invocation, with no prompt required between them.
- **SC-002**: A user asking "what's on my board?" receives a complete, accurate summary of all lanes, projects, and items without opening the GUI.
- **SC-003**: All four read tools (list_lanes, list_projects, list_items, get_item) return correct results consistent with the current board state, as verified by comparing tool output to the raw data file.
- **SC-004**: The dispatch loop correctly terminates after the LLM's final text response with no further tool calls — no hang, no infinite loop, no premature exit on intermediate turns.
- **SC-005**: 100% of existing CLI and GUI tests continue to pass after this change — no regressions introduced.

## Assumptions

- The data set is small (personal use, typically fewer than a few hundred items), so returning all items in a single `list_items` response without pagination is acceptable.
- The existing `_find_item` ambiguity-detection logic in the core module is sufficient for `get_item`; no new fuzzy-matching is needed.
- The dispatch loop processes tool calls sequentially within each round (not in parallel), which avoids write-write conflicts on the shared data file.
- The GUI and its REST API are unaffected by this change; only the CLI agent loop and the tool definitions list are modified.
- Existing write tools continue to work exactly as before; multi-tool dispatch is purely additive to the existing single-tool path.

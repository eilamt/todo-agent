# Feature Specification: Reduce API Cost — Lazy Context and Prompt Caching

**Feature Branch**: `010-reduce-api-cost`

**Created**: 2026-09-25

**Status**: Draft

**Input**: User description: "Reduce Claude API cost by (1) shrinking the per-call data summary sent to the LLM and (2) enabling prompt caching on the static prefix."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Lazy Board Summary (Priority: P1)

The agent receives a compact index of the board instead of the full item dump. When it needs details about specific items it fetches them via read tools during the conversation.

**Why this priority**: The dynamic data summary is the dominant cost driver (~10,400 of 14,777 tokens per call and growing). Shrinking it is the single highest-impact change and is prerequisite to meaningful cost reduction at scale.

**Independent Test**: Run `todo "show me what's due today"` and inspect the cost log. Input tokens per call must be below 7,000 (vs ~14,777 before). Verify the response is still correct — today's items are listed accurately. The agent may now make additional read-tool calls to fetch details; this is expected and correct.

**Acceptance Scenarios**:

1. **Given** a board with 3 lanes, 5 projects, and 32 items, **When** the user asks "show me what's due today", **Then** the agent returns the correct set of today-flagged items, regardless of how many internal steps it takes to do so.
2. **Given** a board with 3 lanes, 5 projects, and 32 items, **When** any CLI request is made, **Then** the context sent to the AI on the first step contains lane names, project names, and item counts only — no individual item titles, flags, deadlines, or descriptions.
3. **Given** the user asks "add a task called write tests to the Backend project", **Then** the agent correctly identifies the project and adds the item without needing the full item list provided upfront.
4. **Given** the user asks a question that requires knowing item flags (e.g. "what's due this week"), **Then** the agent fetches that information using its available read tools and returns a correct answer.
5. **Given** a project name that is ambiguous across lanes, **When** the user refers to it, **Then** the agent uses read tools to disambiguate rather than relying on upfront context.

---

### User Story 2 — Prompt Caching on Static Context (Priority: P2)

The fixed, unchanging portion of the agent's context is marked so the AI platform can reuse it across requests without reprocessing it each time, reducing the billable cost on repeated use within the same session.

**Why this priority**: Caching the ~4,342-token static portion cuts its cost by ~90% for every follow-on request within a 5-minute window. It is a low-risk change with guaranteed savings on multi-turn or rapid-fire usage.

**Independent Test**: Make two CLI requests within 60 seconds of each other. Run `todo cost report`. The second request must show cached token reads in the cost log, and its estimated cost must be lower than the first request's cost for an equivalent amount of work.

**Acceptance Scenarios**:

1. **Given** two CLI requests made within 5 minutes of each other, **When** the cost log is inspected after the session, **Then** the second request shows tokens served from cache and a correspondingly lower input cost.
2. **Given** two CLI requests separated by more than 5 minutes, **When** the second request is made, **Then** the static context is re-cached (cache creation tokens appear again) and cost reflects a full input charge for that request.
3. **Given** the caching change is deployed, **When** `todo cost report` is run after a day of normal use, **Then** the report shows non-zero cached token reads in the cache-read column.
4. **Given** the dynamic board index (which changes per request), **When** a request is made, **Then** the dynamic portion is never cached — only the static instructions are cached — ensuring the agent always sees fresh board data.

---

### Edge Cases

- What happens when the board is empty (no lanes, no projects)? The compact index shows an empty-board message and the agent handles write requests normally.
- What if a project has 0 items? The index shows the project with a count of 0; the agent can still add items to it.
- What if the user asks about a specific item by title that is not visible in the compact index? The agent must use read tools to find it; it must not claim the item doesn't exist without searching.
- What if the platform-side cache expires or fails silently? The agent continues normally; the next request simply incurs full input cost again — no error is surfaced to the user.
- What if the user modifies the board and then immediately queries it? The on-demand read tools return the current state, so the response will reflect the change just made.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The context provided to the AI at the start of each agent run MUST contain only: today's date, a compact board index (lane names, project names, item counts per project, inbox note count), and behavioural instructions. It MUST NOT include individual item titles, statuses, flags, descriptions, deadlines, or importance scores.
- **FR-002**: The compact board index MUST reflect the current state of the board at the moment of each request — it is not pre-computed or stored.
- **FR-003**: The agent MUST remain capable of fulfilling all currently supported request types, including: viewing items by flag (today/this-week/this-weekend), adding/updating/deleting items, setting deadlines and flags, reading and promoting inbox notes. It achieves this by using read tools on demand when it needs detail not present in the compact index.
- **FR-004**: The agent context MUST be structured so the static instructions are clearly separated from the dynamic board index, allowing the static portion to be cached independently of the dynamic portion.
- **FR-005**: The static instructions MUST be eligible for reuse by the AI platform across requests arriving within a 5-minute window, reducing the token cost of those follow-on requests.
- **FR-006**: The dynamic board index MUST NOT be eligible for reuse — it is always sent fresh so the agent sees current board state.
- **FR-007**: The cost tracking system (feature 009) MUST continue to correctly record cached and non-cached token counts in the cost log; no changes to the log format are required.
- **FR-008**: All existing automated tests MUST continue to pass without modification.

### Key Entities

- **Compact Board Index**: A short textual representation of the board containing: list of lanes (name only), per-lane list of projects (name + item count), and total inbox note count. Target size: under 500 tokens for a board with 10 projects and 50 items.
- **Static Context Block**: The unchanging portion of the agent's instructions — date format, tool-use guidance, behavioural rules — eligible for platform-side caching.
- **Dynamic Context Block**: The compact board index, regenerated on every request, never cached.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After the change, the number of tokens consumed per CLI request drops by at least 50% compared to the pre-change baseline of ~14,777 tokens per call, measured via `todo cost report` after a day of normal use.
- **SC-002**: Within a session where two requests arrive within 5 minutes of each other, at least one log record shows tokens served from cache with a correspondingly lower cost estimate.
- **SC-003**: All existing automated tests continue to pass — no regressions introduced.
- **SC-004**: A replay run against the standard utterance set after the change produces agent responses that are functionally equivalent to the pre-change baseline: the same actions are taken on the board, though the agent may make additional read steps to fetch detail on demand.
- **SC-005**: The agent's responses to a representative set of queries (today's items, this-week items, add/update/delete operations, inbox note operations) remain correct and complete after the change.

## Assumptions

- The existing read tools (list items, get item, list inbox notes, get inbox note, list projects, list lanes) are sufficient for the agent to fetch any detail it needs on demand — no new tools are required.
- The compact board index will typically be under 500 tokens even for large boards, making the total context well under 5,000 tokens and significantly cheaper than the current ~14,777 tokens.
- The AI platform's 5-minute reuse window is the appropriate tier — the user's request cadence (multiple requests per work session) will produce cache hits within 5 minutes.
- The agent may make more steps per user request after this change (e.g. an extra read step to fetch flag details). This is acceptable as long as total token cost per user request decreases.
- A slight increase in response latency is acceptable in exchange for cost reduction, provided responses remain subjectively fast.
- The pre-change baseline for comparison is the data already in the cost log from 2026-09-25 (~14,777 input tokens per call).

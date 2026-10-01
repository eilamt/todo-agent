# Feature Specification: API Cost and Token Instrumentation

**Feature Branch**: `009-api-cost-instrumentation`

**Created**: 2026-09-22

**Status**: Draft

**Input**: User description: "Add cost and token instrumentation to the todo agent so I can measure what its Claude API calls actually cost, and decide whether prompt caching or a local model is worth pursuing."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Per-Call Cost Log (Priority: P1)

After a day of normal use the user runs a summary command and sees their API cost per request and per day.

**Why this priority**: This is the core measurement capability. Without the log, no other analysis is possible. It is also the simplest to verify — the user just needs to see a JSONL file grow as they use the CLI.

**Independent Test**: Use the CLI agent to process three natural-language requests. Open `~/.todo-agent/api-calls.jsonl` and confirm three or more log entries exist (multi-round trips may produce more). Each entry must contain `timestamp`, `request_id`, `model`, `input_tokens`, `output_tokens`, `latency_ms`, `seconds_since_previous_call`, and `estimated_cost_usd`. The estimated cost must be a positive number.

**Acceptance Scenarios**:

1. **Given** the CLI agent processes a user request that requires two LLM round-trips, **When** the request completes, **Then** two entries are appended to the log, both sharing the same `request_id`, with correct token counts and a non-negative cost.
2. **Given** the log file directory does not exist, **When** the agent starts, **Then** the directory is created automatically and logging proceeds without any error visible to the user.
3. **Given** the log file is not writable (e.g., permissions error), **When** the agent processes a request, **Then** the agent completes normally and produces its normal output; a warning is printed to stderr but the request does not fail.
4. **Given** two consecutive user requests separated by less than 5 minutes, **When** the second request's first API call is logged, **Then** `seconds_since_previous_call` is less than 300.

---

### User Story 2 - Summary Report (Priority: P2)

The user runs a report command and sees per-day and overall statistics from their log, including cost per request and cache-hit potential.

**Why this priority**: The log alone is not human-readable. The summary command turns raw data into the decision support the user actually needs.

**Independent Test**: Populate the log with at least 5 synthetic entries spanning two calendar days (can be done by running the agent twice on separate days or by hand-editing the JSONL). Run `todo cost report`. Confirm output contains: request count, API call count, calls-per-request ratio, token totals by type, total and mean cost, and the percentage of API calls that arrived within 5 minutes of the previous call.

**Acceptance Scenarios**:

1. **Given** a populated log file, **When** the user runs the summary command, **Then** the output shows a per-day breakdown and an overall total row.
2. **Given** the log contains calls with `cache_read_input_tokens > 0`, **When** the summary is printed, **Then** cache read tokens are shown as a separate column.
3. **Given** no log file exists, **When** the user runs the summary command, **Then** a clear "no data yet" message is shown rather than an error.

---

### User Story 3 - Prefix Size Measurement (Priority: P3)

The user runs a one-off command to learn how many tokens the agent's static prefix (tool schemas + system prompt) consumes, and whether it qualifies for prompt caching.

**Why this priority**: Knowing prefix size is a prerequisite to deciding whether to enable caching, but it only needs to run occasionally.

**Independent Test**: Run `todo cost prefix`. Confirm it prints the token count of the static prefix (tools + system prompt) and a clear yes/no statement about whether the count meets the minimum cacheable length for Haiku 4.5 (4,096 tokens). The count must match a manual token count via the Anthropic Console.

**Acceptance Scenarios**:

1. **Given** the tool schema + system prompt token count exceeds 4,096, **When** the command runs, **Then** it prints the count and "Prefix meets the minimum cacheable length for Haiku 4.5 (4,096 tokens)."
2. **Given** the token count is below 4,096, **When** the command runs, **Then** it prints the count and "Prefix does NOT meet the minimum cacheable length."
3. **Given** the Anthropic API is unreachable, **When** the command runs, **Then** it prints a clear error and exits with a non-zero code.

---

### User Story 4 - Replay Harness (Priority: P4)

The user runs a replay script against a fixed set of utterances in dry-run mode to establish a cost baseline without modifying real data, and can diff the generated tool chains between runs to detect behavioral changes.

**Why this priority**: The replay harness is the most complex story and adds the least immediate day-to-day value; the user needs cost data first.

**Independent Test**: Create a replay utterances file with 3 entries. Run `todo cost replay utterances.txt`. Confirm: (a) no real data file was modified, (b) a tool-chain output file was written with one entry per utterance, (c) the log file gained entries tagged `"replay": true`, (d) running the replay a second time and diffing the output files shows no changes if the model behavior is stable.

**Acceptance Scenarios**:

1. **Given** a replay utterances file with N entries, **When** the replay runs, **Then** N tool-chain entries are written to the output file and N or more log entries are appended (tagged replay).
2. **Given** dry-run mode is active, **When** the agent selects a write tool (e.g., `add_item`), **Then** the tool call is recorded in the output but no actual write happens.
3. **Given** a configurable inter-utterance gap of 2 seconds, **When** the replay runs, **Then** the wall-clock time between consecutive API call groups is at least 2 seconds.
4. **Given** two successive replay runs with identical input, **When** the output files are diffed, **Then** the tool-chain portions are identical (timestamps and costs may differ).

---

### Edge Cases

- What happens when the log file is corrupted (non-JSONL content)? The summary command skips unparseable lines and reports how many were skipped.
- What if `seconds_since_previous_call` cannot be computed (first call ever)? The field is recorded as `null`.
- What if the replay utterances file is empty? The command exits cleanly with a "no utterances to replay" message.
- What if two CLI processes run simultaneously and both try to append to the log? Appends are atomic at the OS level for line-size records on the local filesystem; no locking is required.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST append one JSON record per Claude API call to an append-only log file (`~/.todo-agent/api-calls.jsonl`) immediately after each call completes.
- **FR-002**: Each log record MUST contain: `timestamp` (UTC ISO-8601), `request_id` (UUID shared across all API calls in one user request), `model` (model ID string), `input_tokens` (int), `output_tokens` (int), `cache_creation_input_tokens` (int, 0 if absent), `cache_read_input_tokens` (int, 0 if absent), `latency_ms` (int), `seconds_since_previous_call` (float or null), `estimated_cost_usd` (float), and optionally `replay` (bool, present and true only during replay runs).
- **FR-003**: The system MUST NOT log user utterance text or tool call arguments at any log level.
- **FR-004**: The cost estimate MUST be computed from a price table in configuration, with a `last_verified` date field. Initial prices: input $1.00/M tokens, 5-min cache write $1.25/M, 1-hr cache write $2.00/M, cache read $0.10/M, output $5.00/M.
- **FR-005**: Instrumentation failures (log not writable, etc.) MUST NOT raise exceptions visible to the user or alter the agent's output; a warning MAY be printed to stderr.
- **FR-006**: The system MUST provide a `todo cost report` command that reads the log and prints per-day and overall statistics: user request count, API call count, API calls per request, total tokens by type (input, output, cache-creation, cache-read), total estimated cost, mean cost per request, and the percentage of API calls arriving within 5 minutes of the previous call.
- **FR-007**: The system MUST provide a `todo cost prefix` command that calls the Anthropic token-counting endpoint with the agent's static prefix (tool schemas + system prompt) and reports the token count alongside a statement of whether it meets the 4,096-token minimum cacheable length for Haiku 4.5.
- **FR-008**: The minimum cacheable prefix length (4,096 tokens) MUST be stored in configuration alongside the price table, with a `last_verified` date.
- **FR-009**: The system MUST provide a `todo cost replay <utterances_file>` command that sends each line of the utterances file through the agent in dry-run mode (no writes to the real data store), with a configurable inter-utterance gap (default 1 second), writes the generated tool chain for each utterance to an output file, and logs each API call tagged as replay.
- **FR-010**: In dry-run mode, write tools (add, update, delete, move, reorder operations) MUST be intercepted before execution and recorded as "would call" entries in the tool-chain output without side effects. Read tools MAY execute normally.
- **FR-011**: The instrumentation MUST add negligible latency overhead — the measurement cost must not be perceptible to the user during normal CLI interaction.

### Key Entities

- **API Call Log Record**: One record per Anthropic API call. Fields: `timestamp`, `request_id`, `model`, `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`, `latency_ms`, `seconds_since_previous_call`, `estimated_cost_usd`, optional `replay`.
- **Price Table**: Configuration object with per-token prices and a `last_verified` date. Prices are in USD per million tokens.
- **Replay Utterances File**: Plain text, one natural-language utterance per line; blank lines and `#` comment lines are ignored.
- **Tool Chain Output**: One JSON object per utterance listing the sequence of tool calls the agent selected (in dry-run mode, writes are annotated, not executed).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After one day of normal use (any number of CLI requests), the user can run `todo cost report` and see their total estimated cost and mean cost per request without any manual data extraction.
- **SC-002**: A replay run against 20–30 realistic utterances completes in under 5 minutes and produces a baseline tool-chain file and a baseline cost figure.
- **SC-003**: The `todo cost prefix` command returns a token count and caching eligibility verdict in under 3 seconds on a normal internet connection.
- **SC-004**: Instrumentation overhead adds no more than 5 ms of wall-clock time to any individual CLI request (excluding the actual API call latency).
- **SC-005**: Running the replay harness twice with identical input produces tool-chain output files that are identical line-by-line (ignoring timestamps and cost fields), making behavioral regressions detectable by diff.

## Assumptions

- The Anthropic Python SDK exposes `usage.cache_creation_input_tokens` and `usage.cache_read_input_tokens` on the response object (or returns 0/None when absent). If the SDK does not expose these fields, they default to 0.
- The minimum cacheable prefix length for Haiku 4.5 is 4,096 tokens per current Anthropic documentation; this value is stored in config so it can be updated without a code change.
- Haiku 4.5 has two prompt-caching tiers (5-minute and 1-hour); the price table stores both. Cache tier selection is determined by the Anthropic platform, not by the client.
- The log file (`~/.todo-agent/api-calls.jsonl`) is written by a single process at a time under normal conditions; concurrent multi-process writes are not a design target.
- Dry-run mode in the replay harness is implemented by intercepting the dispatch function — no separate "dry-run flag" is plumbed through the core data module.
- The replay utterances file is maintained by the user; the system only reads it.
- The GUI server does not make Anthropic API calls and requires no instrumentation.

# Data Model: API Cost and Token Instrumentation

## Entity 1: API Call Log Record

One record is appended to `~/.todo-agent/api-calls.jsonl` after each `client.messages.create()` call completes.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `timestamp` | string (ISO-8601 UTC) | yes | UTC time the API call completed, e.g. `"2026-09-22T14:03:22.451Z"` |
| `request_id` | string (UUID4) | yes | Groups all API round-trips from a single user CLI request |
| `model` | string | yes | Model ID used for the call, e.g. `"claude-haiku-4-5-20251001"` |
| `input_tokens` | integer ≥ 0 | yes | Non-cached input tokens billed at standard input rate |
| `output_tokens` | integer ≥ 0 | yes | Output tokens generated |
| `cache_creation_5m_tokens` | integer ≥ 0 | yes | Tokens written to 5-minute cache (from `usage.cache_creation.ephemeral_5m_input_tokens`); 0 if absent |
| `cache_creation_1h_tokens` | integer ≥ 0 | yes | Tokens written to 1-hour cache (from `usage.cache_creation.ephemeral_1h_input_tokens`); 0 if absent |
| `cache_read_input_tokens` | integer ≥ 0 | yes | Tokens read from cache (from `usage.cache_read_input_tokens`); 0 if absent |
| `latency_ms` | integer ≥ 0 | yes | Wall-clock milliseconds from request send to response received |
| `seconds_since_previous_call` | float or null | yes | Seconds between this call's timestamp and the previous call's timestamp across all requests; `null` if no previous record exists |
| `estimated_cost_usd` | float ≥ 0 | yes | Estimated USD cost computed from the price table |
| `replay` | boolean | no | Present and `true` only for calls made during a replay run; absent in normal operation |

### Example Record

```json
{
  "timestamp": "2026-09-22T14:03:22.451Z",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "model": "claude-haiku-4-5-20251001",
  "input_tokens": 512,
  "output_tokens": 48,
  "cache_creation_5m_tokens": 0,
  "cache_creation_1h_tokens": 0,
  "cache_read_input_tokens": 0,
  "latency_ms": 423,
  "seconds_since_previous_call": 34.2,
  "estimated_cost_usd": 0.000752
}
```

### Validation Rules

- `timestamp` must be parseable as ISO-8601 UTC; records with unparseable timestamps are skipped by the summary command.
- All integer token fields default to 0 if absent in the SDK response (not null).
- `estimated_cost_usd` is computed, not stored from an external source; treat as an estimate.
- The log file is append-only. Records are never deleted or modified.

---

## Entity 2: Price Table

Stored as constants in `todo_agent/config.py`. Not written to disk — derived from code at runtime.

| Field | Type | Value (initial) | Description |
|-------|------|-----------------|-------------|
| `input` | float (USD/M tokens) | 1.00 | Standard (non-cached) input tokens |
| `cache_write_5m` | float (USD/M tokens) | 1.25 | 5-minute ephemeral cache write |
| `cache_write_1h` | float (USD/M tokens) | 2.00 | 1-hour ephemeral cache write |
| `cache_read` | float (USD/M tokens) | 0.10 | Cache read tokens |
| `output` | float (USD/M tokens) | 5.00 | Output tokens |
| `last_verified` | string (ISO date) | "2026-09-22" | Date prices were last confirmed against Anthropic docs |

---

## Entity 3: Tool Chain Output Record

One JSON object per utterance, written to the replay output file (one per line, JSONL).

| Field | Type | Description |
|-------|------|-------------|
| `utterance` | string | The input utterance text |
| `tool_calls` | array of objects | Ordered list of tools the agent selected |
| `tool_calls[].name` | string | Tool name |
| `tool_calls[].input` | object | Tool arguments as provided by the LLM |
| `tool_calls[].dry_run` | boolean | `true` if the tool was intercepted (write op); `false` if actually executed (read op) |
| `request_id` | string (UUID4) | Links to log records for this utterance |

### Example

```json
{
  "utterance": "add a task called write tests to the Backend project",
  "request_id": "c3d4e5f6-...",
  "tool_calls": [
    {
      "name": "add_item",
      "input": {"project_name": "Backend", "item_title": "write tests"},
      "dry_run": true
    }
  ]
}
```

---

## Entity 4: Replay Utterances File

Plain text file maintained by the user. One natural-language utterance per line.

**Format rules**:
- Blank lines are ignored.
- Lines starting with `#` are treated as comments and ignored.
- All other lines are sent to the agent verbatim.

### Example (`replay_utterances.txt`)

```
# Inbox operations
add an inbox note about redesigning the login flow
list inbox notes
promote the login flow note

# Board operations
show me what's due today
add a project called API Refactor to the Backend lane
add a task to finish auth tests to the API Refactor project
mark finish auth tests as completed
```

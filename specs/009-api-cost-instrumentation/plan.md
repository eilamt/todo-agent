# Implementation Plan: API Cost and Token Instrumentation

**Branch**: `009-api-cost-instrumentation` | **Date**: 2026-09-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/009-api-cost-instrumentation/spec.md`

## Summary

Add purely-observational instrumentation to the Claude API calls made by the todo agent's LLM loop. Every call appends a JSON Lines record (tokens, latency, cost estimate) to `~/.todo-agent/api-calls.jsonl`. Three new `todo cost` subcommands — `report`, `prefix`, and `replay` — expose summary statistics, prefix token counts, and a dry-run replay harness. No agent behaviour, prompts, or outputs change. No new external dependencies.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `anthropic` SDK (already present), Python stdlib only for all new code

**Storage**: Append-only JSONL at `~/.todo-agent/api-calls.jsonl`; price constants in `todo_agent/config.py`

**Testing**: pytest (existing suite at `tests/`)

**Target Platform**: macOS / Linux local CLI

**Project Type**: CLI tool with LLM agent loop

**Performance Goals**: Instrumentation adds ≤ 5 ms overhead per CLI request (write one JSONL line)

**Constraints**: Instrumentation failures must never raise to the user; no new external services

**Scale/Scope**: Single-user local use; log file expected to stay well under 10 MB for a year of normal use

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Local-First | ✅ PASS | Log written to `~/.todo-agent/`; no network calls beyond existing Anthropic SDK |
| II. Single Source of Truth | ✅ PASS | `todo_agent/instrumentation.py` owns all log I/O |
| III. Deterministic Core | ✅ PASS | Instrumentation is purely observational; LLM loop unchanged |
| IV. Simplicity | ✅ PASS | No new packages; stdlib only |
| V. Human-Readable State | ✅ PASS | JSONL is plain text |
| VI. Staged Scope | ✅ PASS | No Phase 2 features touched |
| VII. User Stays in Control | ✅ PASS | No destructive actions added |

No violations. Complexity Tracking section is not required.

## Project Structure

### Documentation (this feature)

```text
specs/009-api-cost-instrumentation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── cost-cli.md      # CLI contract for todo cost {report,prefix,replay}
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
todo_agent/
├── config.py                # +get_log_path(), +PRICE_TABLE, +MIN_CACHEABLE_PREFIX_TOKENS
├── instrumentation.py       # NEW: compute_cost(), append_log_record(), load_log_records()
├── cli/
│   ├── agent.py             # Modified: wrap messages.create() with timing + log call
│   ├── cost.py              # NEW: cmd_report(), cmd_prefix(), cmd_replay()
│   └── main.py              # Modified: add 'cost' reserved subcommand dispatch
└── tools.py                 # Unchanged

tests/
├── unit/
│   ├── test_instrumentation.py   # NEW: unit tests for instrumentation module
│   └── test_cost_report.py       # NEW: unit tests for report formatting
└── contract/
    └── test_tool_schemas.py       # Unchanged (no new tools)

replay_utterances.txt              # NEW at repo root: example utterances for baseline
```

## New Modules

### `todo_agent/instrumentation.py`

Owns all log I/O and cost arithmetic. No I/O side-effects at import time.

```
Functions:
  compute_cost(usage: anthropic.types.Usage) -> float
    - Reads cache_creation.ephemeral_5m_input_tokens, ephemeral_1h_input_tokens
    - Falls back to cache_creation_input_tokens aggregate if cache_creation is None
    - Uses PRICE_TABLE from config

  append_log_record(record: dict) -> None
    - Opens get_log_path() in append mode, writes json.dumps(record) + "\n"
    - Wraps entire operation in try/except Exception; prints warning to stderr on failure

  load_log_records() -> list[dict]
    - Returns [] if log file does not exist
    - Skips and counts unparseable lines; does not raise

  build_log_record(
      request_id: str,
      response: anthropic.types.Message,
      latency_ms: int,
      seconds_since_previous: float | None,
      replay: bool = False,
  ) -> dict
    - Assembles the full record dict per data-model.md Entity 1
```

### `todo_agent/cli/cost.py`

```
Functions:
  cmd_report() -> None
    - Calls instrumentation.load_log_records()
    - Groups by local date and request_id
    - Prints table per contracts/cost-cli.md

  cmd_prefix() -> None
    - Builds static system prompt (placeholder date, empty data summary)
    - Calls client.messages.count_tokens(model, system, tools, messages=[{role:user,content:"x"}])
    - Prints count and caching verdict

  cmd_replay(utterances_path: str, gap: float = 1.0, output: str = "replay_output.jsonl") -> None
    - Loads utterances (skip blanks and #-comments)
    - Builds dry_run_dispatch closure
    - Calls run_agent() per utterance with dry_run_dispatch and a replay request_id
    - Writes tool-chain JSONL output
    - Prints progress per contracts/cost-cli.md
```

### `todo_agent/config.py` additions

```python
PRICE_TABLE = {
    "input": 1.00,           # USD per million tokens
    "cache_write_5m": 1.25,
    "cache_write_1h": 2.00,
    "cache_read": 0.10,
    "output": 5.00,
    "last_verified": "2026-09-22",
}
MIN_CACHEABLE_PREFIX_TOKENS = 4096  # Haiku 4.5, last verified 2026-09-22

def get_log_path() -> Path:
    return _TODO_DIR / "api-calls.jsonl"
```

### `todo_agent/cli/agent.py` modifications

In `run_agent()`:
1. Generate `request_id = str(uuid.uuid4())` at top of function.
2. Record `prev_call_time` from the last-written log record (read once before the loop from `get_log_path()` — or pass in, to avoid repeated disk reads; read once before the loop and track in-loop).
3. In the loop, immediately before `client.messages.create()`: record `t0 = time.monotonic()`.
4. Immediately after the call: compute `latency_ms = int((time.monotonic() - t0) * 1000)`.
5. Build and append a log record via `instrumentation.append_log_record()`.

No changes to return values, parameters, or error handling of `run_agent()`.

### `todo_agent/cli/main.py` modifications

Add before the free-text LLM path:

```python
if len(sys.argv) >= 3 and sys.argv[1] == "cost":
    subcommand = sys.argv[2]
    if subcommand == "report":
        cost.cmd_report(); sys.exit(0)
    elif subcommand == "prefix":
        cost.cmd_prefix(); sys.exit(0)
    elif subcommand == "replay":
        # parse --gap and --output flags
        cost.cmd_replay(utterances_path, gap, output); sys.exit(0)
    else:
        print(f"Unknown cost subcommand: {subcommand}", file=sys.stderr); sys.exit(1)
```

## Complexity Tracking

No constitution violations — section not required.

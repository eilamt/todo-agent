# Tasks: API Cost and Token Instrumentation

**Input**: Design documents from `specs/009-api-cost-instrumentation/`

**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/cost-cli.md ✓, quickstart.md ✓

---

## Phase 1: Setup

**Purpose**: Add config constants and path helper that all other modules depend on.

- [x] T001 Add `get_log_path() -> Path` (returns `~/.todo-agent/api-calls.jsonl`), `PRICE_TABLE` dict (input=$1.00, cache_write_5m=$1.25, cache_write_1h=$2.00, cache_read=$0.10, output=$5.00 per million tokens, last_verified="2026-09-22"), and `MIN_CACHEABLE_PREFIX_TOKENS = 4096` to `todo_agent/config.py`

---

## Phase 2: Foundational — Core Instrumentation Module

**Purpose**: `todo_agent/instrumentation.py` is the single owner of log I/O and cost arithmetic — all stories depend on it.

- [x] T00 Create `todo_agent/instrumentation.py` with `compute_cost(usage) -> float`: reads `usage.cache_creation.ephemeral_5m_input_tokens` and `ephemeral_1h_input_tokens` when `usage.cache_creation` is not None; falls back to `usage.cache_creation_input_tokens or 0` (using `cache_write_5m` price for fallback); adds `(usage.input_tokens or 0) * PRICE_TABLE["input"] / 1_000_000` and `(usage.output_tokens or 0) * PRICE_TABLE["output"] / 1_000_000` and `(usage.cache_read_input_tokens or 0) * PRICE_TABLE["cache_read"] / 1_000_000`

- [x] T00 Add `build_log_record(request_id: str, response, latency_ms: int, seconds_since_previous: float | None, replay: bool = False) -> dict` to `todo_agent/instrumentation.py`: assembles full record per data-model.md Entity 1; fields: `timestamp` (UTC ISO-8601 via `datetime.utcnow().isoformat() + "Z"`), `request_id`, `model` (`response.model`), `input_tokens` (`response.usage.input_tokens or 0`), `output_tokens` (`response.usage.output_tokens or 0`), `cache_creation_5m_tokens` (from `usage.cache_creation.ephemeral_5m_input_tokens` or 0), `cache_creation_1h_tokens` (from `usage.cache_creation.ephemeral_1h_input_tokens` or 0), `cache_read_input_tokens` (`response.usage.cache_read_input_tokens or 0`), `latency_ms`, `seconds_since_previous_call`, `estimated_cost_usd` (from `compute_cost(response.usage)`); includes `"replay": True` only when `replay=True`

- [x] T00 Add `append_log_record(record: dict) -> None` to `todo_agent/instrumentation.py`: creates parent dir with `mkdir(parents=True, exist_ok=True)`; opens `get_log_path()` in append mode and writes `json.dumps(record) + "\n"`; wraps entire body in `try/except Exception as e: print(f"[instrumentation] warning: could not write log: {e}", file=sys.stderr)` — never raises

- [x] T00 Add `load_log_records() -> list[dict]` and `get_last_call_timestamp() -> datetime | None` to `todo_agent/instrumentation.py`: `load_log_records` returns `[]` if log file absent, skips unparseable lines silently, stores skipped count in a module-level variable; `get_last_call_timestamp` reads only the last non-empty line of the log file (open in rb mode, seek from end) and parses its `timestamp` field as a UTC datetime; returns `None` if file absent or last line unparseable

**Checkpoint**: `instrumentation.py` complete — all stories can now build on it.

---

## Phase 3: User Story 1 — Per-Call Cost Log (Priority: P1) 🎯

**Goal**: Every `client.messages.create()` call in the agent loop appends a record to `~/.todo-agent/api-calls.jsonl`. Failures are silent.

**Independent Test**: Run `todo "list all my lanes"` twice. Open `~/.todo-agent/api-calls.jsonl` — confirm 2+ records exist (one per API round-trip), each has correct fields, no utterance text is present, and the two user requests have different `request_id` values.

- [x] T00 [US1] Modify `todo_agent/cli/agent.py`: add `import uuid`, `import time`, `from datetime import datetime`, `from todo_agent import instrumentation`; at the top of `run_agent()` add `request_id = str(uuid.uuid4())`; call `instrumentation.get_last_call_timestamp()` once before the loop and store as `_prev_call_dt`; inside the loop before each `client.messages.create()` call add `_t0 = time.monotonic()`; immediately after the call add: compute `latency_ms = int((time.monotonic() - _t0) * 1000)`; compute `seconds_since = (datetime.utcnow() - _prev_call_dt).total_seconds() if _prev_call_dt else None`; call `instrumentation.append_log_record(instrumentation.build_log_record(request_id, response, latency_ms, seconds_since))`; update `_prev_call_dt = datetime.utcnow()`

- [x] T00 [US1] Write unit tests in `tests/unit/test_instrumentation.py` covering: (a) `compute_cost` returns correct float for standard tokens; (b) `compute_cost` uses tier-specific prices when `cache_creation` is not None; (c) `compute_cost` falls back to `cache_creation_input_tokens` at 5-min price when `cache_creation` is None; (d) `build_log_record` includes all required fields; (e) `build_log_record` omits `replay` key when `replay=False`; (f) `build_log_record` includes `"replay": True` when `replay=True`; (g) `append_log_record` creates file and writes valid JSON line; (h) `append_log_record` does not raise when directory is not writable; (i) `load_log_records` returns empty list when file absent; (j) `load_log_records` skips malformed lines; (k) `get_last_call_timestamp` returns None when file absent; (l) `get_last_call_timestamp` parses UTC timestamp from last line

**Checkpoint**: CLI agent logs every API call; failures are silent.

---

## Phase 4: User Story 2 — Summary Report (Priority: P2)

**Goal**: `todo cost report` reads the log and prints per-day and overall statistics.

**Independent Test**: Run the agent 3+ times to populate the log. Run `todo cost report`. Confirm output contains a date row, an OVERALL row, all 10 columns, and the cache-hit-potential line. Run with no log file — confirm "No API call data yet" message, exit 0.

- [x] T00 [US2] Create `todo_agent/cli/cost.py` with `cmd_report() -> None`: calls `instrumentation.load_log_records()`; if empty, prints `"No API call data yet. Use the CLI agent to start collecting data."` and returns; groups records by local date (using `datetime.fromisoformat(r["timestamp"].replace("Z","")).date()`) and by `request_id`; computes per-day and overall: request count, API call count, calls/req, sum of `input_tokens`, `output_tokens`, `cache_creation_5m_tokens + cache_creation_1h_tokens` (combined cache-write), `cache_read_input_tokens`, total `estimated_cost_usd`, mean cost per request; computes cache-hit-potential as count of records where `seconds_since_previous_call is not None and seconds_since_previous_call < 300` divided by total records; prints formatted table per `contracts/cost-cli.md` plus price-table disclaimer line

- [x] T00 [US2] Add `cost report` dispatch to `todo_agent/cli/main.py`: in the reserved-subcommand section add a block that checks `len(sys.argv) >= 3 and sys.argv[1] == "cost"`; import `from todo_agent.cli import cost as cost_cmds`; route `sys.argv[2] == "report"` → `cost_cmds.cmd_report(); sys.exit(0)`; route unknown subcommands → `print(f"Unknown cost subcommand: {sys.argv[2]}", file=sys.stderr); sys.exit(1)`

**Checkpoint**: `todo cost report` works end-to-end.

---

## Phase 5: User Story 3 — Prefix Size Measurement (Priority: P3)

**Goal**: `todo cost prefix` calls the token-counting endpoint and reports count + caching eligibility.

**Independent Test**: Run `todo cost prefix`. Confirm output contains "Static prefix tokens: N", the MIN_CACHEABLE_PREFIX_TOKENS value (4096), and a MEETS/does NOT meet verdict. Exit code 0.

- [x] T01 [US3] Add `cmd_prefix() -> None` to `todo_agent/cli/cost.py`: builds static system prompt using `_build_data_summary({})` and today's placeholder date; calls `client.messages.count_tokens(model=config["model"], system=system_prompt, tools=TOOLS, messages=[{"role": "user", "content": "x"}])`; prints "Static prefix tokens: N", "Minimum cacheable length (Haiku 4.5): MIN_CACHEABLE_PREFIX_TOKENS tokens", and verdict line; on `anthropic.APIError` prints error and calls `sys.exit(1)`; needs `from todo_agent.config import load_config, MIN_CACHEABLE_PREFIX_TOKENS`, `from todo_agent.tools import TOOLS`, `from todo_agent.cli.agent import _build_data_summary`

- [x] T01 [US3] Add `cost prefix` dispatch to `todo_agent/cli/main.py`: extend the `cost` subcommand block to route `sys.argv[2] == "prefix"` → `cost_cmds.cmd_prefix(); sys.exit(0)`

**Checkpoint**: `todo cost prefix` reports token count and caching verdict.

---

## Phase 6: User Story 4 — Replay Harness (Priority: P4)

**Goal**: `todo cost replay <file>` sends utterances through the agent in dry-run mode, writes tool chains, and tags log records as replay.

**Independent Test**: Create a 3-utterance file including one write op. Run `todo cost replay <file> --gap 0`. Confirm: data file unchanged; output JSONL has 3 lines with `dry_run: true` on write tools; log gained records with `"replay": true`.

- [x] T01 [US4] Add `cmd_replay(utterances_path: str, gap: float = 1.0, output: str = "replay_output.jsonl") -> None` to `todo_agent/cli/cost.py`: loads utterances file (skip blanks and `#`-prefixed lines); exits cleanly if 0 utterances; builds `_DRY_RUN_WRITE_TOOLS` set containing all write-side-effect tool names per contracts/cost-cli.md; builds `dry_run_dispatch(tool_name, tool_input)` closure: if tool_name in `_DRY_RUN_WRITE_TOOLS` records call in `_tool_chain` list with `dry_run=True` and returns `f"[DRY RUN] would call {tool_name} with args: {json.dumps(tool_input)}"`, else records with `dry_run=False` and calls real `_dispatch(tool_name, tool_input)`; for each utterance: generate `request_id`, run `run_agent(utterance, data, config, dry_run_dispatch)` with a `replay=True` flag threaded through to `append_log_record` calls (requires adding optional `replay: bool = False` param to the `run_agent` call chain — pass it into `build_log_record`); write utterance tool-chain record to output JSONL; print progress per contracts/cost-cli.md; sleep `gap` seconds between utterances; print summary at end

- [x] T01 [US4] Thread `replay: bool = False` through `run_agent()` in `todo_agent/cli/agent.py`: add `replay: bool = False` keyword argument to `run_agent()` signature; pass it to `instrumentation.build_log_record(..., replay=replay)` in the instrumentation call added in T006

- [x] T01 [US4] Add `cost replay` dispatch to `todo_agent/cli/main.py`: extend the `cost` subcommand block to route `sys.argv[2] == "replay"`; parse `sys.argv[3]` as `utterances_path` (error if missing); parse optional `--gap SECONDS` (default 1.0) and `--output FILE` (default `"replay_output.jsonl"`) flags; call `cost_cmds.cmd_replay(utterances_path, gap, output); sys.exit(0)`

- [x] T01 [US4] Create `replay_utterances.txt` at repository root with 25 realistic utterances covering: listing lanes/projects/items, adding inbox notes, listing inbox notes, getting inbox notes, adding items (write — dry-run), setting item status (write — dry-run), setting flags (write — dry-run), adding a project (write — dry-run), moving items (write — dry-run); include `#`-prefixed section comments and blank lines to verify they are skipped

**Checkpoint**: Full replay harness works; dry-run confirmed; log tagged correctly.

---

## Phase 7: Polish & Validation

- [x] T01 Write unit tests in `tests/unit/test_cost_report.py` covering: (a) `cmd_report` prints "no data" message when log is empty; (b) report groups records by local date correctly; (c) per-day request count equals number of distinct `request_id` values; (d) cache-hit-potential counts only records with `seconds_since_previous_call < 300`; (e) OVERALL row sums all days

- [x] T01 Run full test suite `pytest -v` — all pre-existing tests plus new instrumentation and report tests must pass

- [x] T01 Manual validation of quickstart.md scenarios S1, S4 (silent failure), S5, S6, S7, S8 (no data change after replay), S9 (stable diff)

---

## Dependencies

- T001 must complete before T002–T005 (config constants needed by instrumentation)
- T002 must complete before T003 (compute_cost needed by build_log_record)
- T003 must complete before T004 (build_log_record needed by append_log_record)
- T004–T005 depend on T002–T003; can run in sequence
- T006 depends on T001–T005 (agent.py calls instrumentation)
- T007 depends on T001–T005 (tests the instrumentation module)
- T008 depends on T001–T005 (cmd_report calls instrumentation)
- T009 depends on T008 (dispatch routes to cmd_report)
- T010 depends on T008 (same file as cmd_report)
- T011 depends on T009, T010 (extends cost dispatch)
- T012 depends on T006, T008 (replay uses run_agent and _dispatch)
- T013 depends on T006 (adds replay param to run_agent)
- T014 depends on T012, T013 (dispatch routes to cmd_replay)
- T015 can be written alongside T012 (different file)
- T016 depends on T008 (tests cmd_report)
- T017 depends on all implementation tasks
- T018 depends on T017

## Parallel Opportunities

- T006 and T007 can be written together (different files: agent.py vs test file)
- T012 and T015 can run in parallel (different files: cost.py vs replay_utterances.txt)
- T016 can be written alongside T008 (different files: test file vs cost.py)

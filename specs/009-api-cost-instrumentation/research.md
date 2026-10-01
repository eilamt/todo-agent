# Research: API Cost and Token Instrumentation

## Decision 1: Instrumentation Insertion Point

**Decision**: Wrap `client.messages.create()` inside `run_agent()` in `todo_agent/cli/agent.py`. Record a `start_time` just before the call, a `end_time` just after, and read `response.usage` from the returned object.

**Rationale**: `agent.py` is already the sole Anthropic SDK caller (constitution Principle III). Adding timing and usage capture here requires zero changes to any other module and zero new abstractions. The `dispatch_fn` and all core operations remain untouched.

**Alternatives considered**:
- SDK-level middleware (monkey-patching `httpx`): fragile, couples to transport internals.
- Wrapping the entire `run_agent()` call at the CLI layer: cannot capture per-round-trip data.

---

## Decision 2: SDK Usage Fields for Cache Costs

**Decision**: Use `response.usage.cache_creation` (a `CacheCreation` object) when available, with `.ephemeral_5m_input_tokens` and `.ephemeral_1h_input_tokens` as separate fields. Fall back to the aggregate `cache_creation_input_tokens` (int, or 0 if None) when `cache_creation` is None.

**Rationale**: The Anthropic Python SDK (`anthropic` ≥ latest) exposes `usage.cache_creation` as a `CacheCreation` model with two fields that distinguish cache tiers. This allows applying the correct per-tier price ($1.25/M vs $2.00/M). The aggregate `cache_creation_input_tokens` field remains available as a backward-compatible fallback.

**Verification**: Confirmed by inspecting SDK source:
```python
class CacheCreation(BaseModel):
    ephemeral_1h_input_tokens: int  # 1-hour cache write tokens
    ephemeral_5m_input_tokens: int  # 5-minute cache write tokens
```

**Alternatives considered**:
- Use only aggregate `cache_creation_input_tokens` and apply one price: loses tier-level precision.

---

## Decision 3: Log File Format and Path

**Decision**: Append-only JSON Lines (`~/.todo-agent/api-calls.jsonl`). Path returned by a new `get_log_path() -> Path` function in `todo_agent/config.py`.

**Rationale**: JSONL is human-readable (constitution Principle V), requires no schema migrations, streams efficiently for large files, and is trivially parseable by stdlib `json`. Placing the path in `config.py` keeps configuration centrally managed (Principle II).

**Alternatives considered**:
- SQLite: violates Principle IV (database engine without documented bottleneck).
- CSV: insufficient for nested/optional fields.

---

## Decision 4: `request_id` Propagation

**Decision**: Generate a UUID4 at the top of `run_agent()` and pass it as a parameter to the logging call on each round-trip. The `request_id` groups all API calls from a single user CLI invocation.

**Rationale**: A single user request may trigger up to `MAX_ROUNDS=10` round-trips. The `request_id` is the only way to compute per-request cost in the summary. Generating it inside `run_agent()` requires no signature changes to callers.

---

## Decision 5: Price Table Storage

**Decision**: Define a `PRICE_TABLE` dict constant in `todo_agent/config.py` alongside a `PRICE_TABLE_LAST_VERIFIED` date string and `MIN_CACHEABLE_PREFIX_TOKENS = 4096`. The summary and cost functions import from there.

**Rationale**: A single location to update when Anthropic changes prices (Principle II). The `last_verified` date makes staleness visible. Putting it in `config.py` alongside other static defaults avoids a new module.

**Current prices (Haiku 4.5, last verified 2026-09-22, USD per million tokens)**:
- input: $1.00
- cache_write_5m: $1.25
- cache_write_1h: $2.00
- cache_read: $0.10
- output: $5.00

---

## Decision 6: Token-Counting Endpoint

**Decision**: Use `client.messages.count_tokens(model=..., system=..., tools=..., messages=[{"role": "user", "content": "x"}])`. The static prefix is: the system prompt string (with a placeholder for today's date and an empty data summary) plus the full `TOOLS` list.

**Rationale**: `client.messages.count_tokens()` is a documented non-destructive endpoint that returns `MessageTokensCount` with an `input_tokens` field. No tokens are consumed. The system prompt must include a minimal user message for the count to be valid.

**Verification**: SDK exposes `client.messages.count_tokens` (confirmed via `dir(client.messages)`). The `MessageTokensCount` result has `.input_tokens` (int).

**Minimum cacheable prefix for Haiku 4.5**: 4,096 tokens (per Anthropic documentation; stored in `config.py` as `MIN_CACHEABLE_PREFIX_TOKENS`).

---

## Decision 7: Instrumentation Module

**Decision**: Create `todo_agent/instrumentation.py` as the single owner of all log I/O and cost arithmetic. Functions: `compute_cost(usage) -> float`, `append_log_record(record: dict) -> None` (silent on failure), `load_log_records() -> list[dict]`.

**Rationale**: Keeps `agent.py` focused on conversation logic. Centralises cost math for unit-testability without Anthropic API calls.

---

## Decision 8: `cost` CLI Subcommand

**Decision**: Add a new reserved subcommand prefix `cost` to `todo_agent/cli/main.py`. Implement handlers in a new `todo_agent/cli/cost.py` module: `cmd_report()`, `cmd_prefix()`, `cmd_replay(utterances_path, gap_seconds, output_path)`.

**Routing logic** (in `main.py`):
```
todo cost report         → cost.cmd_report()
todo cost prefix         → cost.cmd_prefix()
todo cost replay <file>  → cost.cmd_replay(file, ...)
```

**Rationale**: Consistent with the existing reserved-subcommand pattern (`visualize`). Separate module keeps `main.py` clean.

---

## Decision 9: Dry-Run / Replay Mode

**Decision**: In `cmd_replay()`, build a `dry_run_dispatch` closure that wraps the real `_dispatch` function. For any tool whose name ends with a write-side effect pattern (tools not in a read-only allowlist), the closure returns a "would call: {tool_name}({args})" string without executing the tool. The closure is passed as `dispatch_fn` to `run_agent()`.

**Write-operation allowlist approach**: Explicitly enumerate the read-only tools (`list_*`, `get_*`, `request_clarification`, `visualize_*`) and intercept everything else.

**Rationale**: Cleanest intercept point; no changes needed to `run_agent()`, `_dispatch()`, or any core operation. The closure is entirely self-contained in `cost.py`.

---

## Decision 10: Instrumentation Failure Handling

**Decision**: Wrap the `append_log_record()` call in a broad `except Exception` block that prints a warning to `stderr` and returns `None`. The agent call is unaffected.

**Rationale**: FR-005 requires that logging failures never break the agent. The `try/except` pattern is the minimal mechanism.

---

## Decision 11: No New External Dependencies

**Decision**: All new code uses only Python stdlib (`json`, `uuid`, `time`, `datetime`, `pathlib`, `sys`) and the already-present `anthropic` SDK.

**Rationale**: Principle IV prohibits new dependencies without documented concrete need. The stdlib is sufficient for JSONL I/O, UUID generation, timing, and date arithmetic.

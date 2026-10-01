# Research: Reduce API Cost — Lazy Context and Prompt Caching

## Decision 1: Compact Index Format

**Decision**: Replace `_build_data_summary()` with `_build_compact_index(data)` that outputs lane names, project names, and item counts only. Inbox note count is appended as a single line.

**Measured result**:
- Current full summary: **1,021 tokens** (3,161 chars) for the live board (32 items)
- Compact index: **378 tokens** (609 chars) for the same board — a **63% reduction** in the dynamic context alone
- New total per call: ~4,342 (static prefix) + 378 (compact index) = **~4,720 tokens** vs **14,777 previously** — a **68% total reduction**

**Format**:
```
Lane: <lane-name>
  Project: <project-name> (<N> items)
  Project: <project-name> (<N> items)
Lane: <lane-name>
  Project: <project-name> (<N> items)
...
Inbox: <N> note(s)
```

**Rationale**: The agent's existing `list_items` tool already returns `today`, `this_week`, `this_weekend`, `deadline`, `status`, `importance`, and `description` per item. Its description explicitly says "Use this to answer questions like 'what items are due today?'". No new tools are required; the agent fetches detail on demand exactly as the tool descriptions instruct.

**Alternatives considered**:
- Send no board context at all: risky — the agent has no starting point for write operations and may hallucinate lane/project names.
- Send top-level lane list only (no projects): agent cannot tell which lane to use for an add operation without a follow-up read call; adds latency for common writes.
- Send project names with status but no item counts: item count is useful context for the agent ("this project has 0 items" is meaningful) and costs negligible tokens.

---

## Decision 2: System Prompt Block Structure for Caching

**Decision**: Restructure the `system` parameter in `client.messages.create()` from a plain string to a list of two `TextBlockParam` dicts:

```python
system=[
    {
        "type": "text",
        "text": STATIC_INSTRUCTIONS,        # date + role + tool-use rules + inbox workflow
        "cache_control": {"type": "ephemeral"},
    },
    {
        "type": "text",
        "text": _build_compact_index(data),  # dynamic, no cache_control
    },
]
```

**SDK verification**: `anthropic.types.TextBlockParam` has an optional `cache_control` field (confirmed via `__annotations__`). The `system` parameter of `client.messages.create()` accepts `Union[str, Iterable[TextBlockParam]]`.

**Cache boundary**: The `cache_control` on the first block tells the platform to cache everything up to and including that block — which includes the tool definitions (passed via `tools=TOOLS`) plus the static instructions. The second block (compact index) is always re-sent fresh, so the agent always sees current board state.

**Cache duration**: 5-minute ephemeral (`{"type": "ephemeral"}`). With the user's typical session cadence (multiple requests within a few minutes), this will produce cache hits for follow-on requests.

**Date in static block**: The date (`date.today().isoformat()`) is included in the static block. Since the 5-minute cache always expires and refreshes, the cached date will never be stale by more than 5 minutes — acceptable for a to-do agent.

**Alternatives considered**:
- Cache the tools list only (add `cache_control` to the last tool in `TOOLS`): would also cache the static prefix, but requires modifying `tools.py` which is a shared schema file. Keeping the change inside `agent.py` is cleaner.
- Cache both tools and system prompt separately: unnecessarily complex; one cache boundary covering both achieves the same result.
- 1-hour cache (`ephemeral_1h`): higher write cost ($2.00/M vs $1.25/M), only saves money if there are many requests per hour. The 5-minute tier is lower risk and lower write cost for this usage pattern.

---

## Decision 3: No New Tools Required

**Decision**: No changes to `todo_agent/tools.py` or `todo_agent/core/operations.py`.

**Rationale**: The existing `list_items` tool returns all flag fields (`today`, `this_week`, `this_weekend`, `deadline`) per item. The agent's LLM already knows to call it for flag-based queries (per tool description). The compact index provides enough context for write operations (lane + project names visible). Read-on-demand is already the intended pattern per the tool descriptions.

---

## Decision 4: Regression Testing Approach

**Decision**: Run the replay harness (`todo cost replay replay_utterances.txt`) before and after the change and diff the tool-chain output files. Accept the change if:
- All write-operation utterances produce the same tool name and arguments as before.
- Read-operation utterances may produce additional `list_items` / `list_projects` calls — this is expected and acceptable.
- The agent never returns "not found" or an empty result for a query that previously returned data.

**Rationale**: The spec explicitly permits additional read-tool calls. The diff only needs to confirm that the terminal write actions are unchanged; intermediate read steps may be added.

---

## Decision 5: Test Suite Compatibility

**Decision**: Update `tests/unit/test_agent.py` to pass `system` as a list of blocks (not a string) when patching `client.messages.create`. The existing tests mock the Anthropic client, so they need to handle the new `system` format in their mock setup — but the mock doesn't validate `system` content, so the change is minimal.

**Rationale**: The test mocks intercept `client.messages.create()` entirely and return pre-canned responses. The `system` parameter format change doesn't affect mock behavior. Tests only need updating if they assert on the `system` value passed; a quick grep will confirm.

---

## Token Reduction Summary

| Component | Before | After | Reduction |
|-----------|--------|-------|-----------|
| Static prefix (tools + instructions) | ~13,756 tokens | ~4,342 tokens (cached after first call) | 68% (cost: $0.10/M cache read vs $1.00/M input) |
| Dynamic data summary | ~1,021 tokens | ~378 tokens | 63% |
| **Total per call** | **~14,777** | **~4,720** (or ~4,342 cached + 378 fresh) | **68%** |

After caching kicks in, the effective cost per call drops further because the 4,342 static tokens are served at $0.10/M (cache read) rather than $1.00/M (input).

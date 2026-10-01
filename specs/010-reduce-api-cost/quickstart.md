# Quickstart: Reduce API Cost — Lazy Context and Prompt Caching

Validation scenarios for feature 010. Run these after implementation is complete.

**Prerequisites**:
- `ANTHROPIC_API_KEY` set
- At least one lane, one project, and several items in the data store
- `~/.todo-agent/api-calls.jsonl` exists (or will be created on first call)

---

## S1 — Token count drops by at least 50%

**Goal**: Confirm the compact index reduces total input tokens significantly.

```bash
# Note current baseline from earlier log entries
todo cost report

# Make a request after the change
todo "show me what's due today"

# Check the new token count
todo cost report
```

**Expected outcome**: The new log entry shows input tokens ≤ 7,000 (vs ~14,777 before). The response correctly lists today-flagged items.

---

## S2 — Compact index does not contain item titles

**Goal**: Confirm the full item dump is gone from the system prompt.

```bash
# Trigger a request and check what the agent received
todo "list all my lanes"
cat ~/.todo-agent/api-calls.jsonl | tail -1 | python3 -m json.tool
```

**Expected outcome**: `input_tokens` is well below 5,000. The agent's response correctly lists lanes — confirming it used its read tools, not pre-loaded data.

---

## S3 — Agent still answers flag queries correctly

**Goal**: Confirm lazy fetching doesn't break flag-based queries.

```bash
todo "show me what's due today"
todo "what's on my list for this week"
todo "show me this weekend items"
```

**Expected outcome**: All three return correct, non-empty results matching the actual flag state in the data store. The agent may make one extra API round-trip (calling `list_items`) — that's expected.

---

## S4 — Agent still handles write operations correctly

**Goal**: Confirm the agent can add/update items using only the compact index as context.

```bash
todo "add a task called test lazy context to the apps lane yoga project"
todo "mark test lazy context as completed"
todo "delete test lazy context"
```

**Expected outcome**: Each operation succeeds. The agent correctly identifies the lane and project from the compact index without needing item-level detail upfront.

---

## S5 — Cache hits appear in cost log

**Goal**: Confirm prompt caching is active and producing cache reads.

```bash
# First request — creates the cache
todo "list all my lanes"

# Second request within 60 seconds — should hit cache
todo "show me my inbox"

# Check for cache hits
todo cost report
```

**Expected outcome**: The report shows non-zero `Cache-Read Tok` for today. The second request's estimated cost is lower than the first for equivalent input.

---

## S6 — Cache hit potential improves

**Goal**: Confirm the summary metric reflects the caching benefit.

```bash
# Run 3-4 requests within 5 minutes
todo "list all my lanes"
todo "show me what's due today"
todo "what's in my inbox"
todo "show me this week"

todo cost report
```

**Expected outcome**: Cache hit potential shows ≥ 50% of API calls arriving within 5 minutes (the first call creates the cache; subsequent calls within 5 minutes hit it).

---

## S7 — Replay harness behavioral equivalence

**Goal**: Confirm tool chains are functionally equivalent before and after the change.

```bash
# Run replay after the change
todo cost replay replay_utterances.txt --gap 0 --output replay_after.jsonl

# Compare write-operation tool chains with the pre-change baseline
# (strip request_id and timestamps before diffing)
python3 - << 'EOF'
import json

def normalize(path):
    results = []
    for line in open(path):
        r = json.loads(line)
        # Keep only write tool calls for comparison
        write_calls = [tc for tc in r.get("tool_calls", []) if tc["dry_run"]]
        results.append({"utterance": r["utterance"], "write_calls": write_calls})
    return results

before = normalize("replay_output.jsonl")   # pre-change baseline
after  = normalize("replay_after.jsonl")

mismatches = []
for b, a in zip(before, after):
    if b["write_calls"] != a["write_calls"]:
        mismatches.append({"utterance": b["utterance"], "before": b["write_calls"], "after": a["write_calls"]})

if mismatches:
    print(f"FAIL: {len(mismatches)} mismatch(es)")
    for m in mismatches:
        print(m)
else:
    print(f"PASS: all {len(before)} write-operation tool chains are identical")
EOF
```

**Expected outcome**: "PASS: all N write-operation tool chains are identical". Read-only utterances may show additional `list_items` calls in the after file — that is acceptable and expected.

---

## S8 — All existing tests still pass

```bash
python3 -m pytest -v
```

**Expected outcome**: 213 passed, 0 failed.

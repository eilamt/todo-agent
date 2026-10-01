# Quickstart: API Cost and Token Instrumentation

Validation scenarios for feature 009. Run these after implementation is complete.

**Prerequisites**:
- `ANTHROPIC_API_KEY` set in environment
- `todo-agent` installed / running from repo root (`python -m todo_agent.cli.main`)
- `~/.todo-agent/` directory exists (created automatically on first run)

---

## S1 — Normal use generates a log

**Goal**: Confirm every CLI agent call appends records to the JSONL log.

```bash
# Run two CLI requests
todo "list all my lanes"
todo "add an inbox note about refactoring the login page"

# Inspect the log
cat ~/.todo-agent/api-calls.jsonl | python3 -m json.tool --no-ensure-ascii
```

**Expected outcome**:
- File `~/.todo-agent/api-calls.jsonl` exists and contains two or more JSON objects (one per API round-trip).
- Each object has `timestamp`, `request_id`, `model`, `input_tokens`, `output_tokens`, `latency_ms`, `estimated_cost_usd`.
- Both requests from `todo "list all my lanes"` share the same `request_id`; both from the second request share a different `request_id`.
- No utterance text appears in any log record.

---

## S2 — Log persists across multiple runs

**Goal**: Confirm the log is append-only and does not truncate.

```bash
COUNT_BEFORE=$(wc -l < ~/.todo-agent/api-calls.jsonl)
todo "show me today's items"
COUNT_AFTER=$(wc -l < ~/.todo-agent/api-calls.jsonl)
echo "Added $((COUNT_AFTER - COUNT_BEFORE)) record(s)"
```

**Expected outcome**: Count increases by at least 1.

---

## S3 — `seconds_since_previous_call` is populated

**Goal**: Confirm inter-call timing is recorded.

```bash
todo "list all my lanes"
sleep 10
todo "list inbox notes"
tail -1 ~/.todo-agent/api-calls.jsonl | python3 -c "import sys,json; r=json.load(sys.stdin); print('Gap:', r['seconds_since_previous_call'])"
```

**Expected outcome**: Printed gap is approximately 10 seconds (±2 s).

---

## S4 — Instrumentation failure is silent

**Goal**: Confirm the agent runs normally even if the log cannot be written.

```bash
# Make the log file unwritable
touch ~/.todo-agent/api-calls.jsonl
chmod 000 ~/.todo-agent/api-calls.jsonl

todo "list all my lanes"

# Restore
chmod 644 ~/.todo-agent/api-calls.jsonl
```

**Expected outcome**:
- Agent produces its normal output.
- A warning line appears on stderr (not stdout) mentioning the log write failure.
- The agent does not raise an exception or exit non-zero.

---

## S5 — `todo cost report` shows per-day stats

**Goal**: Confirm the summary command reads the log and prints useful output.

```bash
# Run a few requests to populate the log
todo "list all lanes"
todo "add an inbox note about testing"
todo "list inbox notes"

todo cost report
```

**Expected outcome**:
- Output contains a table with at least one date row and an OVERALL row.
- Columns: Requests, API Calls, Calls/Req, token counts by type, Total Cost, Mean/Req.
- "Cache hit potential" line shows a percentage.

---

## S6 — `todo cost report` handles missing log gracefully

```bash
mv ~/.todo-agent/api-calls.jsonl ~/.todo-agent/api-calls.jsonl.bak 2>/dev/null || true
todo cost report
mv ~/.todo-agent/api-calls.jsonl.bak ~/.todo-agent/api-calls.jsonl 2>/dev/null || true
```

**Expected outcome**: Prints "No API call data yet" message; exits with code 0; no traceback.

---

## S7 — `todo cost prefix` reports token count and caching verdict

```bash
todo cost prefix
```

**Expected outcome**:
- Prints "Static prefix tokens: N" where N is a positive integer.
- Prints the minimum cacheable length (4,096 for Haiku 4.5).
- Prints either "Prefix MEETS the minimum" or "Prefix does NOT meet the minimum".
- Exits with code 0.

---

## S8 — `todo cost replay` runs without modifying data

**Goal**: Confirm replay mode does not touch the real data file.

```bash
# Capture current data file checksum
BEFORE=$(md5 -q ~/.todo-agent/todos.json 2>/dev/null || md5sum ~/.todo-agent/todos.json | cut -d' ' -f1)

# Create a small utterances file
cat > /tmp/test_utterances.txt << 'EOF'
list all my lanes
add a project called Replay Test to the Work lane
add a task called dry run item to Replay Test
EOF

todo cost replay /tmp/test_utterances.txt --gap 0 --output /tmp/replay_out.jsonl

AFTER=$(md5 -q ~/.todo-agent/todos.json 2>/dev/null || md5sum ~/.todo-agent/todos.json | cut -d' ' -f1)
echo "Data file changed: $([ "$BEFORE" = "$AFTER" ] && echo NO || echo YES)"
```

**Expected outcome**:
- "Data file changed: NO"
- `/tmp/replay_out.jsonl` contains 3 lines (one per utterance).
- The second and third lines have `"dry_run": true` for the write tool calls.
- Log records tagged `"replay": true` appear in `~/.todo-agent/api-calls.jsonl`.

---

## S9 — Replay output is stable across two runs

**Goal**: Confirm behavioral regression detection via diff.

```bash
todo cost replay /tmp/test_utterances.txt --gap 0 --output /tmp/replay_run1.jsonl
todo cost replay /tmp/test_utterances.txt --gap 0 --output /tmp/replay_run2.jsonl

# Strip timestamps and costs before diffing
python3 -c "
import json, sys
for line in open(sys.argv[1]):
    r = json.loads(line)
    r.pop('request_id', None)
    print(json.dumps(r, sort_keys=True))
" /tmp/replay_run1.jsonl > /tmp/r1_stripped.jsonl

python3 -c "
import json, sys
for line in open(sys.argv[1]):
    r = json.loads(line)
    r.pop('request_id', None)
    print(json.dumps(r, sort_keys=True))
" /tmp/replay_run2.jsonl > /tmp/r2_stripped.jsonl

diff /tmp/r1_stripped.jsonl /tmp/r2_stripped.jsonl && echo "No behavioral diff" || echo "Behavioral change detected"
```

**Expected outcome**: "No behavioral diff" (tool chains are identical between runs).

---

## S10 — Replay with comment lines and blanks

```bash
cat > /tmp/comments_utterances.txt << 'EOF'
# This is a comment
list all my lanes

# Another comment
list inbox notes
EOF

todo cost replay /tmp/comments_utterances.txt --gap 0 --output /tmp/comments_out.jsonl
wc -l /tmp/comments_out.jsonl
```

**Expected outcome**: Output file has exactly 2 lines (comments and blanks skipped).

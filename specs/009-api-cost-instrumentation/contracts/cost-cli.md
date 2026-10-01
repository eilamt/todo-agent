# Contract: `todo cost` CLI Subcommands

These are the three new CLI commands exposed under the `cost` subcommand prefix.

---

## `todo cost report`

**Description**: Reads the API call log and prints per-day and overall usage statistics.

**Invocation**:
```
todo cost report
```

**Output format** (plain text, human-readable):

```
API Cost Report
===============

Date          Requests  API Calls  Calls/Req  Input Tok  Output Tok  Cache-Write Tok  Cache-Read Tok  Total Cost    Mean/Req
2026-09-22    4         9          2.25       18,432     864         0                0               $0.0236       $0.0059
2026-09-23    2         3          1.50       7,120      312         4,096            512             $0.0081       $0.0041

OVERALL       6         12         2.00       25,552     1,176       4,096            512             $0.0317       $0.0053

Cache hit potential: 5 of 12 API calls (41.7%) arrived within 5 minutes of the previous call.
Price table last verified: 2026-09-22. Verify current prices at console.anthropic.com.
```

**Behaviour**:
- If no log file exists: print `No API call data yet. Use the CLI agent to start collecting data.` and exit 0.
- If log file exists but all lines are unparseable: print count of skipped lines and `No valid records found.`
- Skip unparseable lines silently; print a count at the end: `(N lines skipped — unreadable)`.
- Dates are local calendar dates (uses local timezone for grouping).

---

## `todo cost prefix`

**Description**: Counts the tokens in the agent's static prefix (tool schemas + system prompt) using the Anthropic token-counting endpoint, and reports whether it meets the minimum cacheable length.

**Invocation**:
```
todo cost prefix
```

**Output format**:

```
Agent Prefix Token Count
========================
Static prefix tokens: 5,842
Minimum cacheable length (Haiku 4.5): 4,096 tokens
Result: Prefix MEETS the minimum — prompt caching is viable.
```

Or, if below minimum:

```
Static prefix tokens: 2,103
Minimum cacheable length (Haiku 4.5): 4,096 tokens
Result: Prefix does NOT meet the minimum — caching would have no effect.
```

**Behaviour**:
- Calls `client.messages.count_tokens()` with the static prefix only (tools + system prompt skeleton with placeholder date and empty data summary).
- Uses the configured model from `config.json`.
- On API error: print the error message and exit with code 1.
- No tokens are billed for this call.

---

## `todo cost replay <utterances_file> [--gap SECONDS] [--output OUTPUT_FILE]`

**Description**: Sends each utterance in the file through the agent in dry-run mode, records the tool chains, and logs the API calls tagged as replay.

**Invocation**:
```
todo cost replay replay_utterances.txt
todo cost replay replay_utterances.txt --gap 2 --output tool_chains.jsonl
```

**Arguments**:

| Argument | Default | Description |
|----------|---------|-------------|
| `utterances_file` | (required) | Path to plain-text file, one utterance per line |
| `--gap SECONDS` | `1` | Seconds to wait between utterances |
| `--output FILE` | `replay_output.jsonl` (in current dir) | Where to write the tool-chain JSONL |

**Output during run** (to stdout):

```
Replay: 8 utterances loaded from replay_utterances.txt
[1/8] add an inbox note about redesigning the login flow
      → add_inbox_note (dry-run) | 2 API calls | $0.0009
[2/8] list inbox notes
      → list_inbox_notes (executed) | 1 API call | $0.0004
...
Replay complete. Tool chains written to replay_output.jsonl.
Total: 8 utterances | 14 API calls | $0.0087 estimated
```

**Dry-run behaviour**:
- **Write tools** (intercepted, not executed): `add_lane`, `add_project`, `add_item`, `set_item_status`, `set_item_flag`, `set_item_deadline`, `set_item_description`, `set_item_importance`, `set_project_status`, `set_project_importance`, `set_project_note`, `delete_lane`, `delete_project`, `delete_item`, `move_item`, `reorder_lanes`, `reorder_projects`, `add_inbox_note`, `mark_note_promoted`
- **Read tools** (executed normally): `list_lanes`, `list_projects`, `get_project`, `list_items`, `list_inbox_notes`, `get_inbox_note`, `request_clarification`, `visualize_board`, `visualize_project`
- Write tool interception returns the string `"[DRY RUN] would call {tool_name} with args: {json_args}"` to the LLM.

**Behaviour**:
- Reads the real data file (read-only) for context; no writes.
- Skips blank lines and `#`-prefixed comments in the utterances file.
- If `utterances_file` does not exist: print error and exit 1.
- If `utterances_file` is empty (no valid utterances): print `No utterances to replay.` and exit 0.
- On API error for a single utterance: record the error in the output file and continue to the next utterance.
- The `replay: true` field is present on all log records generated during replay.

**Tool chain output file** (JSONL, one object per utterance):
```json
{"utterance": "...", "request_id": "...", "tool_calls": [{"name": "...", "input": {...}, "dry_run": true}]}
```

See `data-model.md` → Entity 3 for full schema.

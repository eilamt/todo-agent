# Tasks: Reduce API Cost — Lazy Context and Prompt Caching

**Input**: Design documents from `specs/010-reduce-api-cost/`

**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, quickstart.md ✓

---

## Phase 1: Setup

**Purpose**: Capture a pre-change replay baseline so behavioral regression can be detected after implementation.

- [x] T001 Capture pre-change tool-chain baseline by running `python3 -m todo_agent.cli.main cost replay replay_utterances.txt --gap 0 --output replay_before.jsonl` from the repo root; verify `replay_before.jsonl` exists and contains one JSON line per non-blank, non-comment utterance in `replay_utterances.txt`

---

## Phase 2: Foundational

No foundational blocking prerequisites — both user stories modify the same single file (`todo_agent/cli/agent.py`) and can proceed directly.

---

## Phase 3: User Story 1 — Lazy Board Summary (Priority: P1) 🎯

**Goal**: Replace the full item dump in the system prompt with a compact lane/project/count index. Agent fetches item detail on demand via existing read tools.

**Independent Test**: Run `todo "show me what's due today"` and check `~/.todo-agent/api-calls.jsonl` — the latest record must show `input_tokens` ≤ 7,000 (down from ~14,777). The response must still correctly list today-flagged items.

- [x] T002 [US1] In `todo_agent/cli/agent.py`, add `_build_compact_index(data: dict) -> str` immediately after the existing `_build_data_summary` function: iterate `data.get("lanes", [])`, emit `Lane: {lane["name"]}` then for each project emit `  Project: {project["name"]} ({len(project.get("items", []))} items)`; after all lanes, if `get_inbox_dir().glob("*.md")` yields any files append `Inbox: {N} note(s)`; return `"(empty board)"` if no lanes exist; add `from todo_agent.config import get_inbox_dir` import if not already present

- [x] T003 [US1] In `todo_agent/cli/agent.py`, update `run_agent()` to build the system prompt using `_build_compact_index(data)` instead of `_build_data_summary(data)`; replace the existing single `system_prompt` string with two separate variables: `_static` (containing role description, today's date, tool-use instructions, preference for clarification, explicit read-tool guidance sentence: "The board index below shows lanes, projects, and item counts only. Call list_items, get_item, list_inbox_notes, or get_inbox_note to fetch item-level detail — titles, statuses, flags, deadlines, descriptions — when needed to fulfill the request.", and the inbox promotion workflow) and `_dynamic` (containing `f"Current board:\n{_build_compact_index(data)}"`)

**Checkpoint**: Agent uses compact index. Input tokens per call should be ≤ 5,000. Flag queries still work correctly (agent calls `list_items` on demand).

---

## Phase 4: User Story 2 — Prompt Caching on Static Context (Priority: P2)

**Goal**: Mark the static instructions block for 5-minute platform caching so follow-on requests within the same session pay cache-read price (~10× cheaper) for the static portion.

**Independent Test**: Make two CLI requests within 60 seconds. Check `~/.todo-agent/api-calls.jsonl` — the second request's record must show `cache_read_input_tokens > 0`.

- [x] T004 [US2] In `todo_agent/cli/agent.py`, change the `system` argument in the `client.messages.create()` call from the single `system_prompt` string to a list of two dicts: `[{"type": "text", "text": _static, "cache_control": {"type": "ephemeral"}}, {"type": "text", "text": _dynamic}]`; remove the now-unused `system_prompt` variable; ensure `_static` and `_dynamic` are built before the loop (compact index is computed once per `run_agent()` call, not per round-trip)

**Checkpoint**: Two rapid CLI requests produce a log record with `cache_read_input_tokens > 0` on the second call.

---

## Phase 5: Polish & Validation

- [x] T005 Run `python3 -m pytest -v` — all 213 pre-existing tests must pass with zero failures

- [x] T006 [P] Validate quickstart scenario S1: run `todo "show me what's due today"`, inspect `~/.todo-agent/api-calls.jsonl` latest record — confirm `input_tokens` ≤ 7,000 and the CLI response correctly lists today-flagged items; then validate S3 by running `todo "what's on my list for this week"` and `todo "show me this weekend items"` — both must return correct non-empty results

- [x] T007 [P] Validate quickstart scenario S7 (replay regression check): run `python3 -m todo_agent.cli.main cost replay replay_utterances.txt --gap 0 --output replay_after.jsonl`; compare write-operation tool chains between `replay_before.jsonl` and `replay_after.jsonl` by extracting only `dry_run: true` tool calls per utterance and confirming tool names and inputs are identical across both files; additional read-tool calls in `replay_after.jsonl` are expected and acceptable

---

## Dependencies

- T001 must complete before T002 (baseline captured before any code changes)
- T002 must complete before T003 (function must exist before it's referenced)
- T003 must complete before T004 (variables `_static`/`_dynamic` must exist before restructuring `system=`)
- T004 must complete before T005 (full change in place before test run)
- T005 must complete before T006 and T007 (tests must pass before manual validation)
- T006 and T007 can run in parallel (independent validations, different files)

## Parallel Opportunities

- T006 and T007 can run simultaneously after T005 passes
- T002 and T003 affect the same file — must run sequentially

## Implementation Strategy

### MVP First (US1 only — tasks T001–T003, T005–T006)

1. Capture baseline (T001)
2. Add compact index function (T002)
3. Update system prompt to use it (T003)
4. Run tests (T005)
5. Validate token reduction and correctness (T006)
6. **Stop and validate** — token count and response quality before adding caching

### Full Delivery (add US2 — task T004, T007)

7. Add cache_control blocks (T004)
8. Re-run tests (T005)
9. Validate cache hits appear in log (T006 second check)
10. Run replay comparison (T007)

# Implementation Plan: Reduce API Cost — Lazy Context and Prompt Caching

**Branch**: `010-reduce-api-cost` | **Date**: 2026-09-25 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/010-reduce-api-cost/spec.md`

## Summary

Two targeted changes to `todo_agent/cli/agent.py` that together reduce per-call input tokens by ~68%:

1. Replace the full board dump in the system prompt with a compact index (lane/project/count only). The agent calls existing read tools on demand for item-level detail.
2. Split the system prompt into a static block (instructions, marked for 5-minute caching) and a dynamic block (compact index, never cached).

No new tools, no new modules, no new dependencies. One file changes (`agent.py`); one test file may need minor updates (`test_agent.py`).

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `anthropic` SDK (already present — `TextBlockParam.cache_control` confirmed available)

**Storage**: No changes — data store untouched

**Testing**: pytest (existing suite); replay harness for behavioral regression

**Target Platform**: macOS / Linux local CLI

**Performance Goals**: Input tokens per call ≤ 7,000 (down from ~14,777); cache read tokens > 0 on second request within 5 minutes

**Constraints**: Agent correctness must be preserved for all 27 tool operations; no latency regression beyond one additional read-tool round-trip on detail queries

**Scale/Scope**: Single file change; existing 213 tests must pass

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Local-First | ✅ PASS | No network changes; caching is platform-side, transparent |
| II. Single Source of Truth | ✅ PASS | `agent.py` remains the sole Anthropic caller |
| III. Deterministic Core | ✅ PASS | Instrumentation untouched; LLM still orchestrates via tools |
| IV. Simplicity | ✅ PASS | No new deps; one function replaced, one prompt restructured |
| V. Human-Readable State | ✅ PASS | Data store untouched |
| VI. Staged Scope | ✅ PASS | No Phase 2 features |
| VII. User Stays in Control | ✅ PASS | No new destructive operations |

No violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/010-reduce-api-cost/
├── plan.md          # This file
├── research.md      # Phase 0 — token measurements, SDK verification, decisions
├── quickstart.md    # Phase 1 — validation scenarios
└── tasks.md         # Phase 2 output (/speckit-tasks)
```

No `data-model.md` (no new data entities). No `contracts/` (no external interface changes — entirely internal to `agent.py`).

### Source Code (repository root)

```text
todo_agent/
└── cli/
    └── agent.py    # ONLY FILE CHANGED:
                    #   _build_data_summary() → _build_compact_index()
                    #   system prompt restructured as two TextBlockParam blocks
                    #   cache_control added to static block

tests/
└── unit/
    └── test_agent.py   # Minor updates if assertions check system prompt content
```

## Implementation Detail

### Change 1: `_build_compact_index(data: dict) -> str`

Replaces `_build_data_summary()`. Produces:

```
Lane: <name>
  Project: <name> (<N> items)
  Project: <name> (<N> items)
Lane: <name>
  ...
Inbox: <N> note(s)     ← only if inbox dir exists and has .md files
```

Inbox count computed from `get_inbox_dir().glob("*.md")`.

### Change 2: System Prompt as Two Blocks

**Static block** (with `cache_control: {"type": "ephemeral"}`):
- Today's date
- Role description and behavioral instructions
- Tool-use rules (call multiple tools, prefer clarification over destructive actions)
- Explicit guidance: "The board index below shows lanes, projects, and item counts only. Call `list_items`, `get_item`, `list_inbox_notes`, or `get_inbox_note` to fetch item-level detail when needed."
- Inbox promotion workflow

**Dynamic block** (no cache_control):
- `"Current board:\n" + _build_compact_index(data)`

The `system` parameter changes from `str` to `list[dict]`. The Anthropic SDK accepts both; no other call sites exist.

### Agent Behavior After Change

The agent starts each request knowing which lanes and projects exist and their item counts. It calls `list_items` when it needs flags/deadlines/titles, and `get_item` for specific item details. The `list_items` tool description already says "Use this to answer questions like 'what items are due today?'" so no prompt engineering is needed beyond the explicit guidance note above.

## Complexity Tracking

No constitution violations — section not required.

# Tasks: Deadline Auto-Flags

**Input**: Design documents from `specs/007-deadline-auto-flags/`

**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, quickstart.md ✓

---

## Phase 1: Setup

- [x] T001 Verify `.gitignore` already covers Python patterns (already confirmed in earlier features — no-op)

---

## Phase 2: User Story 1 — Deadline Due Today Appears in Today Tab (Priority: P1) 🎯

**Goal**: Items with `deadline == today` automatically have `today=True` on every `load_data()` call, without any manual flag toggle.

**Independent Test**: Create an item with `deadline = today` and `today = False`. Call `load_data()` directly. Confirm `today == True` in the returned dict. Confirm the JSON file on disk is unchanged.

### Implementation

- [x] T002 [US1] Add `apply_deadline_flags(data: dict) -> None` function to `todo_agent/core/store.py`: iterate `data["lanes"] → projects → items`; for each item, parse `deadline` via `datetime.date.fromisoformat()` in a try/except; if `deadline == datetime.date.today()` set `item["today"] = True` (additive only; never set to False)
- [x] T003 [US1] In `load_data()` in `todo_agent/core/store.py`, call `apply_deadline_flags(data)` immediately after `json.load(f)` (and after the empty-store creation path), before `return`

---

## Phase 3: User Story 2 — Deadline This Week Appears in This Week Tab (Priority: P2)

**Goal**: Items with a deadline anywhere in the current Monday–Sunday ISO calendar week automatically have `this_week=True` on every `load_data()` call.

**Independent Test**: Create an item with `deadline` = any day of the current Mon–Sun week other than today, and `this_week = False`. Call `load_data()`. Confirm `this_week == True` in the returned dict.

### Implementation

- [x] T004 [US2] Extend `apply_deadline_flags()` in `todo_agent/core/store.py` to also check the ISO week: if `deadline.isocalendar()[:2] == datetime.date.today().isocalendar()[:2]` set `item["this_week"] = True` (additive only). This runs in the same per-item loop as the `today` check — both checks happen together.

---

## Phase 4: Polish & Validation

- [x] T005 Write unit tests in `tests/unit/test_deadline_flags.py` covering: (a) deadline == today sets `today=True`; (b) deadline in current week but not today sets `this_week=True`; (c) deadline == today also sets `this_week=True`; (d) overdue deadline (yesterday) sets neither flag; (e) next-week deadline sets neither flag; (f) null deadline leaves flags untouched; (g) malformed deadline string is silently skipped; (h) manually-set `today=True` with no deadline is preserved; (i) manually-set `this_week=True` with no deadline is preserved; (j) `save_data()` is never called by `apply_deadline_flags()`
- [x] T006 Run full test suite `pytest -v` and confirm all tests pass (no regressions)
- [ ] T007 Manual validation of quickstart.md scenarios S1–S7 via GUI and CLI

---

## Dependencies

- T002 must complete before T003 (function must exist before it is called)
- T003 must complete before T004 (both extend the same function; sequential to avoid conflicts)
- T005, T006, T007 depend on T002–T004 completing
- T006 depends on T005

## Parallel Opportunities

- T005 can be written in parallel with T002–T004 (tests reference the function signature but do not block implementation)
- T006 and T007 are independent of each other (different files, different surfaces)

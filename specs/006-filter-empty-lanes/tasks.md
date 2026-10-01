# Tasks: Filter Empty Lanes

**Input**: Design documents from `specs/006-filter-empty-lanes/`

**Prerequisites**: plan.md ✓, spec.md ✓, quickstart.md ✓

## Phase 1: Setup

- [x] T001 Verify `.gitignore` is present and covers Python patterns (already confirmed in feature 005)

---

## Phase 2: User Story 1 — Hide Empty Lanes in Filtered Views (Priority: P1) 🎯

**Goal**: In filtered tabs (Today, This Week, This Weekend), skip rendering lanes that have no items matching the active filter.

**Independent Test**: With two lanes where only one has a today-flagged item, the Today tab shows only the matching lane. The All tab continues to show both.

### Implementation

- [x] T002 [US1] In `todo_agent/gui/static/app.js` `render()` function: before calling `buildLaneCol(lane, view)`, check whether the lane has at least one item passing `filteredItems()` for the active view — skip the lane entirely if none match (guard only applies when `view !== "all"`)

---

## Phase 3: Polish & Validation

- [x] T003 Run full test suite `pytest -v` and confirm all 155 tests still pass
- [x] T004 Manual browser validation of quickstart.md scenarios S1–S8

---

## Dependencies

- T002 is the sole implementation task — no sequencing needed.
- T003 and T004 depend on T002 completing.

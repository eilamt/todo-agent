# Feature Specification: Deadline Auto-Flags

**Feature Branch**: `007-deadline-auto-flags`

**Created**: 2026-09-22

**Status**: Draft

**Input**: User description: "Auto-set today=True on items whose deadline equals today's date, and this_week=True on items whose deadline falls within the current Monday-Sunday calendar week. Flags are additive on every load — existing manually-set flags are never cleared. Items with no deadline are unaffected."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Deadline Due Today Appears in Today Tab (Priority: P1)

A user sets a deadline of today on a task and forgets to manually flag it. When they open the app or the GUI refreshes, the item automatically appears in the Today tab — no manual action required.

**Why this priority**: The most direct and high-value case: a task due today must always surface in the Today view without extra effort from the user.

**Independent Test**: Create an item with `deadline = today`. Without toggling any flag, open the Today tab — the item appears. Remove the deadline — the item disappears from Today (assuming no manual flag was set).

**Acceptance Scenarios**:

1. **Given** an item with `deadline = today` and `today = False`, **When** the app loads or the GUI polls, **Then** the item appears in the Today tab.
2. **Given** an item with `deadline = today` and `today = True` (manually set), **When** the app loads, **Then** the item still appears in the Today tab (flag is not cleared).
3. **Given** an item with `deadline = tomorrow`, **When** the app loads, **Then** the item does NOT appear in the Today tab solely due to deadline.
4. **Given** an item with no deadline and `today = True` (manually set), **When** the app loads, **Then** the item still appears in the Today tab (manual flag is preserved).

---

### User Story 2 - Deadline This Week Appears in This Week Tab (Priority: P2)

A user sets a deadline anywhere within the current Monday–Sunday week. The item automatically appears in the This Week tab on every load, giving the user a complete view of what needs to be done this week.

**Why this priority**: Complements the Today auto-flag; gives users a broader weekly horizon without manual flag management.

**Independent Test**: Create an item with a deadline on any day of the current Mon–Sun week (but not today). Without toggling any flag, open the This Week tab — the item appears.

**Acceptance Scenarios**:

1. **Given** an item with `deadline` on any day in the current Mon–Sun week, **When** the app loads, **Then** the item appears in the This Week tab.
2. **Given** an item with `deadline = today` (which is also within this week), **When** the app loads, **Then** the item appears in BOTH the Today tab and the This Week tab.
3. **Given** an item with `deadline` on a day in next week, **When** the app loads, **Then** the item does NOT appear in the This Week tab solely due to deadline.
4. **Given** an item with `deadline` on a day in last week, **When** the app loads, **Then** the item does NOT appear in the This Week tab.
5. **Given** an item with no deadline and `this_week = True` (manually set), **When** the app loads, **Then** the item still appears in the This Week tab (manual flag is preserved).

---

### Edge Cases

- What if an item's deadline was yesterday (overdue)? It does NOT auto-set `today`; the user must manually flag it or reschedule the deadline. Overdue handling is out of scope.
- What if today is Monday — does an item with `deadline = Monday` appear in both Today and This Week? Yes, both flags are set independently.
- What if today is Sunday — does `this_week` cover Monday through today (Sunday)? Yes, the full Mon–Sun week including today.
- What happens at midnight? The GUI's next poll cycle after midnight will pick up the new date and update flags accordingly — no special midnight handling required.
- What if the deadline field contains an invalid or malformed date? The item is treated as having no deadline — no flags are set.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Any item with `deadline == today's date` MUST have `today` set to `True` on every data load, regardless of its stored value.
- **FR-002**: Any item with `deadline` falling within the current Monday–Sunday calendar week MUST have `this_week` set to `True` on every data load.
- **FR-003**: The deadline-based flag computation MUST be additive — it can only set flags to `True`, never to `False`. Manually-set `today` or `this_week` flags MUST NOT be cleared by this computation.
- **FR-004**: Items with no deadline MUST NOT be affected by this computation.
- **FR-005**: Items with a deadline outside today or the current week MUST NOT have their flags auto-set by this computation (though manually-set flags remain untouched).
- **FR-006**: The computation MUST run on every data load so flags always reflect the current date — including across the GUI's polling cycle and between separate CLI invocations.
- **FR-007**: Malformed or unparseable deadline values MUST be silently skipped — no error is raised and the item is treated as having no deadline.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of items with `deadline = today` appear in the Today tab without any manual flag toggle.
- **SC-002**: 100% of items with a deadline within the current Mon–Sun week appear in the This Week tab without any manual flag toggle.
- **SC-003**: Zero manually-set `today` or `this_week` flags are cleared as a side effect of the deadline computation.
- **SC-004**: Items with deadlines outside the current day/week are not incorrectly surfaced in Today or This Week tabs.
- **SC-005**: The feature requires no user-facing configuration — it works automatically from the moment a deadline is set.

## Assumptions

- "Current week" is defined as Monday through Sunday of the week containing today's date (ISO calendar week).
- Overdue items (deadline in the past, before today) do not auto-set `today` or `this_week` — only current-day and current-week deadlines trigger flags.
- The deadline field is stored as an ISO 8601 date string (`YYYY-MM-DD`) or `null`; no time component is involved.
- The computation does not persist flag changes back to the data file — flags are applied to the in-memory snapshot returned by the data load, keeping the stored file clean and the flags purely derived.
- The GUI poll cycle (every 5 seconds) is the accepted latency for date-change updates (e.g. overnight).

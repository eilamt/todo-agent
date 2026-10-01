# Feature Specification: Filter Empty Lanes

**Feature Branch**: `006-filter-empty-lanes`

**Created**: 2026-09-20

**Status**: Draft

**Input**: User description: "In filtered tabs (Today, This Week, This Weekend), hide any lane that has no projects with items matching the active filter. The All tab is unaffected. Frontend-only change in app.js."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Hide Empty Lanes in Filtered Views (Priority: P1)

A user switches to the Today, This Week, or This Weekend tab. They only want to see lanes that are actually relevant — lanes where at least one item matches the filter. Lanes with no matching items anywhere inside them should disappear from view entirely, reducing visual noise.

**Why this priority**: This is the entire feature — a single, focused behaviour change with no sub-stories.

**Independent Test**: With two lanes where only one contains a today-flagged item, switch to the Today tab — only the lane with the matching item appears. Switch back to All — both lanes appear. Unflag the item — switch to Today again — that lane now disappears too.

**Acceptance Scenarios**:

1. **Given** a board with lanes A (has a today item) and B (no today items), **When** the user clicks the Today tab, **Then** only lane A is shown; lane B is hidden.
2. **Given** a board with lanes A and B both having this-week items, **When** the user clicks the This Week tab, **Then** both lanes are shown.
3. **Given** a board where no lane has any this-weekend items, **When** the user clicks the This Weekend tab, **Then** no lanes are shown (the board is empty).
4. **Given** the Today tab is active and shows only lane A, **When** the user switches to the All tab, **Then** all lanes reappear regardless of their item flags.
5. **Given** the Today tab is active showing lane A, **When** the user unchecks the today flag on the last matching item (triggering a poll), **Then** lane A disappears from the Today view.
6. **Given** a lane with multiple projects where only one project has a matching item, **When** viewing a filtered tab, **Then** the lane is shown (because it has at least one matching item somewhere inside it).

---

### Edge Cases

- What if a lane has projects but all projects have zero items? Lane is hidden in all filtered tabs (no items means no matching items).
- What if a lane has no projects at all? Lane is hidden in all filtered tabs.
- What if the same item has multiple flags set (e.g. `today=true` and `this_week=true`)? The lane appears in both the Today and This Week tabs independently.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: In the Today, This Week, and This Weekend filtered tabs, a lane MUST only be displayed if it contains at least one item where the corresponding flag (`today`, `this_week`, `this_weekend`) is `true`.
- **FR-002**: In the All tab, all lanes MUST be displayed regardless of item flags — existing behaviour is unchanged.
- **FR-003**: The lane visibility check MUST consider items across all projects within the lane — a single matching item anywhere in the lane is sufficient to show it.
- **FR-004**: Lane visibility MUST update automatically on the next poll cycle when item flags change (no manual refresh required).
- **FR-005**: No changes to the data model, backend API, or server are permitted — this is a display-only adjustment.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In any filtered tab, 100% of visible lanes contain at least one item matching the active filter.
- **SC-002**: Switching between filtered tabs and the All tab produces the correct lane set instantly (within the existing poll cycle).
- **SC-003**: The All tab continues to show all lanes — zero regressions in existing behaviour.

## Assumptions

- The poll cycle (every 5 seconds) is the accepted update latency for lane visibility changes triggered by flag toggles.
- An empty filtered board (no matching lanes) shows no lanes and no error — same as the existing behaviour when all projects in a lane are filtered out.
- Lane hiding is purely visual — hidden lanes remain in the data store and reappear in the All tab.

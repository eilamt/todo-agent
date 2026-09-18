# Feature Specification: GUI Inline Editing

**Feature Branch**: `003-gui-interactivity`

**Created**: 2026-09-17

**Status**: Draft

**Input**: User description: "Add full GUI interactivity for all item and project fields."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Edit Item Fields Inline (Priority: P1)

A user viewing the board can click on any editable field on an item card — title, description, importance, or deadline — and edit it directly without leaving the board. Changes are saved automatically when the user confirms (presses Enter or clicks outside the field).

**Why this priority**: This is the core request. The CLI is the only way to edit fields today; bringing editing into the GUI removes the primary friction point and makes the GUI a self-contained productivity tool.

**Independent Test**: Open the board, click an item's title, type a new name, press Enter. The card updates with the new title immediately and persists after a page refresh.

**Acceptance Scenarios**:

1. **Given** an item card is displayed, **When** the user clicks the item title, **Then** the title becomes an editable text input pre-filled with the current value.
2. **Given** an item title input is active, **When** the user types a new title and presses Enter, **Then** the change is saved, the input reverts to display text, and the card shows the updated title.
3. **Given** an item title input is active, **When** the user clicks outside the input (blur), **Then** the change is saved automatically.
4. **Given** an item card is displayed, **When** the user edits the description inline (textarea), **Then** the description updates on save.
5. **Given** an item has no description, **When** the user clicks a "clear" button next to an empty description input, **Then** the description is set to null and no description area is shown.
6. **Given** an item card is displayed, **When** the user edits the importance field (0–100), **Then** the updated importance is saved and the high-importance highlight appears or disappears accordingly.
7. **Given** an item card is displayed, **When** the user sets or clears the deadline via a date input, **Then** the deadline badge on the card updates immediately.

---

### User Story 2 — Toggle Item Flags (Priority: P2)

A user can toggle the "today" and "this week" flags on an item card directly via checkboxes. The change is saved immediately without any confirm step.

**Why this priority**: Flag toggling is the most frequent daily action (marking tasks for today). Inline checkboxes remove the need to type CLI commands for the most common workflow.

**Independent Test**: Open the board, click the "today" checkbox on an item. Verify the card shows the "today" badge and a page refresh confirms persistence.

**Acceptance Scenarios**:

1. **Given** an item card is displayed, **When** the user checks the "today" checkbox, **Then** the today flag is saved to true and the "today" badge appears on the card.
2. **Given** an item with today=true, **When** the user unchecks the "today" checkbox, **Then** the today flag is saved to false and the badge disappears.
3. **Given** an item card is displayed, **When** the user toggles "this week", **Then** only the this_week flag changes; the today flag is not affected.

---

### User Story 3 — Edit Project Fields Inline (Priority: P3)

A user can click a project name to rename it inline, and edit the project's importance score directly on the project header — without using the CLI.

**Why this priority**: Project-level editing is less frequent than item editing but rounds out the GUI as a full CRUD interface. Project names appear in bold for visual hierarchy.

**Independent Test**: Click a project name, type a new name, press Enter. The project header updates to the new bold name and persists on refresh.

**Acceptance Scenarios**:

1. **Given** a project header is displayed, **When** the user clicks the project name, **Then** the name becomes an editable text input.
2. **Given** a project name input is active, **When** the user types a new name and confirms, **Then** the project header shows the updated name in bold.
3. **Given** a project header is displayed, **When** the user edits the importance field, **Then** the updated importance score is saved and shown.

---

### User Story 4 — Collapsible Item Cards (Priority: P4)

Each item card has a collapse/expand toggle. When collapsed, only the item title (and its status) remains visible. A global "Collapse all / Expand all" button in the header controls all cards simultaneously.

**Why this priority**: As boards grow, collapsed cards reduce visual noise and let users focus on specific items. This is a quality-of-life improvement that requires the other editing features to be in place first.

**Independent Test**: Click the collapse toggle on one item. The description, flags, deadline, importance badge, and delete button all hide. Only the title row remains. Click the global "Expand all" button — all cards on the board expand.

**Acceptance Scenarios**:

1. **Given** an item card is expanded, **When** the user clicks the collapse toggle, **Then** all fields except the title become hidden.
2. **Given** an item card is collapsed, **When** the user clicks the expand toggle, **Then** all fields return to their visible state.
3. **Given** multiple items are displayed, **When** the user clicks "Collapse all" in the header, **Then** all item cards collapse.
4. **Given** all item cards are collapsed, **When** the user clicks "Expand all", **Then** all item cards expand.

---

### Edge Cases

- What happens when a user clears an item title to blank and saves? The save must be rejected client-side; the original title is restored and no API call is made.
- What happens when an importance value outside 0–100 is entered? The input is rejected client-side (clamped or shown as invalid); no API call is made.
- What happens if an API save fails (e.g., server not running)? The field reverts to its previous value and a brief error indicator is shown.
- What happens when an item is collapsed and the user clicks the delete button? The delete confirmation still appears and works correctly.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to edit item title inline by clicking on it; the edit MUST confirm on Enter or blur and be saved immediately.
- **FR-002**: Users MUST be able to edit item description inline via a textarea; a clear button MUST allow setting description to null.
- **FR-003**: Users MUST be able to edit item importance inline (integer 0–100); the high-importance highlight MUST update immediately after save.
- **FR-004**: Users MUST be able to set or clear an item's deadline via an inline date input; the change MUST be saved immediately on input change.
- **FR-005**: Users MUST be able to toggle item "today" and "this week" flags via checkboxes; each toggle MUST save immediately without a confirm step.
- **FR-006**: Users MUST be able to rename a project inline by clicking the project name; the edit MUST confirm on Enter or blur.
- **FR-007**: Users MUST be able to edit project importance inline (integer 0–100); the change MUST save on confirm.
- **FR-008**: Project names MUST be displayed in bold black text at all times.
- **FR-009**: When a field is in edit mode, a visual highlight (e.g., distinct border) MUST be shown on the active input.
- **FR-010**: Each item card MUST have a collapse/expand toggle that hides all fields except the title when collapsed.
- **FR-011**: A global "Collapse all / Expand all" control in the page header MUST apply to all item cards simultaneously.
- **FR-012**: A blank item title input MUST be rejected client-side; the original title MUST be restored with no server call.
- **FR-013**: An importance value outside 0–100 MUST be rejected client-side with no server call.
- **FR-014**: If an API save call fails, the field MUST revert to its prior value.
- **FR-015**: Notes fields MUST remain non-editable in the GUI (append-only).
- **FR-016**: percent_complete and push_count fields MUST remain read-only display values in the GUI.

### Key Entities

- **Item**: A task card with editable fields: title, description, importance, today, this_week, deadline, status. Read-only: percent_complete, push_count, notes.
- **Project**: A group of items with editable fields: name, importance, status. Read-only: percent_complete, notes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can update any editable item field (title, description, importance, deadline, flags) entirely within the GUI board with zero CLI commands.
- **SC-002**: All GUI saves complete and the board reflects the updated value within 1 second under normal local conditions.
- **SC-003**: Invalid inputs (blank title, out-of-range importance) are caught and rejected before any server call, with clear visual feedback.
- **SC-004**: The board remains usable and all existing cards are navigable when all items are collapsed, with only titles visible.
- **SC-005**: All edits persist correctly after a full page refresh, confirming round-trip data integrity.

## Assumptions

- The GUI server runs locally and all API calls succeed within normal local response times.
- The existing REST endpoints (PATCH /api/items/:id and PATCH /api/projects/:id) already accept the fields being edited; no new backend endpoints are required.
- The project PATCH endpoint accepts `name` and `importance` fields (currently only `status` is used by the GUI — this assumption needs verification during planning).
- Item title uniqueness enforcement (within a project) occurs server-side; a duplicate-title save will return an error and the client will revert the field.
- The GUI is a single-user local tool; no concurrent-edit conflict resolution is required.
- Mobile/touch optimisation is out of scope; the GUI targets desktop browsers only.
- The "Saved" flash indicator after successful saves is a nice-to-have and may be omitted if it adds complexity beyond simple styling.

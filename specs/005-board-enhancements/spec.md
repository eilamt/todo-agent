# Feature Specification: Board Enhancements

**Feature Branch**: `005-board-enhancements`

**Created**: 2026-09-18

**Status**: Draft

**Input**: User description: "Add a 'this-weekend' binary flag to items alongside today/this-week, a This Weekend tab in the GUI, drag-and-drop to reorder lanes left/right on the board, and drag-and-drop to reorder projects up/down within a lane."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Mark Items for This Weekend (Priority: P1)

A user wants to flag certain to-do items as relevant to the upcoming weekend — separate from what they need to do today or this week. They can mark any item as "this weekend" and instantly see all such items in a dedicated board tab.

**Why this priority**: This-weekend is the core data/scheduling addition that the other two stories do not depend on. It delivers standalone value and mirrors the established pattern for today and this-week.

**Independent Test**: Can be fully tested by marking an item as "this weekend" via the GUI toggle and verifying it appears in the This Weekend tab — no other enhancement needed.

**Acceptance Scenarios**:

1. **Given** an item with `this_weekend=False`, **When** the user enables the this-weekend toggle on the item card, **Then** `this_weekend` is set to `True` and the item appears in the This Weekend tab.
2. **Given** an item with `this_weekend=True`, **When** the user disables the toggle, **Then** the item disappears from the This Weekend tab.
3. **Given** a board with multiple items, **When** the user navigates to the This Weekend tab, **Then** only items where `this_weekend=True` are shown.
4. **Given** existing saved data that has no `this_weekend` field, **When** the application loads, **Then** all such items default to `this_weekend=False` without errors.
5. **Given** a user types "add task X to this weekend" in the CLI/agent, **When** the command is processed, **Then** `this_weekend` is set to `True` on task X.

---

### User Story 2 - Reorder Lanes Left/Right (Priority: P2)

A user has multiple lanes on their board and wants to change their left-to-right display order by dragging a lane column to a new position.

**Why this priority**: Lane reordering is a board-level organisational feature. It is independent of the this-weekend flag and the within-lane project ordering.

**Independent Test**: Can be fully tested by dragging a lane column header to a new position, releasing it, reloading the page, and confirming the order persisted.

**Acceptance Scenarios**:

1. **Given** a board with at least two lanes, **When** the user drags a lane column header to the left of another lane, **Then** the dragged lane appears to the left of that lane.
2. **Given** a board with at least two lanes, **When** the user drags a lane column header to the right of another lane, **Then** the dragged lane appears to the right of that lane.
3. **Given** a reordered board, **When** the user reloads the page, **Then** the lane order matches the last drag result (order is persisted).
4. **Given** a drag operation in progress, **When** the user releases the dragged lane outside of a valid drop zone, **Then** the lane returns to its original position and no data changes.
5. **Given** a board with one lane, **When** the user attempts to drag the single lane, **Then** the interaction is a no-op (nothing breaks).

---

### User Story 3 - Reorder Projects Up/Down Within a Lane (Priority: P3)

A user has multiple projects inside a lane and wants to change their top-to-bottom display order by dragging a project card to a new position within the same lane.

**Why this priority**: Project reordering is scoped within a lane and is the most granular of the three features. It delivers value only when there are multiple projects in a lane.

**Independent Test**: Can be fully tested by dragging a project card above or below another project card within the same lane, releasing it, reloading the page, and confirming the order persisted.

**Acceptance Scenarios**:

1. **Given** a lane with at least two projects, **When** the user drags a project card above another project, **Then** the dragged project appears above that project.
2. **Given** a lane with at least two projects, **When** the user drags a project card below another project, **Then** the dragged project appears below that project.
3. **Given** a reordered lane, **When** the user reloads the page, **Then** the project order within the lane matches the last drag result.
4. **Given** a drag operation where the user drags a project card and releases it outside its origin lane, **Then** the project returns to its original position and no cross-lane move occurs.
5. **Given** a lane with one project, **When** the user attempts to drag the single project, **Then** the interaction is a no-op (nothing breaks).

---

### Edge Cases

- What happens when two tabs (This Weekend and Today) both show the same item (item has both `today=True` and `this_weekend=True`)? Both tabs must show it independently.
- How does the board handle a lane drag when the page is mid-scroll? The drag should still resolve to the correct drop target.
- What happens if the data file is written during a drag operation? The drop must always reflect the user's intent; the next full reload will reflect the persisted state.
- What happens when a project is dragged to the very top or bottom of a lane? It should become the first or last item respectively.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each item MUST have a `this_weekend` boolean attribute that defaults to `False` when absent in existing data.
- **FR-002**: Users MUST be able to toggle `this_weekend` on any item via an inline control in the item card, consistent with the existing `today` and `this_week` toggles.
- **FR-003**: The board MUST include a **This Weekend** tab that displays only items where `this_weekend=True`, following the same layout and behaviour as the existing Today and This Week tabs.
- **FR-004**: The agent/CLI MUST understand natural-language commands for setting and clearing `this_weekend` (e.g., "add X to this weekend", "remove X from this weekend").
- **FR-005**: Lane columns on the board MUST be draggable left and right to reorder them relative to each other.
- **FR-006**: The new lane order MUST be persisted to the data store immediately after a successful drop.
- **FR-007**: Projects within a lane MUST be draggable up and down to reorder them relative to other projects in the same lane.
- **FR-008**: The new project order within a lane MUST be persisted to the data store immediately after a successful drop.
- **FR-009**: Dropping a dragged element (lane or project) outside a valid drop target MUST be a safe no-op — the element returns to its original position and no data changes.
- **FR-010**: All drag interactions MUST provide visual affordance (e.g., a drag handle or cursor change) so the user knows dragging is available.

### Key Entities

- **TodoItem**: Extended with `this_weekend: bool = False` alongside existing `today` and `this_week` fields.
- **Lane**: Already an ordered list; order is now user-controllable via drag-and-drop. The list position in the data store is the authoritative order.
- **Project**: Already an ordered list within its parent lane; order is now user-controllable via drag-and-drop. The list position within the lane in the data store is the authoritative order.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can mark an item as "this weekend" and see it appear in the This Weekend tab in under 1 second.
- **SC-002**: A user can drag a lane to a new position and have the new order persist — verifiable by reloading the page — with the entire interaction completing in under 3 seconds.
- **SC-003**: A user can drag a project within a lane to a new position and have the new order persist — verifiable by reloading the page — with the entire interaction completing in under 3 seconds.
- **SC-004**: All three enhancements are independently usable — each can be exercised without requiring the others to be in use.
- **SC-005**: Existing data files without the `this_weekend` field load without errors and treat all items as `this_weekend=False`.

## Assumptions

- The `this_weekend` field follows the exact same persistence and serialisation pattern already used for `today` and `this_week` on `TodoItem`.
- The GUI currently renders lanes as columns and projects as vertical cards within a column — the drag-and-drop model maps directly onto this layout.
- Both drag-and-drop interactions (lanes and projects) can share the same underlying drag-and-drop mechanism or library; the implementation choice is deferred to planning.
- Cross-lane project moves are explicitly out of scope for this feature; dropping a project card outside its origin lane is a no-op.
- The This Weekend tab uses the same filtering and display approach as the Today tab; no new layout or grouping logic is required.
- Mobile/touch drag-and-drop support is out of scope for this iteration.

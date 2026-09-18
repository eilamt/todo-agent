# Feature Specification: Item Data Model Enhancements

**Feature Branch**: `002-item-data-model`

**Created**: 2026-09-17

**Status**: Draft

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add Description to an Item (Priority: P1)

A user wants to capture more context about a to-do item beyond its title. They type a natural-language command to set a description on an existing item, and the system stores it. When the user opens the visual board, the description appears beneath the item title.

**Why this priority**: Description is the simpler of the two fields (no validation range, no visual highlighting logic) and unlocks richer item context immediately.

**Independent Test**: Create an item, set its description via the CLI, open the board and confirm the description appears below the title.

**Acceptance Scenarios**:

1. **Given** an existing item "Design homepage", **When** the user runs `todo "set description of Design homepage to: needs mobile-first approach"`, **Then** the item's description is saved as "needs mobile-first approach" and a confirmation is printed.
2. **Given** an item with a description, **When** the user sets a new description, **Then** the old description is replaced (not appended).
3. **Given** an item with a description, **When** the user clears the description (e.g. `todo "clear description of Design homepage"`), **Then** the description is set to null.
4. **Given** an item with a description, **When** the board is viewed, **Then** the description text appears below the title on the item card.
5. **Given** an item with no description, **When** the board is viewed, **Then** no description area is rendered on the card (no empty placeholder).
6. **Given** a new item is created with a description in the same command, **When** the item is saved, **Then** the description is stored alongside the title.

---

### User Story 2 - Set and View Item Importance (Priority: P2)

A user wants to mark certain items as high-priority by assigning them an importance score. They set the score via a natural-language command. On the visual board, items with importance above 80 are visually distinct so the user can immediately spot the most critical work.

**Why this priority**: Importance scoring on items mirrors the existing project-level field and enables priority-at-a-glance on the board. Depends on US1's schema plumbing being in place.

**Independent Test**: Create an item, set its importance to 90 via the CLI, open the board and confirm the item is highlighted differently from a default-importance item.

**Acceptance Scenarios**:

1. **Given** an existing item "Design homepage", **When** the user runs `todo "set importance of Design homepage to 90"`, **Then** the item's importance is saved as 90 and a confirmation is printed.
2. **Given** an item with importance set to 90, **When** the board is viewed, **Then** the item card has a distinct visual highlight (e.g. coloured border or tinted background).
3. **Given** an item with importance set to 50 (default), **When** the board is viewed, **Then** the item card has no special highlight.
4. **Given** the user attempts to set importance to 101 or -1, **Then** the system rejects the value with a clear error message and does not modify the item.
5. **Given** a new item is created without specifying importance, **Then** its importance defaults to 50.
6. **Given** an existing stored item that pre-dates this feature (no importance field in JSON), **When** it is loaded, **Then** it is treated as having importance 50 (backward-compatible default).

---

### Edge Cases

- What happens when the user sets a description on an item that does not exist? → System returns a clear "item not found" error; no data is written.
- What happens if two items in different projects have the same title and the user sets a description without specifying the project? → System asks for clarification (existing `AmbiguousMatchError` behaviour is reused).
- What happens when importance is set to exactly 80? → No highlight (threshold is strictly greater than 80).
- What happens when importance is set to exactly 81? → Highlight is applied.
- What happens if description is set to an empty string? → Treated as clearing the description (stored as null).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Items MUST support an optional `description` field (free text, null by default).
- **FR-002**: Users MUST be able to set an item's description via a natural-language CLI command.
- **FR-003**: Users MUST be able to clear an item's description (set it back to null) via CLI.
- **FR-004**: The system MUST display an item's description below its title in the visual board when the description is non-null.
- **FR-005**: The system MUST NOT display a description area on item cards where description is null.
- **FR-006**: Items MUST support an `importance` field — an integer from 0 to 100, defaulting to 50.
- **FR-007**: Users MUST be able to set an item's importance via a natural-language CLI command.
- **FR-008**: The system MUST reject importance values outside the range 0–100 with a clear error message.
- **FR-009**: Items with importance strictly greater than 80 MUST be visually highlighted on the board (distinct from non-highlighted items).
- **FR-010**: Items with importance of 80 or below MUST NOT be highlighted.
- **FR-011**: Both new fields MUST be backward-compatible: existing stored items missing these fields MUST be read without error, defaulting to null (description) and 50 (importance).
- **FR-012**: A new item created without a description MUST have description set to null.
- **FR-013**: A new item created without an explicit importance value MUST have importance set to 50.
- **FR-014**: An empty-string description MUST be stored as null (not as an empty string).

### Key Entities

- **Item**: Extended with two new fields — `description` (optional free text) and `importance` (integer 0–100, default 50). All other item fields are unchanged.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can set and retrieve an item description in a single CLI command with no additional steps.
- **SC-002**: 100% of items with importance > 80 are visually distinguishable from items with importance ≤ 80 on the board without any user action beyond loading the page.
- **SC-003**: All existing stored items load without error after the schema change is deployed.
- **SC-004**: Attempting to set an invalid importance value (outside 0–100) always produces a visible error and never modifies stored data.

## Assumptions

- The existing `validate_importance` function in the codebase covers the 0–100 range check and will be reused for item importance without modification.
- Description field has no maximum length enforced at the application layer (the local JSON file is the only storage, so size is at the user's discretion).
- Inline editing of description and importance from the GUI is explicitly out of scope for this feature (covered by a separate GUI interactivity spec).
- The visual highlight style for importance > 80 is a left-border accent or background tint; the exact colour is an implementation detail left to the GUI layer.
- No reminder, scheduling, or notification logic is tied to item importance in this phase.

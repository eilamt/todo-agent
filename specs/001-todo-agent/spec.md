# Feature Specification: Personal To-Do Agent

**Feature Branch**: `001-todo-agent`

**Created**: 2026-09-17

**Status**: Draft

**Input**: User description: "Build a personal to-do management agent with two interfaces — a
command-line natural-language interface, and a local interactive graphical view — sharing one
underlying data store."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Manage Tasks via Natural Language CLI (Priority: P1)

As a user, I want to type natural-language commands into a terminal to add, update, and remove
my to-do items, projects, and lanes without memorising exact syntax or record IDs.

**Why this priority**: The CLI is the primary interaction model. All day-to-day data changes
flow through it. Without a working CLI, no other part of the system has data to operate on.

**Independent Test**: Can be fully tested by running the CLI against a fresh data store, adding
lanes/projects/items, changing statuses, and confirming the shared data store reflects every
change immediately.

**Acceptance Scenarios**:

1. **Given** an empty data store, **When** I run `todo "add a new lane called Work"`, **Then**
   a lane named "Work" appears in the data store, a blank Markdown instructions file is
   auto-created at the default path (e.g., `~/.todo-agent/lanes/work.md`), and a confirmation
   message is printed.
2. **Given** a lane "Work" exists, **When** I run `todo "add a project to Work called Website
   Redesign"`, **Then** a project "Website Redesign" belonging to "Work" is created in the data
   store.
3. **Given** a project "Website Redesign" with items exists, **When** I run `todo "mark the
   homepage task as done"`, **Then** the matching item's status is set to `completed` and the
   project's percent-complete is recalculated automatically.
4. **Given** an item "Budget Review" exists, **When** I run `todo "move the budget review task
   to today"`, **Then** the item's `today` flag is set to `true`.
5. **Given** free text matches two or more items equally, **When** I run an ambiguous command,
   **Then** the system asks me to clarify rather than acting on a guess.

---

### User Story 2 - Safely Delete Entities with Cascade Confirmation (Priority: P2)

As a user, I want to delete lanes, projects, or items from the CLI or GUI with a prompt that
tells me exactly how much data will be removed before I commit to the action.

**Why this priority**: Destructive operations are irreversible. Trust in the tool depends on
never silently losing data.

**Independent Test**: Can be tested independently by attempting to delete a lane that contains
projects and items, verifying the prompt includes accurate counts, then testing both confirm and
cancel paths.

**Acceptance Scenarios**:

1. **Given** a lane "Health" has 3 projects and 10 items in total, **When** I run `todo "delete
   the Health lane"`, **Then** the system displays "This will permanently delete 'Health', 3
   projects, and 10 items. Confirm? (y/n)" and waits for input.
2. **Given** that prompt is displayed, **When** I respond `n`, **Then** no data is modified and
   the system reports that the deletion was cancelled.
3. **Given** that prompt is displayed, **When** I respond `y`, **Then** the lane and all its
   projects and items are removed from the data store.
4. **Given** the same scenario in the GUI, **When** I click delete on a lane, **Then** a modal
   appears with the same entity name, project count, and item count before any data is removed.

---

### User Story 3 - Visualise Tasks in a Local Browser View (Priority: P3)

As a user, I want to open a local web view of my lanes, projects, and items, filtered to "all",
"today", or "this week", and interact with data directly in the browser while continuing to use
the CLI in parallel.

**Why this priority**: The GUI provides an at-a-glance overview that terminal output cannot
match. Changes made in either interface must stay in sync automatically.

**Independent Test**: Can be tested by launching the GUI against a populated data store,
verifying the lane/project/item layout, changing a status in the GUI, and confirming the data
store is updated. Then making a CLI change and confirming the GUI reflects it without a reload.

**Acceptance Scenarios**:

1. **Given** a populated data store, **When** I run `todo visualize` or `todo visualize all`,
   **Then** a local web server starts and the browser opens to a view of all
   lanes/projects/items.
2. **Given** the GUI is open, **When** I run a CLI command that changes an item's status, **Then**
   the GUI reflects that change automatically within a short interval, without a manual reload.
3. **Given** the GUI is open, **When** I switch to the "today" view filter, **Then** only items
   with `today: true` are shown.
4. **Given** the GUI is open, **When** I change a project's status using its dropdown, **Then**
   the data store is updated immediately and the GUI continues to reflect the new state.
5. **Given** the GUI is open, **When** I click the delete button on a project that has items,
   **Then** a confirmation dialog states the project name and item count before any deletion.

---

### User Story 4 - Append Timestamped Notes to Projects and Items (Priority: P4)

As a user, I want to append free-text notes (with automatic timestamps) to any project or item
so I have a running log of context, blockers, or progress.

**Why this priority**: Notes are a non-destructive, append-only operation that significantly
increases the tool's value for personal tracking without adding complexity.

**Independent Test**: Can be tested by appending notes to a project and an item, then reading
them back and verifying content and timestamp ordering.

**Acceptance Scenarios**:

1. **Given** a project "Budget", **When** I run `todo "note on the Budget project: waiting on
   finance team"`, **Then** a note with text "waiting on finance team" and the current timestamp
   is appended to the project's notes list.
2. **Given** an item "Q3 Review", **When** I run `todo "note on the Q3 review task: sent draft
   to Alice"`, **Then** a note with text "sent draft to Alice" and the current timestamp is
   appended to the item's notes list.
3. **Given** notes have been appended over time, **When** I run `todo "show notes for the Budget
   project"` or `todo "show notes for the Q3 review task"`, **Then** all notes appear in
   chronological order, each showing its text and UTC timestamp.
4. **Given** Phase 1, **When** a user attempts to edit or delete an existing note, **Then** no
   mechanism exists to do so (notes are append-only in this phase).

---

### User Story 5 - Set Project Scheduling Fields and Importance (Priority: P5)

As a user, I want to set a project's start date (when status is `scheduled`) and importance
score so that, when automated reminders arrive in Phase 2, all the data is already in place.

**Why this priority**: These fields must be stored and settable now to avoid a schema migration
later. No automated logic acts on them in Phase 1.

**Independent Test**: Can be tested by setting a project to `scheduled` with a start date of
a future date, setting importance to 80, and reading the data store to confirm both values are
persisted correctly.

**Acceptance Scenarios**:

1. **Given** a project "Q4 Planning", **When** I run `todo "schedule Q4 Planning to start on
   2026-10-01"`, **Then** the project's status becomes `scheduled` and its `start_date` is set
   to `2026-10-01`.
2. **Given** a project "Q4 Planning", **When** I run `todo "set importance of Q4 Planning to
   80"`, **Then** the project's `importance` field is stored as `80`.
3. **Given** a project with zero items, **When** its percent-complete is read, **Then** it is
   returned as `null` and displayed as "—", not as `0%`.

---

### Edge Cases

- What happens when free text matches multiple items with the same name? The system asks the user
  to clarify (by lane or project context) rather than acting destructively.
- What happens when a delete is requested for an entity that does not exist? The system returns a
  clear "not found" message and takes no action.
- What happens when all items in a project are removed, reducing item count to zero? Percent-complete
  resets to `null` immediately.
- What happens when `today` and `this-week` are both set on an item? Both flags are independent;
  setting one does not clear the other.
- What happens when `todo visualize` is called while a local server is already running on the same
  port? The system prints a clear error message and exits. Automatic fallback to an alternate port
  is out of scope for Phase 1.
- What happens when free text contains a name shared by a lane, project, and item? The system
  infers the target level from context phrasing; if still ambiguous, it asks for clarification.
- What happens when the GUI is open and the data store is externally deleted or corrupted? The GUI
  displays an appropriate empty or error state on the next refresh cycle.

## Requirements *(mandatory)*

### Functional Requirements

#### Data Store

- **FR-001**: The system MUST maintain a single shared data file as the sole persistent state store
  for all lanes, projects, and items.
- **FR-002**: The data file MUST be stored as human-readable, non-minified plain JSON.
- **FR-003**: All reads and writes to the data file MUST be performed exclusively through a shared
  core module. Neither the CLI nor the GUI may access the file directly.
- **FR-004**: Each **Lane** MUST store: a unique name, an ordered list of projects, and a file-system
  path to an associated Markdown instructions file. When a lane is created, the system MUST
  automatically create a blank Markdown file at a default path (e.g.,
  `~/.todo-agent/lanes/<lane-name>.md`) and record that path. The system stores the path, not
  the file contents; the user edits the file manually afterwards.
- **FR-005**: Each **Project** MUST store: a name (unique within its lane), a status
  (`not-started` | `scheduled` | `in-progress` | `completed`), an importance score (integer 0–100,
  default 50), a start date (meaningful only when status is `scheduled`; otherwise null/unset), a
  computed percent-complete (see FR-007/FR-008), and an ordered list of timestamped notes.
  When a project's status changes away from `scheduled`, `start_date` is preserved in storage
  but carries no semantic meaning in that non-scheduled state.
- **FR-006**: Each **Item** MUST store: a title (unique within its project), a status
  (`not-started` | `in-progress` | `completed`), a `today` boolean (default `false`), a `this-week`
  boolean (default `false`), an optional deadline date, a push count integer (default `0`), and an
  ordered list of timestamped notes.
- **FR-007**: Project percent-complete MUST be automatically recalculated — as
  `floor(completed_items / total_items × 100)` — whenever any item within that project has its
  status changed. It is MUST NOT be directly settable by the user.
- **FR-008**: When a project has zero items, its percent-complete MUST be stored and returned as
  `null`, not `0`. It MUST be displayed as "—" or equivalent in any UI.

#### CLI Interface

- **FR-009**: The system MUST expose a CLI entry point (`todo`) that accepts arbitrary
  natural-language input as its primary argument (e.g., `todo "add a project called Q3 Review"`),
  as well as reserved subcommands (e.g., `todo visualize`).
- **FR-010**: Intent resolution MUST use an LLM to map free text to a specific action from a fixed,
  explicitly declared set of callable actions. The LLM MUST NOT write directly to the data store.
- **FR-011**: The CLI MUST support adding a lane, project, or item, inferring the correct entity
  level from phrasing.
- **FR-012**: The CLI MUST support deleting a lane, project, or item with a mandatory confirmation
  prompt that names the entity and states the count of all child records that will be cascade-deleted.
  Deletion MUST cascade to all children. There is no "must be empty first" restriction.
- **FR-013**: The CLI MUST support changing the status of a project or item to any valid status value.
- **FR-014**: The CLI MUST support independently marking or unmarking an item's `today` and
  `this-week` flags.
- **FR-015**: The CLI MUST support setting an item's deadline to a specific date or clearing it.
- **FR-016**: The CLI MUST support setting a project's importance (0–100) and status, including
  `scheduled` with an associated start date.
- **FR-017**: The CLI MUST support appending a timestamped free-text note to a project or item,
  inferring the target from phrasing and data context. The CLI MUST also support listing all
  notes for a named project or item in chronological order, displaying each note's UTC timestamp
  and text. Note listing is a read-only operation and MUST NOT modify any data.
- **FR-018**: The CLI MUST support a `todo visualize` subcommand with an optional scope argument
  (`all`, `today`, `this-week`) — e.g., `todo visualize today` — that launches the GUI rather
  than printing to the terminal. This is a reserved subcommand, not processed by the LLM.
- **FR-019**: When the CLI cannot safely resolve ambiguous intent from data context, it MUST prompt
  the user for clarification rather than proceeding with a potentially destructive guess.

#### GUI Interface

- **FR-020**: The GUI MUST run exclusively on the user's local machine with no external hosting,
  public network access, or remote server required.
- **FR-021**: The GUI MUST display: lanes as top-level columns or sections; within each lane,
  projects as collapsible groups showing name, status, importance, and computed percent-complete;
  within each project, items as cards showing title, status, `today`/`this-week` flags, and deadline
  (if set). Notes are not displayed in the GUI in Phase 1; note interaction is CLI-only.
- **FR-022**: The GUI MUST support three view filters (`all`, `today`, `this-week`) switchable
  without re-launching. The `today` filter shows only items with `today: true`; the `this-week`
  filter shows only items with `this-week: true`.
- **FR-023**: The GUI MUST allow changing an item's or project's status directly in the view, with
  the change persisted to the shared data store immediately.
- **FR-024**: The GUI MUST allow deleting a lane, project, or item with a confirmation dialog that
  names the entity and states the count of cascade-deleted children — consistent with CLI delete
  behaviour.
- **FR-025**: The GUI MUST allow adding a new item to an existing project, a new project to an
  existing lane, and a new lane.
- **FR-026**: The GUI MUST automatically reflect changes made via the CLI without requiring a manual
  page reload. The maximum acceptable lag from CLI change to GUI update is 10 seconds.

#### Configuration

- **FR-027**: The system MUST read the data file path from a configuration file stored at a
  well-known location (e.g., `~/.todo-agent/config.json`). The user sets this path once during
  initial setup. The system uses this path for all reads and writes via the shared core module.

#### Lane Instructions File

- **FR-028**: Each lane's associated Markdown instructions file MUST be auto-created as a blank
  file at a default path when the lane is created, and that path recorded in the data store. The
  system reads the file as unstructured prose context (for future Phase 2 reminder logic); it
  MUST NOT attempt to parse it into structured fields. The user edits the file directly with any
  text editor.

#### Out of Scope — Phase 2 (MUST NOT be implemented in this build)

- **FR-OS-001**: No daily or weekly job to auto-increment push counts or migrate unfinished
  `today`/`this-week` items forward.
- **FR-OS-002**: No scheduler-driven reminder sending derived from lane instruction files.
- **FR-OS-003**: No SMS or push notification delivery.
- **FR-OS-004**: No logic that maps project importance to reminder frequency or tone.

### Key Entities

- **Lane**: Top-level grouping. Attributes: unique name, ordered list of projects, path to a
  Markdown instructions file.
- **Project**: Belongs to exactly one lane. Attributes: name (unique within lane), status,
  importance (0–100), start date (nullable), percent-complete (computed/nullable), notes list.
- **Item**: Belongs to exactly one project. Attributes: title (unique within project), status,
  `today` flag, `this-week` flag, deadline (nullable), push count, notes list.
- **Note**: An immutable timestamped text record. Appendable to projects or items; not editable
  or deletable in Phase 1.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can add a lane, project, and item each via a single natural-language command,
  with the correct entity appearing in the data store after each command — verifiable by reading the
  data file directly.
- **SC-002**: A delete confirmation prompt correctly names the target entity and states the exact
  count of all child records that will be removed, 100% of the time, before any data is deleted.
- **SC-003**: The GUI reflects any CLI-driven data change within 10 seconds without a manual page
  reload.
- **SC-004**: Project percent-complete is always consistent with the current item statuses: any item
  status change is reflected in a recalculated percent-complete within the same operation, verifiable
  by reading the data store immediately after.
- **SC-005**: A completely unambiguous natural-language command is actioned without any clarification
  prompt; a genuinely ambiguous command (e.g., matching two distinct items by name) always triggers a
  clarification request — never a silent destructive guess.
- **SC-006**: The data file remains valid, human-readable JSON after any sequence of CLI and GUI
  operations — verifiable by opening the file in a text editor and parsing it with a standard JSON
  tool.
- **SC-007**: All Phase 2 fields (`start_date` on projects, `importance` on projects, `push_count`
  on items, lane instructions file path) are present in the data store and individually settable via
  the CLI in Phase 1, even though no automated logic reads or acts on them.

## Assumptions

- The user operates a single CLI session and at most one browser GUI session at a time; concurrent
  multi-user or multi-session access is out of scope.
- The data file path is configured once in a small config file (e.g., `~/.todo-agent/config.json`).
  The system reads this config at startup. File relocation requires editing the config; no in-app
  migration tool is needed in Phase 1.
- When a lane is created, the system automatically creates a blank Markdown instructions file at a
  default path (e.g., `~/.todo-agent/lanes/<lane-name>.md`). The user then populates that file
  manually using any text editor; the system does not modify it after creation.
- Lane names are unique across the entire data store. Project names are unique within a lane. Item
  titles are unique within a project. Duplicate names at the same level are treated as an error.
- Sensible defaults are applied when not specified: importance defaults to 50 for new projects;
  `today` and `this-week` default to `false`; push count defaults to `0`; deadline defaults to unset.
- The GUI refresh interval (for live updates) is a short fixed value; user-configurable intervals
  are out of scope for Phase 1.
- `todo visualize` binds to a fixed default local port. A port conflict results in a clear error
  message; automatic fallback to an alternate port is a nice-to-have, not a requirement.
- Push count is visible and manually settable in Phase 1, but it is never auto-incremented; that
  logic is reserved for Phase 2.

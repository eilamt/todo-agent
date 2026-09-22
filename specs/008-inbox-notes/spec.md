# Feature Specification: Inbox Notes

**Feature Branch**: `008-inbox-notes`

**Created**: 2026-09-22

**Status**: Draft

**Input**: User description: "Inbox feature: a collection of markdown notes (.md files) stored in ~/.todo-agent/inbox/. Each note has a title and a body. Notes can be promoted to create new projects, new items, or append notes to existing projects, guided by a structured '## Promote to' section written by the user inside the note. After promotion the note is marked promoted."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Capture an Idea as an Inbox Note (Priority: P1)

A user has a new idea that is not ready to be a project or task. They create an inbox note — giving it a title and a freeform description — so the idea is captured and visible without cluttering the project board.

**Why this priority**: Capture is the entry point of the whole Inbox feature. Without it, nothing else is possible. It is also the highest-frequency action.

**Independent Test**: Run the CLI to add a note with a title and body. Open the GUI Inbox tab — the note appears with its title. No projects or items are created. This is fully testable as a standalone slice.

**Acceptance Scenarios**:

1. **Given** a user runs the CLI command to add a note with a title and body, **When** the command succeeds, **Then** a new `.md` file appears in `~/.todo-agent/inbox/` containing the title (in YAML frontmatter) and body text, with `promoted: false` in frontmatter.
2. **Given** a user drops a hand-written `.md` file with valid frontmatter into `~/.todo-agent/inbox/`, **When** the GUI or CLI lists notes, **Then** the dropped file appears as an inbox note.
3. **Given** the GUI is open, **When** the user navigates to the Inbox tab, **Then** all notes (promoted and unpromoted) are listed, showing title and promoted status.
4. **Given** a note exists in the inbox, **When** the user asks the CLI to list inbox notes, **Then** each note's title and promoted status are shown.
5. **Given** the inbox directory does not yet exist, **When** the first note is created via CLI, **Then** the directory is created automatically and the note is saved successfully.

---

### User Story 2 — Promote an Inbox Note to the Project Board (Priority: P2)

A user has an inbox note with a `## Promote to` section describing which projects and items to create or update. They ask the agent to promote the note. The agent reads the instructions, executes the actions (creating projects, items, or appending notes), and marks the note as promoted.

**Why this priority**: Promotion is the core value of the Inbox — it converts raw ideas into actionable board entries. Without it the inbox is just a scratch pad.

**Independent Test**: Create a note with a `## Promote to` section that references one existing project and one new project. Ask the agent to promote it. Verify the new project exists, the item was created, and the note is marked promoted (`promoted: true` in frontmatter). The original note file remains in the inbox directory.

**Acceptance Scenarios**:

1. **Given** a note with a `## Promote to` section naming an existing project and specifying text to add as a note, **When** the agent promotes the note, **Then** the specified text is appended as a note to that project.
2. **Given** a note with a `## Promote to` section naming a project that does not yet exist, **When** the agent promotes the note, **Then** the new project is created in the specified lane, and the specified content is added to it.
3. **Given** a note with a `## Promote to` section naming a new item to create in a project, **When** the agent promotes the note, **Then** the item is created in that project with the specified title (and optionally description).
4. **Given** a note with multiple targets in the `## Promote to` section, **When** the agent promotes it, **Then** all targets are processed — new projects and items are created, notes are appended — in a single promotion action.
5. **Given** the agent has promoted a note, **When** the user views the Inbox tab or lists notes via CLI, **Then** the note is shown with a "promoted" badge/status and `promoted: true` in its frontmatter.
6. **Given** a note that is already marked promoted, **When** the user asks the agent to promote it again, **Then** the agent warns that the note is already promoted and requires explicit confirmation before re-promoting.

---

### User Story 3 — View and Browse Inbox Notes (Priority: P3)

A user wants to review what ideas they have captured — both unpromoted and already-promoted — from the GUI Inbox tab and from the CLI.

**Why this priority**: Browsing completes the read side of the inbox. It is lower priority than capture and promotion because the list view in US1 already provides basic visibility; this story adds richer inspection (viewing full note content).

**Independent Test**: With several notes in the inbox (some promoted, some not), open the Inbox tab in the GUI. Verify notes are listed with title and promoted status. Click or select a note to view its full body. This is testable independently of promotion logic.

**Acceptance Scenarios**:

1. **Given** notes exist in the inbox, **When** the user opens the Inbox tab, **Then** notes are shown with title and a clear promoted/unpromoted indicator, newest first.
2. **Given** a mix of promoted and unpromoted notes, **When** the user views the Inbox tab, **Then** promoted notes are visually distinguished (e.g., a badge or muted style) but still visible.
3. **Given** the user selects a note in the GUI, **When** the note detail is shown, **Then** the full body (markdown rendered) and the `## Promote to` section are visible.
4. **Given** the user runs the CLI command to view a specific note by title, **When** the command runs, **Then** the full note content is printed.

---

### Edge Cases

- What if a `## Promote to` section references a lane that does not exist? The agent asks the user to clarify or confirm creation of the new lane before proceeding.
- What if the note file is malformed (missing frontmatter, unreadable)? The note is silently skipped in listings; the user is notified only if they explicitly try to view or promote that note.
- What if two notes have the same title? Titles are not required to be unique — notes are identified by filename. The CLI and GUI display both.
- What if the `## Promote to` section is absent and the user asks to promote? The agent notifies the user that no promotion instructions were found and takes no action.
- What if promotion partially fails (e.g., one target project exists but another lane is missing)? The agent reports which actions succeeded and which failed; it does not mark the note as promoted until all targets are processed successfully.
- What if the inbox directory contains non-`.md` files? They are ignored.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST maintain a dedicated inbox directory where notes are stored as individual `.md` files, each with YAML frontmatter containing at minimum `title` and `promoted` (boolean) fields.
- **FR-002**: The user MUST be able to create an inbox note via CLI by providing a title and optional body text; the system creates the `.md` file automatically.
- **FR-003**: The inbox directory MUST be created automatically on first use if it does not already exist.
- **FR-004**: The system MUST accept hand-placed `.md` files in the inbox directory as valid notes (files placed there manually by the user are treated identically to CLI-created notes).
- **FR-005**: The CLI MUST provide a command to list all inbox notes, showing each note's title and promoted status.
- **FR-006**: The GUI MUST display an Inbox tab that lists all notes with title and promoted/unpromoted indicator.
- **FR-007**: When the user asks the agent to promote a note, the agent MUST read the `## Promote to` section and execute the described actions: creating new lanes (with confirmation), creating new projects, creating new items, and/or appending notes to existing projects.
- **FR-008**: After a successful promotion (all targets processed), the system MUST set `promoted: true` in the note's YAML frontmatter. The note file MUST remain in the inbox directory — it is never deleted.
- **FR-009**: If the `## Promote to` section is absent, promotion MUST be refused and the user notified.
- **FR-010**: If a note is already marked promoted, the agent MUST warn the user and require explicit confirmation before re-promoting.
- **FR-011**: Promotion MUST be atomic with respect to the promoted flag: the flag is set only after all target actions complete successfully. A partial failure leaves the note unmarked and reports which actions failed.
- **FR-012**: The CLI MUST provide a command to view the full content of a specific note by title.
- **FR-013**: The GUI MUST visually distinguish promoted notes from unpromoted notes (e.g., a badge or style difference).

### Key Entities

- **Inbox Note**: A markdown file with YAML frontmatter (`title`, `promoted`, optional `created_at`) and a freeform body. The body MAY contain a `## Promote to` section with structured routing instructions.
- **Promote-to Section**: A named section within a note's body that lists target lanes, projects, items, and/or note text to be created or appended on the project board. The exact format is user-authored prose; the agent interprets it via LLM reasoning.
- **Inbox Directory**: The folder on disk that contains all inbox note files (`~/.todo-agent/inbox/`). It is the single source of truth for inbox state.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can capture a new idea as an inbox note in under 30 seconds using the CLI.
- **SC-002**: 100% of notes listed in the GUI Inbox tab accurately reflect the files present in the inbox directory at the time of the request.
- **SC-003**: A promotion that targets 3 or fewer board actions (create project, create item, append note) completes in a single agent interaction without requiring follow-up commands.
- **SC-004**: After a successful promotion, the note's `promoted: true` status is immediately visible in both the CLI and the GUI without requiring a manual refresh.
- **SC-005**: Zero notes are deleted or lost as a result of promotion — the note file always remains in the inbox directory.
- **SC-006**: A hand-placed `.md` file with valid frontmatter appears in the inbox listing within the next GUI poll cycle (≤ 5 seconds) without any additional user action.

---

## Assumptions

- The inbox directory path is fixed at `~/.todo-agent/inbox/` and is not user-configurable in this version.
- Note filenames are auto-generated from the title (slugified, e.g., `my-great-idea.md`) when created via CLI; hand-placed files retain their original filename.
- The `## Promote to` section is freeform prose authored by the user; the agent uses LLM reasoning to interpret which projects/items/notes to create. No rigid sub-format (e.g., bullet syntax) is required.
- Promoted notes are never automatically hidden or deleted; the user must manually delete a note file if they want to remove it from the inbox.
- The GUI Inbox tab uses the same polling mechanism as the board (every 5 seconds) to detect new or changed note files.
- Creating a new lane via promotion requires user confirmation (to align with Principle VII — destructive/significant actions need explicit user intent); creating projects and items does not.
- Note bodies support full markdown syntax; the GUI renders them as formatted markdown.
- `created_at` in frontmatter is set automatically at note creation time (ISO 8601 timestamp); hand-placed files without this field are treated as having an unknown creation date and sorted to the end.

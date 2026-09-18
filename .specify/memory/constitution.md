<!--
SYNC IMPACT REPORT (remove before committing)
=============================================
Version change:     N/A (initial population) → 1.0.0
Bump type:          MAJOR / initial — template placeholders replaced with real governance content
Modified sections:
  - [PROJECT_NAME] → "To-Do Agent"
  - All 5 placeholder principles expanded to 7 concrete principles
  - [SECTION_2_NAME] → "Scope Boundaries"
  - [SECTION_3_NAME] → "Quality Standards"
  - [GOVERNANCE_RULES] → full amendment procedure
  - All date/version tokens resolved
Added:              Principles VI (Staged Scope) and VII (User Stays in Control) beyond template's 5-slot scaffold
Removed:            All HTML example comments (replaced by real content)
Deferred TODOs:     None — all placeholders resolved from user input
-->

# To-Do Agent Constitution

## Core Principles

### I. Local-First, No Hosting

All application data MUST reside in a local file on the user's machine. The system MUST NOT
require any server, cloud service, or external host to operate. Any future networked feature
(e.g., SMS reminders) is an explicit opt-in add-on and MUST NOT be a dependency of the core
system. The system MUST remain fully operational with no internet connection.

**Rationale**: User data sovereignty and zero-dependency operation are non-negotiable for a
personal productivity tool. The user owns their data and controls its location at all times.

### II. Single Source of Truth for State

All reads and writes to the data store MUST be routed through one shared core module. The CLI
and the GUI are thin front ends that call the same core functions — neither is permitted to
access the data file directly. This MUST be enforced at the architectural level, not by
convention alone.

**Rationale**: Two interfaces touching the same file independently will eventually produce
inconsistent state. A single access layer makes bugs locatable, writes serialisable, and
the system auditable.

### III. Deterministic Core, Generative Edges

Free-text intent parsing is the ONLY part of the system that MAY invoke an LLM. Once a
user's natural-language input is resolved to a specific function call, all subsequent
processing MUST be plain, deterministic, testable code. An LLM MUST NOT write directly to
the data store; it MUST select exclusively from a fixed, explicitly declared set of
tool/function call signatures.

**Rationale**: Non-deterministic code paths make behaviour unpredictable and testing
impractical. Confining generative AI to the intent-resolution boundary keeps the rest of the
system reliable and independently verifiable.

### IV. Simplicity Over Frameworks

The project MUST NOT introduce agent orchestration frameworks (LangChain, CrewAI, or
equivalents) or a database engine without a specific, documented concrete need. The standard
library and a minimal set of well-understood dependencies are preferred. A single JSON file
is the correct and sufficient data store for this project's current scale. SQLite or any
relational/document database MUST NOT be introduced unless a specific, documented bottleneck
makes the JSON file inadequate.

**Rationale**: Frameworks and databases add hidden behaviour, surface area, and maintenance
burden. The simplest solution that satisfies the requirement is the correct solution until
evidence demands otherwise.

### V. Human-Readable State

The data store MUST remain plain JSON — not a binary format, not a minified or compressed
representation — such that the user can open and understand it with any text editor. Lane-level
instructions MUST remain plain Markdown that the user can hand-edit without any application
tooling.

**Rationale**: If the application stops working, the user's data must still be accessible and
interpretable. A human-readable data store is also a debuggable one.

### VI. Staged Scope

This project is built in two explicit phases:

- **Phase 1 (current build):** Fully local CLI with free-text intent parsing backed by the LLM
  tool-call pattern, plus an interactive local web GUI with live updates.
- **Phase 2 (explicitly out of scope for this build):** Daily scheduler, push-count tracking on
  missed items, and SMS reminders via a provider such as Twilio, with reminder frequency and tone
  driven by per-project importance scores.

Phase 2 components MUST NOT be implemented in this build. The data schema MAY include fields that
anticipate Phase 2 (they may sit unused), but no scheduler process, cron job, or SMS/push
integration MUST be implemented in Phase 1.

**Rationale**: Building to an explicit scope boundary prevents creep and keeps Phase 1 shippable
and reviewable on its own terms. Schema anticipation avoids costly future migrations without
incurring implementation cost today.

### VII. User Stays in Control

Destructive actions — deleting a lane, a project, or an item — MUST require explicit user
confirmation before execution, regardless of whether the triggering input originates from the CLI,
free-text parsing, or the GUI. No destructive action may be silently irreversible.

**Rationale**: A productivity tool that silently destroys user data is not trustworthy. A
mandatory confirmation step is a small, consistent cost that prevents potentially unrecoverable
losses.

## Scope Boundaries

The Phase 1 build is bounded to the following deliverables:

- A shared core module that owns all data-store access (reads and writes).
- A CLI interface with free-text intent parsing using the LLM tool-call pattern.
- An interactive local web GUI with live updates (no external hosting required).
- A plain-JSON data store with a schema that anticipates Phase 2 fields (unused in Phase 1).

The following are explicitly **out of scope** for Phase 1 and MUST NOT be implemented:

- Any scheduler, cron job, or background daemon process.
- SMS or push notification integration (e.g., Twilio or equivalent).
- Push-count or missed-item tracking logic.
- Reminder frequency or tone configuration driven by importance scores.
- Any cloud storage, sync, or remote-hosting mechanism.

## Quality Standards

- Every function in the core module MUST be independently unit-testable with deterministic inputs
  and outputs.
- The LLM intent-resolution layer MUST be isolated behind an interface or adapter so it can be
  stubbed or mocked in tests without network calls.
- The CLI and GUI MUST each be exercisable without a real on-disk data file (via the core module's
  interface).
- All confirmed-destructive actions MUST have at least one automated test covering the
  confirmation path and one covering the cancellation/abort path.
- No new dependency may be added without documenting the specific need it addresses and confirming
  that no standard-library equivalent exists.

## Governance

This constitution supersedes all other project conventions and informal practices. Any amendment
MUST follow this procedure:

1. **Document** the rationale for the proposed change.
2. **Classify** the version bump: MAJOR for principle removals or incompatible redefinitions;
   MINOR for new principles, new sections, or materially expanded guidance; PATCH for
   clarifications, wording fixes, or non-semantic refinements.
3. **Increment** `CONSTITUTION_VERSION` accordingly.
4. **Update** `Last Amended` to the date of the change (ISO 8601: YYYY-MM-DD).
5. **Record** a `SYNC IMPACT REPORT` comment in the amended file for human review before
   committing.

All implementation decisions MUST be validated against the principles above before merging.
Complexity MUST be justified against Principle IV. Any scope addition MUST be evaluated against
Principle VI. Code reviews MUST treat violations of these principles as blocking issues.

**Version**: 1.0.0 | **Ratified**: 2026-09-17 | **Last Amended**: 2026-09-17

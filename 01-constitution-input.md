Create a constitution for a personal, local-first to-do agent with these principles:

1. **Local-first, no hosting.** All data lives in a local file on the user's machine. Nothing is deployed, nothing requires a server the user doesn't control. Any future networked feature (SMS reminders) is an explicit opt-in add-on, not a dependency of the core system.

2. **Single source of truth for state.** All reads and writes to the data store happen through one shared core module. The CLI and the GUI are both thin front ends that call the same functions — neither is allowed to touch the data file directly. This guarantees the two interfaces can never drift apart or corrupt state with conflicting writes.

3. **Deterministic core, generative edges.** Free-text understanding (turning "move the budget task to today" into a structured action) is the only part of the system that goes through an LLM. Once intent is resolved into a specific function call, everything after that point is plain, deterministic, testable code. Never let an LLM write directly to the data store — it selects from a fixed, explicit set of tool/function calls.

4. **Simplicity over frameworks.** No agent orchestration frameworks (LangChain, CrewAI, etc.) and no database engine beyond what the project actually needs at its current scale. Prefer the standard library and a small number of well-understood dependencies. A single JSON file is the correct data store for this project's scale — do not introduce SQLite or a database unless a documented, concrete need arises.

5. **Human-readable state.** The data store must remain something the user could open and read directly if needed (plain JSON, not a binary format), and lane-level instructions must remain plain Markdown the user can hand-edit.

6. **Staged scope.** This is a two-phase project. Phase 1 (this build) is fully local: CLI with free-text parsing, and an interactive local web GUI with live updates. Phase 2 (explicitly out of scope for this build) adds a daily scheduler, push-count tracking on missed items, and SMS reminders via a provider like Twilio, with reminder frequency and tone driven by each project's importance score. Do not build phase 2 components now; the schema should anticipate them (fields can exist and sit unused) but no scheduler process, cron job, or SMS integration should be implemented in this pass.

7. **User stays in control.** Destructive actions (delete lane, delete project, delete item) should be confirmable, not silently irreversible, whether triggered via free text or the GUI.

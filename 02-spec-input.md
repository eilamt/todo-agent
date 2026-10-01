Build a personal to-do management agent with two interfaces — a command-line natural-language interface, and a local interactive graphical view — sharing one underlying data store.

## Data model

**Lane** — a top-level grouping (e.g. "Work", "Personal", "Health"). Each lane has:
- A name.
- A collection of projects.
- An associated Markdown file containing free-text instructions written by the user: when and how they want to be reminded about this lane (e.g. "weekends only", "every day at 9am"), how reminder frequency/tone should map to a project's importance score, and optional links to related knowledge bases or assets. This file is read by the agent as context, not parsed into rigid fields — it stays human-editable prose (optionally with a small structured header if that helps the agent resolve it reliably).

**Project** — belongs to exactly one lane. Each project has:
- A name.
- Status: one of `not-started`, `scheduled`, `in-progress`, `completed`.
- Start date: only meaningful when status is `scheduled`; unset otherwise. When a project's start date arrives, it should be eligible for a reminder (reminder *sending* is phase 2 — for now, just make sure the field exists and a scheduler could compute "which scheduled projects are due today").
- Importance: an integer 0–100, default not specified by the user unless given (pick a sensible default, e.g. 50). Higher means more important. This value is not acted on yet (no reminders exist yet) — it just needs to be stored and settable, since it will drive reminder frequency/tone in a later phase.
- Percent complete: NOT set directly by the user. Automatically computed as (number of completed items ÷ total items) × 100, recalculated whenever any item's status changes. If a project has zero items, percent complete is `null` (displayed as "—" or similar), not zero — this distinguishes "nothing to do yet" from "0% done."
- Notes: a list of free-text notes with timestamps, addable and viewable but not required to be editable/deletable in v1 beyond appending.

**Item** — belongs to exactly one project. Each item has:
- A title.
- Status: one of `not-started`, `in-progress`, `completed`.
- `today`: boolean, default false. Marks the item as something to work on today.
- `this-week`: boolean, default false. Marks the item as something to work on this week.
- Deadline: optional date, unset by default.
- Push count: integer, default 0. Intended to track how many times this item has been carried over while still flagged `today` or `this-week` and incomplete (the actual daily increment job is phase 2 — for now just include the field, default 0, and make it visible/settable so the mechanism can be added later without a schema change).
- Notes: same shape as project notes — free-text, timestamped, appendable.

## Interface 1: Command-line, natural language

A single command (e.g. `todo "<free text>"`) takes an arbitrary natural-language instruction and performs the corresponding action(s) against the shared data store. It must support, at minimum:

- Adding a lane, project, or item (inferring the right level from phrasing, e.g. "add a new lane called Health" vs. "add a task to the budget project called Q3 review").
- Deleting a lane, project, or item, with a confirmation step before destructive deletes. If the thing being deleted still contains children (a lane with projects, a project with items), the confirmation prompt must state how many projects/items will be removed as a result before the user confirms — deletion then cascades to all of them. There is no "must be empty first" restriction.
- Changing an item's or project's status.
- Marking/unmarking an item as `today` or `this-week`.
- Setting an item's deadline.
- Setting a project's importance or status (including `scheduled` with a start date).
- Adding a free-text note to a project or an item (the system should infer which, from context and phrasing — e.g. "note on the budget project: waiting on finance" vs. "note on the review task: sent draft").
- Triggering the visualization (`\visualize` or similar), optionally scoped to `all`, `today`, or `this week` — this opens the GUI (see below) rather than printing to the terminal.

Ambiguous free text should be resolved using the current state of the data (lane/project/item names) as context, so the user doesn't need to give exact IDs — but if the system genuinely cannot resolve what's meant, it should ask for clarification rather than guessing destructively.

## Interface 2: Local interactive visualization

Triggered by the `\visualize` command (with `all` / `today` / `this-week` view options). This launches a local web application (not hosted publicly — runs only on the user's own machine) and opens it in the default browser.

Layout: lanes shown as columns/sections; within each lane, projects shown as collapsible groups (showing name, status, importance, computed percent-complete); within each project, items shown as cards (showing title, status, today/this-week flags, deadline if set). The view filter (all/today/this-week) restricts which items are shown, consistent with the CLI's filter options.

Interactivity required in this view:
- Change an item's or project's status directly from the UI.
- Delete an item, project, or lane directly from the UI (with confirmation that states how many child projects/items will be cascade-deleted, consistent with the CLI's delete behavior).
- Add a new item (and ideally project/lane) directly from the UI.

Live updates: if the CLI is used to change data while the GUI is open, the GUI should reflect those changes without the user needing to manually reload the page (polling the underlying state at a short interval is an acceptable implementation).

## Explicitly out of scope for this build (future phase)

- The daily/weekly job that increments push-count and actually migrates unfinished `today`/`this-week` items forward.
- Sending reminders on a schedule derived from each lane's Markdown instructions.
- SMS delivery (e.g. via Twilio) of a daily "here are today's items" message.
- Any mapping of project importance to reminder frequency/tone.

These should not block this build, but the data model above is intentionally already shaped to support them later without migration.

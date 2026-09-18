# Quickstart Validation Guide: Personal To-Do Agent

**Feature**: `specs/001-todo-agent`
**Date**: 2026-09-17

This guide documents runnable validation scenarios that prove the feature works end-to-end.
It is not a full implementation guide — it describes what to run and what to expect.
See `data-model.md` for schema details and `contracts/` for interface contracts.

---

## Prerequisites

- Python 3.11+ installed (`python3 --version`)
- An Anthropic API key set as `ANTHROPIC_API_KEY` environment variable
- The package installed in development mode (`pip install -e .`)
- `~/.todo-agent/config.json` written on first run (or created manually):
  ```json
  { "data_file": "~/.todo-agent/todos.json", "model": "claude-haiku-3" }
  ```

---

## Scenario 1: First Run — Empty State

**Purpose**: Confirm setup, config file creation, and empty data store initialisation.

```bash
todo "list everything"
```

**Expected**:
- `~/.todo-agent/` directory created if absent.
- `~/.todo-agent/config.json` written with defaults.
- `~/.todo-agent/todos.json` created with `{ "version": "1", "lanes": [] }`.
- CLI prints a message indicating no lanes exist yet.

**Verify**:
```bash
cat ~/.todo-agent/todos.json
# should print: {"version": "1", "lanes": []}
```

---

## Scenario 2: Add Lane, Project, Item

**Purpose**: Validate the three add operations and the auto-creation of the lane
instructions file.

```bash
todo "add a new lane called Work"
todo "add a project to Work called Website Redesign"
todo "add a task to Website Redesign called Design homepage"
```

**Expected after each command**:
1. Lane "Work" in `todos.json`; `~/.todo-agent/lanes/work.md` created (blank).
2. Project "Website Redesign" nested under "Work"; `percent_complete: null`.
3. Item "Design homepage" nested under "Website Redesign"; status `not-started`;
   `today: false`; `this_week: false`; `push_count: 0`.

**Verify**:
```bash
cat ~/.todo-agent/todos.json | python3 -m json.tool
ls ~/.todo-agent/lanes/
# should list: work.md
```

---

## Scenario 3: Status Change and Percent-Complete Recalculation

**Purpose**: Validate item status update triggers project percent-complete recalculation.

```bash
todo "add a task to Website Redesign called Write copy"
todo "mark Design homepage as done"
```

**Expected**:
- "Design homepage" status → `completed`.
- "Website Redesign" `percent_complete` → `50` (1 of 2 items complete).

```bash
todo "mark Write copy as done"
```

**Expected**:
- `percent_complete` → `100` (2 of 2 complete).

**Verify** by reading `todos.json` after each command.

---

## Scenario 4: Today and This-Week Flags

**Purpose**: Validate flag toggling and independence.

```bash
todo "move Design homepage to today"
todo "mark Design homepage as this week"
```

**Expected**: `today: true`, `this_week: true` (both set independently).

```bash
todo "remove Design homepage from today"
```

**Expected**: `today: false`, `this_week: true` (this_week unchanged).

---

## Scenario 5: Deadline and Importance

```bash
todo "set deadline on Design homepage to 2026-10-15"
todo "set importance of Website Redesign to 85"
```

**Expected**:
- Item `deadline: "2026-10-15"`.
- Project `importance: 85`.

---

## Scenario 6: Notes

```bash
todo "note on the Website Redesign project: kickoff call done"
todo "note on the Design homepage task: wireframes shared with client"
```

**Expected**:
- Project `notes` array has one entry: `{ "text": "kickoff call done", "created_at": "<ISO timestamp>" }`.
- Item `notes` array has one entry with the wireframes text.

---

## Scenario 7: Scheduled Project

```bash
todo "schedule Website Redesign to start on 2026-10-01"
```

**Expected**:
- Project `status: "scheduled"`, `start_date: "2026-10-01"`.

---

## Scenario 8: Ambiguity Handling

**Setup**: Add a second project with an identically-named item.

```bash
todo "add a project to Work called Budget"
todo "add a task to Budget called Review"
todo "add a project to Work called Finance"
todo "add a task to Finance called Review"
todo "mark Review as done"
```

**Expected**: CLI prints a clarification question naming both matches (e.g., "Did you mean
'Review' in Budget or 'Review' in Finance?") and exits without modifying any data.

---

## Scenario 9: Delete with Cascade Confirmation

```bash
todo "delete the Work lane"
```

**Expected CLI output** (before any deletion):
```
This will permanently delete 'Work', 2 projects, and N items. Confirm? (y/n):
```

- Type `n` → no data changed; cancellation message printed.
- Type `y` → lane and all contents removed; `todos.json` has empty `lanes` array.

---

## Scenario 10: GUI Launch and Live Sync

**Step 1** — Populate data (re-run Scenario 2 if needed), then:

```bash
todo visualize
```

**Expected**:
- Local web server starts on the configured port.
- Default browser opens to `http://127.0.0.1:<PORT>`.
- Lanes appear as columns; projects as collapsible groups showing name, status, importance,
  and percent-complete; items as cards showing title, status, today/this-week flags, deadline.

**Step 2** — While GUI is open, run a CLI command in a separate terminal:

```bash
todo "add a task to Website Redesign called Final QA"
```

**Expected**: Within 10 seconds, the GUI shows "Final QA" without a manual reload.

**Step 3** — In the GUI, change "Design homepage" status via its dropdown.

**Expected**: `todos.json` is updated immediately; the next CLI command reads the new status.

**Step 4** — Test view filters in the GUI.

```bash
todo "move Final QA to today"
```

Switch the GUI to "Today" view — only "Final QA" should appear.
Switch to "This Week" view — depends on flags set in earlier scenarios.
Switch to "All" — all items restored.

---

## Scenario 11: GUI Delete with Confirmation

In the GUI, click the delete button on a project that has items.

**Expected**: A modal dialog appears naming the project and stating the item count (e.g.,
"Delete 'Budget'? This will also delete 1 item. Confirm?").

- Click Cancel → no data changed.
- Click Confirm → project and items removed; GUI updates immediately.

---

## Scenario 12: todo visualize with Scope

```bash
todo visualize today
todo visualize this-week
todo visualize all
```

**Expected**: Each opens the GUI (or navigates the already-open browser) to the specified
filter view. Items shown match the filter: `today` → `today: true` items; `this-week` →
`this_week: true` items; `all` → all items.

---

## Validation Checklist

Run through all scenarios and confirm:

- [ ] S1: Config and data file auto-created on first run
- [ ] S2: Lane, project, item add correctly; instructions file created
- [ ] S3: `percent_complete` recalculates correctly (50 → 100)
- [ ] S4: `today` and `this_week` toggle independently
- [ ] S5: `deadline` and `importance` stored correctly
- [ ] S6: Notes appended with timestamps; not modifiable
- [ ] S7: `status: scheduled` with `start_date` stored
- [ ] S8: Ambiguous command triggers clarification, no data modified
- [ ] S9: Delete shows correct cascade count; cancel preserves data; confirm deletes
- [ ] S10: GUI reflects CLI changes within 10 seconds; GUI writes persist to data store
- [ ] S11: GUI delete shows count-aware confirmation modal
- [ ] S12: `todo visualize [scope]` opens GUI with correct filter

All scenarios passing = feature complete.

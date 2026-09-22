# Quickstart Validation Guide: Deadline Auto-Flags

## Prerequisites

```bash
cd /path/to/todo-agent
source .venv/bin/activate   # or however the project venv is activated
```

## Scenario S1 — Today flag auto-set from deadline

**Setup**: Create an item with `deadline = today's date` and `today = False`.

```bash
# Using CLI (substitute today's actual date)
todo add item "Buy groceries" to project "Personal" in lane "Home" deadline 2026-09-18
```

**Expected**: Item appears in Today tab without any manual flag toggle. Confirm via GUI Today tab or:

```bash
todo list items in project "Personal"
# → Item shows today: true
```

**Teardown**: Remove deadline or delete item.

---

## Scenario S2 — This-week flag auto-set from deadline

**Setup**: Create an item with a deadline on any day of the current Mon–Sun week that is NOT today.

```bash
todo add item "Team standup prep" to project "Work" in lane "Office" deadline 2026-09-19
```

**Expected**: Item appears in This Week tab. Does NOT appear in Today tab (unless deadline equals today).

---

## Scenario S3 — Deadline equals today → appears in BOTH tabs

**Setup**: Item with `deadline = today`.

**Expected**: Item appears in Today tab AND This Week tab simultaneously.

---

## Scenario S4 — Manually-set flags are preserved

**Setup**: Create an item with no deadline but `today = True` (set manually).

```bash
todo set today for item "Stand-up notes" in project "Work"
```

Remove the deadline (or ensure it was never set). Reload the app.

**Expected**: Item still appears in Today tab. Auto-flag computation must not have cleared the manual flag.

---

## Scenario S5 — Overdue deadline: no auto-flag

**Setup**: Create an item with `deadline = yesterday`.

```bash
todo add item "Overdue task" to project "Personal" in lane "Home" deadline 2026-09-17
```

**Expected**: Item does NOT appear in Today tab or This Week tab solely due to deadline. Manually-set flags still work normally.

---

## Scenario S6 — Next-week deadline: no auto-flag

**Setup**: Create an item with a deadline one week from today (next Mon–Sun week).

**Expected**: Item does NOT appear in This Week tab.

---

## Scenario S7 — Malformed deadline: no error, no flag

**Setup**: Directly edit `~/.todo-agent/data.json` and set an item's `deadline` to `"not-a-date"`.

**Expected**: App loads without error. Item is unaffected (no flags auto-set). Malformed value is silently ignored.

---

## Running the Unit Test Suite

```bash
pytest tests/unit/test_deadline_flags.py -v
```

All tests must pass. Then run the full suite to confirm no regressions:

```bash
pytest -v
```

Expected: all existing tests still pass.

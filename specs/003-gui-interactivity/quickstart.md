# Quickstart: GUI Inline Editing Validation

## Prerequisites

- `pip install -e .` completed
- At least one lane with one project and one item in the data store

**Seed data** (if starting fresh):
```bash
todo "add lane Work"
todo "add project Website to lane Work"
todo "add item Design homepage to project Website"
todo "add item Write copy to project Website"
```

## Start the GUI

```bash
todo visualize
```

The board opens at `http://127.0.0.1:517x/`.

---

## Scenario 1: Edit item title inline

1. Click the text "Design homepage" on the item card.
2. The title becomes an editable text input pre-filled with "Design homepage".
3. Type "Redesign homepage" and press Enter.
4. **Expected**: The card now shows "Redesign homepage". No page reload required.
5. Reload the page. **Expected**: Title is still "Redesign homepage" (persisted).

---

## Scenario 2: Set and clear item description inline

1. Click the description area below the title (or a "+" placeholder if no description exists).
2. Type "Needs mobile-first approach" and confirm (Enter or click outside).
3. **Expected**: The description appears below the title in a smaller grey text.
4. Click the description again, clear it with a clear button.
5. **Expected**: The description disappears from the card.

---

## Scenario 3: Set item importance and verify highlight

1. Click the importance badge (shows "50" by default).
2. Enter "90" and confirm.
3. **Expected**: The card gains a red left border and light pink background (importance > 80 highlight).
4. Set it back to "50".
5. **Expected**: The highlight disappears; badge shows "50".

---

## Scenario 4: Toggle today and this-week flags

1. Check the "today" checkbox on the "Write copy" item.
2. **Expected**: A "today" badge appears on the card immediately. No page reload required.
3. Uncheck the "today" checkbox.
4. **Expected**: The "today" badge disappears.
5. Toggle "this week" and verify the "this-week" badge behaves independently.

---

## Scenario 5: Set and clear deadline

1. Click the deadline field on an item.
2. Set a date (e.g., 2026-12-31).
3. **Expected**: A deadline badge appears on the card showing "2026-12-31".
4. Click the clear button next to the deadline.
5. **Expected**: The deadline badge disappears.

---

## Scenario 6: Edit project name and importance

1. Click the project name "Website" in the project header.
2. Type "New Website" and press Enter.
3. **Expected**: The project header now shows "New Website" in bold.
4. Click the importance value in the project header and change it to 80.
5. **Expected**: The meta display updates to show importance 80.

---

## Scenario 7: Collapse individual card and global collapse

1. Click the collapse toggle (▲/▼) on the "Redesign homepage" card.
2. **Expected**: All fields below the title disappear; only the title row is visible.
3. Click the toggle again. **Expected**: All fields reappear.
4. Click "Collapse all" in the page header.
5. **Expected**: All item cards on the board are collapsed (titles only visible).
6. Click "Expand all". **Expected**: All item cards expand.

---

## Scenario 8: Invalid input rejection

1. Click the item title, clear the field to blank, and press Enter.
2. **Expected**: The original title is restored; no save is sent to the server.
3. Click the importance badge, enter "200", and confirm.
4. **Expected**: The input is rejected (shown as invalid or clamped); no save is sent.

---

## Verification

After running all scenarios, inspect the data file:

```bash
cat ~/.todo-agent/data.json | python3 -m json.tool | grep -A 20 '"items"'
```

Confirm that `title`, `description`, `importance`, `today`, `this_week`, and `deadline` reflect the final saved values from the scenarios above.

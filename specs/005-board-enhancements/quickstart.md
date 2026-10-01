# Quickstart Validation Guide: Board Enhancements

**Date**: 2026-09-18

Use this guide to verify the three enhancements end-to-end after implementation.

## Prerequisites

1. The project is installed in development mode: `pip install -e ".[dev]"`
2. At least two lanes exist, each with at least two projects, each with at least one item.
   - Quick setup via CLI if needed:
     ```
     todo "add lane Work"
     todo "add lane Personal"
     todo "add project Website to Work"
     todo "add project Finance to Work"
     todo "add project Fitness to Personal"
     todo "add project Reading to Personal"
     todo "add item Fix login bug to Website"
     todo "add item Update docs to Finance"
     todo "add item Morning run to Fitness"
     ```
3. GUI is running: `todo gui` (opens at `http://127.0.0.1:5000`)

---

## S1: this_weekend flag via CLI

**Goal**: Verify `set_this_weekend` is wired end-to-end through the CLI agent.

```bash
todo "mark Fix login bug for this weekend"
```

**Expected**: Confirmation that the item was flagged.

```bash
todo "show me this weekend items"
```

**Expected**: "Fix login bug" appears in the response.

```bash
todo "remove Fix login bug from this weekend"
```

**Expected**: Confirmation that the flag was cleared.

---

## S2: this_weekend toggle in GUI

**Goal**: Verify the GUI checkbox and This Weekend tab.

1. Open `http://127.0.0.1:5000` in a browser.
2. Find the "Fix login bug" item card.
3. Check the **this weekend** checkbox.
4. Click the **This Weekend** tab in the header nav.

**Expected**: "Fix login bug" appears in the This Weekend tab view.

5. Uncheck the **this weekend** checkbox (switch back to All first).
6. Click the **This Weekend** tab again.

**Expected**: "Fix login bug" no longer appears.

---

## S3: this_weekend backward compatibility

**Goal**: Verify existing data without `this_weekend` loads cleanly.

1. Open `~/.todo-agent/data.json` in a text editor.
2. Find any item and manually remove the `this_weekend` key.
3. Reload `http://127.0.0.1:5000`.

**Expected**: Page loads without errors; removed-key item has its checkbox unchecked (defaults to false).

---

## S4: Lane drag-and-drop reorder

**Goal**: Verify dragging a lane column header changes the order and persists.

1. Note the current left-to-right lane order (e.g., Work | Personal).
2. Drag the **Personal** lane column header to the left of **Work**.

**Expected**: Board immediately shows Personal | Work.

3. Reload the page.

**Expected**: Order is still Personal | Work.

4. Drag **Personal** back to the right.

**Expected**: Board shows Work | Personal.

---

## S5: Lane drag-and-drop — no-op on invalid drop

**Goal**: Verify releasing a lane outside a valid drop zone is safe.

1. Start dragging the **Work** lane header.
2. Move it to the page `<header>` area and release.

**Expected**: Work lane returns to its original position. No console errors. No data change (reload confirms same order).

---

## S6: Project drag-and-drop reorder within a lane

**Goal**: Verify dragging a project card changes the order within a lane and persists.

1. In the **Work** lane, note the current top-to-bottom project order (e.g., Website above Finance).
2. Drag the **Finance** project card above **Website**.

**Expected**: Finance now appears above Website in the Work lane.

3. Reload the page.

**Expected**: Finance is still above Website.

---

## S7: Project drag-and-drop — no cross-lane move

**Goal**: Verify dragging a project card into a different lane is a no-op.

1. Start dragging the **Website** project card (in Work lane).
2. Hover over and release it on the **Personal** lane column.

**Expected**: Website returns to its original position in Work. Personal lane is unchanged. No console errors.

---

## S8: Unit test suite

```bash
pytest tests/test_this_weekend.py tests/test_reorder_lane.py tests/test_reorder_project.py -v
```

**Expected**: All tests pass.

---

## S9: Full regression check

```bash
pytest -v
```

**Expected**: All existing tests continue to pass alongside the new ones.

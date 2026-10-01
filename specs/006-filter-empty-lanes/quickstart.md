# Quickstart Validation Guide: Filter Empty Lanes

**Date**: 2026-09-20

Use this guide to verify the feature end-to-end after implementation.

## Prerequisites

1. GUI running: `todo gui` (opens at `http://127.0.0.1:5000`)
2. At least two lanes exist. One lane has an item with `today=True`; the other lane has no such items.
   - Quick setup via CLI if needed:
     ```
     todo "add lane Work"
     todo "add lane Personal"
     todo "add project Website to Work"
     todo "add project Fitness to Personal"
     todo "add item Fix login bug to Website"
     todo "mark Fix login bug for today"
     todo "add item Morning run to Fitness"
     ```

---

## S1: Empty lane hidden in Today tab

1. Open `http://127.0.0.1:5000`.
2. Click **Today** tab.

**Expected**: Only the **Work** lane is visible. **Personal** lane (no today items) is not rendered.

---

## S2: All tab still shows all lanes

1. While on the Today tab, click **All**.

**Expected**: Both **Work** and **Personal** lanes appear.

---

## S3: Lane reappears when an item is flagged

1. On the **Today** tab (only Work visible), switch to **All**.
2. Check the **today** checkbox on "Morning run" in Personal.
3. Switch back to **Today**.

**Expected**: Both **Work** and **Personal** lanes now appear (Personal has a matching item).

---

## S4: Lane disappears when last matching item is unflagged

1. On the **Today** tab (both lanes visible after S3), uncheck **today** on "Morning run".
2. Wait for the next poll cycle (up to 5 seconds) or toggle away and back to the Today tab.

**Expected**: **Personal** lane disappears again.

---

## S5: This Week tab filters lanes correctly

1. Flag "Morning run" with `this_week=True` only (not today).
2. Click **This Week** tab.

**Expected**: **Personal** lane visible, **Work** lane hidden (no this-week items in Work).

---

## S6: This Weekend tab filters lanes correctly

1. Flag "Fix login bug" with `this_weekend=True`.
2. Click **This Weekend** tab.

**Expected**: **Work** lane visible, **Personal** lane hidden.

---

## S7: Empty board state (no matching items anywhere)

1. Clear all flags from all items.
2. Click **Today** tab.

**Expected**: No lanes rendered. Board area is empty (no error, no crash).

---

## S8: Regression — existing tests still pass

```bash
pytest -v
```

**Expected**: All tests pass (backend is unchanged).

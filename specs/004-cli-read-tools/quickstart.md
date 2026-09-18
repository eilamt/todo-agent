# Quickstart Validation Guide: CLI Multi-Tool Dispatch and Read Tools

## Prerequisites

- `ANTHROPIC_API_KEY` is set in the environment.
- `todo` CLI installed (`pip install -e .` from project root).
- A board with at least one lane, one project, and a few items (use the setup commands below).

## Test Board Setup

```bash
todo "add a lane called Work"
todo "add a project called Website to Work lane"
todo "add a project called API to Work lane"
todo "add an item called Homepage to Website project"
todo "add an item called About page to Website project"
todo "add an item called Auth endpoint to API project"
todo "mark Homepage as today"
todo "set deadline for About page to 2026-09-30"
```

---

## Scenario 1: Multi-Tool Dispatch — Compound Add Command

**Purpose**: Verify that a single compound command creates multiple entities.

```bash
todo "add a project called Mobile to Work lane and add three items: iOS app, Android app, and React Native"
```

**Expected outcome**:
- CLI prints three distinct "Added item" confirmation lines.
- All three items are visible in the GUI (`todo visualize`).
- Single CLI invocation — no second prompt required.

---

## Scenario 2: Multi-Tool Dispatch — Mixed Update Command

**Purpose**: Verify that multiple field updates complete in one turn.

```bash
todo "mark Homepage as in-progress and set its importance to 90"
```

**Expected outcome**:
- CLI prints both "Updated 'Homepage' status..." and "Importance for 'Homepage' set to 90."
- Both changes persist on reload of the GUI.

---

## Scenario 3: List Lanes

**Purpose**: Verify `list_lanes` read tool.

```bash
todo "what lanes do I have?"
```

**Expected outcome**:
- LLM response lists "Work" lane and the number of projects it contains.
- No GUI required to answer the question.

---

## Scenario 4: List Projects Filtered by Lane

**Purpose**: Verify `list_projects` with optional lane filter.

```bash
todo "list all projects in Work lane"
```

**Expected outcome**:
- LLM response lists Website, API, and Mobile (from the setup above) with their status and importance.
- Projects from other lanes (if any) are not shown.

---

## Scenario 5: List Items — All

**Purpose**: Verify `list_items` with no filter returns everything.

```bash
todo "show me all my tasks"
```

**Expected outcome**:
- LLM response lists Homepage, About page, Auth endpoint, iOS app, Android app, React Native.
- Each item shows its project and lane.

---

## Scenario 6: List Items — Today Filter

**Purpose**: Verify `list_items` filtered to today.

```bash
todo "what items are marked for today?"
```

**Expected outcome**:
- LLM response lists only "Homepage" (the only item flagged today in the test setup).
- Does not list About page, Auth endpoint, or the Mobile items.

---

## Scenario 7: Get Item — Full Detail

**Purpose**: Verify `get_item` returns complete item information.

```bash
todo "tell me everything about the About page task"
```

**Expected outcome**:
- LLM response includes: title "About page", project "Website", lane "Work", deadline "2026-09-30", status, importance, description (null), and any notes.

---

## Scenario 8: Get Item — Ambiguity

**Purpose**: Verify `get_item` handles ambiguous titles gracefully.

```bash
# First, create a duplicate title in a different project:
todo "add an item called Homepage to API project"

# Then query it:
todo "show me the Homepage item"
```

**Expected outcome**:
- LLM response reports that "Homepage" was found in two locations (Work/Website and Work/API).
- LLM asks the user to specify which one, or the user can rerun with project context.

---

## Scenario 9: Empty Board Query

**Purpose**: Verify read tools handle an empty board.

```bash
# Remove the data file or start fresh, then:
todo "what's on my board?"
```

**Expected outcome**:
- LLM response states there are no lanes or items yet.
- No crash or unhandled error.

---

## Scenario 10: Max Rounds Safety

**Purpose**: Verify the dispatch loop does not hang indefinitely.

This is validated by the unit tests (mock LLM returns infinite tool calls); no manual step needed.

**Expected test outcome**: After 10 rounds, `run_agent()` raises `ValueError` with a partial-results message and exits cleanly.

---

## Regression Check

After implementing this feature, run the full test suite to confirm no regressions:

```bash
python3 -m pytest tests/ -q
```

**Expected**: All 93 existing tests pass. New tests for read operations and multi-tool dispatch also pass.

# Quickstart Validation Guide: Inbox Notes

## Prerequisites

```bash
cd /path/to/todo-agent
source .venv/bin/activate
```

---

## Scenario S1 — Create an inbox note via CLI

```bash
todo inbox add "Lake Book Ideas" "Lots of ideas about my book project."
```

**Expected**:
- File `~/.todo-agent/inbox/lake-book-ideas.md` created with `promoted: false` frontmatter.
- CLI prints the note title and slug.

**Verify**:
```bash
cat ~/.todo-agent/inbox/lake-book-ideas.md
# → shows frontmatter + body
```

---

## Scenario S2 — List inbox notes via CLI

```bash
todo list inbox notes
```

**Expected**: Prints a list showing the note title and `[not promoted]` status.

---

## Scenario S3 — Hand-drop a note file

Create a file manually:
```bash
cat > ~/.todo-agent/inbox/hand-written.md << 'EOF'
---
title: Hand-Written Idea
promoted: false
---

This was placed manually.
EOF
```

```bash
todo list inbox notes
```

**Expected**: `Hand-Written Idea` appears in the list.

---

## Scenario S4 — View note content via CLI

```bash
todo get inbox note "Lake Book Ideas"
```

**Expected**: Full note body printed, including promoted status.

---

## Scenario S5 — Promote a note via CLI agent

Create a note with a `## Promote to` section:

```bash
todo inbox add "Sprint Planning" "Ideas for the next sprint.

## Promote to

Create a new item \"Define sprint goals\" in project \"Work\" in lane \"Active\".
Add a note to project \"Work\" in lane \"Active\": \"Sprint planning ideas from inbox note.\""
```

Then:
```bash
todo promote inbox note "Sprint Planning"
```

**Expected**:
- Agent reads the `## Promote to` section.
- Creates item `Define sprint goals` in project `Work`.
- Appends note to project `Work`.
- Marks the note as promoted (`promoted: true` in file).
- CLI confirms all actions taken.

**Verify**:
```bash
cat ~/.todo-agent/inbox/sprint-planning.md
# → promoted: true
todo list items in project Work
# → "Define sprint goals" appears
```

---

## Scenario S6 — Promoted note stays in inbox with badge

```bash
todo list inbox notes
```

**Expected**: `Sprint Planning` still listed, now with `[promoted]` status.

---

## Scenario S7 — GUI Inbox tab

1. Start the GUI: `todo gui`
2. Navigate to the **Inbox** tab.
3. **Expected**: All notes listed with title and promoted/unpromoted badge.
4. Click a note → full body displayed.
5. Promoted notes show a distinct visual indicator.

---

## Scenario S8 — Malformed note file silently skipped

```bash
echo "not valid frontmatter" > ~/.todo-agent/inbox/broken.md
todo list inbox notes
```

**Expected**: `broken.md` is skipped silently; other notes still listed; no error raised.

---

## Running Unit Tests

```bash
pytest tests/unit/test_inbox.py -v
pytest -v  # full suite — all existing tests must still pass
```

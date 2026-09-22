# Data Model: Inbox Notes

## New Storage Layer

Inbox notes are stored **separately from `data.json`** in `~/.todo-agent/inbox/`. No changes to the existing board schema.

---

## InboxNote (on-disk file format)

**File**: `~/.todo-agent/inbox/<slug>.md`

### Frontmatter (YAML subset)

```markdown
---
title: Lake Book Ideas
promoted: false
created_at: 2026-09-22T10:30:00Z
---
```

| Field        | Type              | Required | Description |
|--------------|-------------------|----------|-------------|
| `title`      | string            | yes      | Human-readable note title. Need not be unique (filename is the unique key). |
| `promoted`   | boolean           | yes      | `false` until the user promotes the note. Set to `true` by `mark_note_promoted`. Never automatically reset. |
| `created_at` | ISO 8601 datetime | no       | Set automatically at creation time. Hand-placed files without this field sort to the end. |

### Body

Everything after the closing `---` of the frontmatter block. Free-form markdown. May contain a `## Promote to` section.

### `## Promote to` Section (optional, within body)

User-authored freeform prose describing board actions to take on promotion. Interpreted by the LLM agent. No rigid sub-format enforced.

Example:
```markdown
## Promote to

Add a note to project "Lake Book" in lane "Writing" with: "Idea for chapter structure..."
Create a new item "Research comparable titles" in project "Lake Book".
Create a new project "Book Marketing" in lane "Business" and add a note: "Start thinking about...".
```

---

## InboxNote (in-memory representation)

Returned by `core/inbox.py` functions to callers (CLI, GUI server, agent tools).

```python
{
    "slug": "lake-book-ideas",          # derived from filename (without .md)
    "title": "Lake Book Ideas",         # from frontmatter
    "promoted": False,                  # from frontmatter
    "created_at": "2026-09-22T10:30:00Z",  # from frontmatter, or None
    "body": "Body text here...",        # full body string (includes ## Promote to)
}
```

---

## Inbox Directory

| Path | Role |
|------|------|
| `~/.todo-agent/inbox/` | Root directory; created on first `add_inbox_note` call |
| `~/.todo-agent/inbox/<slug>.md` | Individual note file |

**Invariants**:
- Only `.md` files are treated as notes; other files are ignored.
- Filenames are unique within the inbox directory.
- `promoted` in frontmatter is the authoritative source of promotion state — never derived from board state.
- Note files are never deleted by the application (user must delete manually).

---

## No Changes to Board Schema

`data.json` (`~/.todo-agent/data.json`) is unaffected by this feature. Inbox and board are independent storage systems.

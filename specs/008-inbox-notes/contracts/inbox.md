# Contracts: Inbox Notes

## LLM Tool Contracts (new tools added to `tools.py`)

Current tool count: 23. After this feature: **27**.

---

### `add_inbox_note`

Creates a new inbox note file.

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "title": {
      "type": "string",
      "description": "Title of the note. Becomes the frontmatter title and basis for the filename."
    },
    "body": {
      "type": "string",
      "description": "Full body text of the note (markdown). May include a '## Promote to' section."
    }
  },
  "required": ["title"]
}
```

**Returns**: `{ "slug": "...", "title": "...", "promoted": false, "created_at": "..." }`

**Errors**: ValueError if title is empty/whitespace.

---

### `list_inbox_notes`

Lists all inbox notes (titles, slugs, promoted status, created_at). Does not return note bodies.

**Input schema**:
```json
{
  "type": "object",
  "properties": {},
  "required": []
}
```

**Returns**: Array of `{ "slug", "title", "promoted", "created_at" }` objects, sorted newest-first (nulls last).

---

### `get_inbox_note`

Returns full content of a single note including body.

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "title": {
      "type": "string",
      "description": "Title of the note to retrieve (case-insensitive match)."
    }
  },
  "required": ["title"]
}
```

**Returns**: `{ "slug", "title", "promoted", "created_at", "body" }`

**Errors**: ValueError if no note with that title exists. If multiple notes share a title, returns the first match (slug is the true unique key; user can retry with a more specific title if needed).

---

### `mark_note_promoted`

Sets `promoted: true` in a note's frontmatter. Idempotent — safe to call on an already-promoted note.

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "title": {
      "type": "string",
      "description": "Title of the note to mark as promoted."
    }
  },
  "required": ["title"]
}
```

**Returns**: `{ "slug", "title", "promoted": true, "created_at" }`

**Errors**: ValueError if no note with that title exists.

---

## REST API Contracts (new routes in `gui/server.py`)

### `GET /api/inbox`

List all inbox notes (no bodies).

**Response 200**:
```json
[
  {
    "slug": "lake-book-ideas",
    "title": "Lake Book Ideas",
    "promoted": false,
    "created_at": "2026-09-22T10:30:00Z"
  }
]
```

**Errors**: None (empty array if inbox directory empty or missing).

---

### `POST /api/inbox`

Create a new inbox note.

**Request body**:
```json
{ "title": "My Idea", "body": "Optional body text..." }
```

**Response 201**: Full note object including slug.

**Response 400**: `{ "error": "title is required" }` if title missing/blank.

---

### `GET /api/inbox/<slug>`

Get full note content by slug.

**Response 200**: Full note object including body.

**Response 404**: `{ "error": "Note not found" }` if slug does not match any file.

---

### `PATCH /api/inbox/<slug>`

Update note fields. Currently only `promoted` is patchable (set to `true`).

**Request body**: `{ "promoted": true }`

**Response 200**: Updated note object (without body).

**Response 404**: Note not found.

**Response 400**: Invalid body.

---

## CLI Dispatch Additions (`cli/main.py`)

The agent already routes all user input through the LLM tool loop. No new CLI-specific dispatch is required — the four new tools (`add_inbox_note`, `list_inbox_notes`, `get_inbox_note`, `mark_note_promoted`) are automatically available in the tool loop.

The existing `cli/main.py` dispatch table handles tool results for printing. Add result-formatting branches for the four new tools.

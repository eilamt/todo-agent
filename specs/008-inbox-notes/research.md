# Research: Inbox Notes

## Decision 1: Storage format for inbox notes

**Decision**: One `.md` file per note in `~/.todo-agent/inbox/`, with a minimal YAML-subset frontmatter block (lines between `---` delimiters at the top of the file).

**Rationale**: Principle V (human-readable state). Plain markdown files are readable and editable in any text editor with zero tooling. One-file-per-note enables hand-dropping files into the directory (FR-004) and gives each note an independent mtime that could be used for future features.

**Alternatives considered**:
- Single JSON index file — rejected: breaks hand-drop use case; binary-like for large notes.
- SQLite — rejected: Principle IV prohibits a database without documented bottleneck.
- Single `.md` with dividers — rejected: adds complexity, hard to hand-edit individual notes.

---

## Decision 2: Frontmatter parsing — manual vs. PyYAML

**Decision**: Parse frontmatter manually using simple line splitting. The frontmatter schema is fixed and minimal (`title`, `promoted`, `created_at`), making a full YAML parser unnecessary.

**Rationale**: Principle IV (no new dependency without justification). The format is:
```
---
title: Some Title Here
promoted: false
created_at: 2026-09-22T10:30:00Z
---
```
Only string and boolean values are needed. A 10-line parser handles this correctly without PyPI.

**Parsing algorithm**:
1. If file starts with `---\n`, find the closing `---` line.
2. Split each frontmatter line on the first `:`, strip whitespace.
3. Coerce `promoted` to bool (`"true"` → `True`, anything else → `False`).
4. Everything after the closing `---` block is the body.

**Alternatives considered**:
- `python-frontmatter` (PyPI) — rejected: adds a dependency for trivial parsing.
- `PyYAML` — already available transitively (Flask pulls it) but coupling to transitive deps is fragile; manual parsing is safer.

---

## Decision 3: Filename generation

**Decision**: Slugify the note title (lowercase, spaces → hyphens, strip non-alphanumeric/hyphen characters). If the slug collides with an existing filename, append a short UUID suffix.

**Rationale**: Predictable, human-readable filenames. Hand-dropped files keep their original filenames.

**Slug algorithm**: `re.sub(r"[^a-z0-9-]", "", title.lower().replace(" ", "-"))` (same pattern already used in `add_lane` for instructions files).

---

## Decision 4: Promotion tool architecture

**Decision**: Four separate tools exposed to the LLM: `add_inbox_note`, `list_inbox_notes`, `get_inbox_note`, `mark_note_promoted`. The LLM agent orchestrates promotion by:
1. Calling `get_inbox_note` to read the full note including `## Promote to`.
2. Interpreting the section and calling existing tools (`add_project`, `add_item`, `add_project_note`, etc.).
3. Calling `mark_note_promoted` after all targets succeed.

**Rationale**: Consistent with Principle III (deterministic core, generative edges). The LLM is already the orchestrator for multi-step tool sequences. No new "meta-tool" pattern needed; reuses the existing agent loop. `mark_note_promoted` is a simple deterministic write.

**Alternatives considered**:
- A single `promote_inbox_note` tool that internally calls the LLM — rejected: violates Principle III (LLM would be inside a deterministic function), untestable.
- Returning `## Promote to` content as part of `list_inbox_notes` — rejected: bloats listing responses.

---

## Decision 5: GUI polling for inbox

**Decision**: Separate `GET /api/inbox` endpoint, polled by the frontend alongside the existing `GET /api/data` poll.

**Rationale**: Inbox notes live in a different storage layer (`.md` files, not `data.json`). Mixing them into `/api/data` would require `load_data()` to touch the filesystem outside its documented responsibility. A separate endpoint keeps concerns cleanly separated.

**Implementation**: Frontend adds a second `setInterval` polling `GET /api/inbox` every 5 seconds when the Inbox tab is active. Polling only runs while the Inbox tab is visible to avoid unnecessary filesystem reads.

---

## Decision 6: Re-promotion guard

**Decision**: The `mark_note_promoted` tool is idempotent (calling it on an already-promoted note is a no-op, not an error). The re-promotion guard ("warn and require confirmation") is implemented in the LLM agent layer: `get_inbox_note` returns `promoted: true`, and the LLM system prompt instructs it to warn before re-promoting.

**Rationale**: Keeps the deterministic core simple. The guard is a UX policy, not a data integrity concern — the right place to enforce it is at the generative edge (the LLM), not in the file-writing function.

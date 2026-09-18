# Research: GUI Inline Editing

## Decision 1: Inline Edit Pattern

**Decision**: Click-to-edit pattern — clicking a display element (title text, importance badge) replaces it with an input; Enter or blur saves and reverts to display.

**Rationale**: This is the dominant pattern for Kanban/board UIs (Trello, Linear). It requires no additional modal or sidebar, keeping the UI minimal. All edits happen in-place, which fits the single-page board layout.

**Alternatives considered**:
- Edit sidebar/panel — rejected as it would require significant new layout code and conflicts with Principle IV (simplicity).
- Explicit "Edit mode" toggle per card — rejected as it adds an extra click and is less discoverable.

---

## Decision 2: Server-side PATCH field handling

**Decision**: Extend the existing `PATCH /api/items/:id` and `PATCH /api/projects/:id` endpoints to accept the new fields (`title`, `description`, `importance` for items; `name` for projects). The server dispatches to new `rename_item` and `rename_project` operations in `core/operations.py`, and to the already-existing `set_item_description` and `set_item_importance`.

**Rationale**: The existing PATCH endpoints already accept multiple optional fields in the request body and dispatch them independently. Adding new field handlers follows the same pattern and requires no new endpoints. This preserves Principle II (single source of truth) and avoids adding routes.

**Alternatives considered**:
- New dedicated endpoints (e.g., `PATCH /api/items/:id/title`) — rejected as REST convention allows multi-field PATCH bodies and the extra routes add unnecessary surface area.
- Client-side JSON file manipulation — prohibited by Principle II.

---

## Decision 3: Item and project rename operations

**Decision**: Add `rename_item(item_id, new_title, project_id_or_context)` logic in `core/operations.py` that performs a uniqueness check (new title must not already exist in the project) and saves. Similarly add `rename_project`. Both find by name (using existing `_find_*_by_id`-style lookup within the server, then call name-based operation).

**Rationale**: The existing operations use name-based lookup. The server already resolves IDs to names before calling operations. Adding rename operations follows the same architecture and keeps the core deterministic.

**Alternatives considered**:
- Direct dict mutation inside the server route — prohibited by Principle II (the server must not write to the data file directly; all writes go through core operations).

---

## Decision 4: Collapse/expand state

**Decision**: Collapse state is purely client-side (JavaScript variable per card, not persisted to the data file). The global toggle sets all cards to collapsed/expanded. State resets to expanded on each page reload / board re-render.

**Rationale**: Collapse state is UI preference, not application data. Persisting it would complicate the schema and violate Principle IV. The spec explicitly says the data file must remain human-readable and minimal (Principle V). A per-session default of "expanded" is the right default for discoverability.

**Alternatives considered**:
- Persist collapse state in the JSON data file — rejected as unnecessary scope creep (Principle VI: don't build what isn't needed now).
- LocalStorage persistence — acceptable future enhancement but not required by the spec.

---

## Decision 5: "Saved" flash indicator

**Decision**: Implement a brief CSS-driven flash (1.5 s green border pulse on the saved field) as a non-blocking polish step. This requires no extra JS library.

**Rationale**: The spec marks it as a nice-to-have. A pure CSS animation (`@keyframes`) is the simplest implementation that delivers the feedback without adding a toast library or significant JS.

**Alternatives considered**:
- Toast notification library — rejected per Principle IV.
- No feedback — acceptable but flash adds clear user confidence for saves.

---

## Resolved Assumptions

- **Project PATCH `/name`**: The existing `update_project` server route already uses the name-based `set_project_status` and `set_importance` operations. Adding a `name` field handler follows the same pattern. A `rename_project` operation will perform uniqueness check within the lane.
- **Item title uniqueness**: Title uniqueness is enforced within a project. The `rename_item` operation will check for duplicates before saving. The client will revert on a 409 error response.
- **No new dependencies**: All changes are pure Python (backend) and vanilla JS (frontend). No JS build step or npm package is introduced.

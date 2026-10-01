# Research: Board Enhancements

**Date**: 2026-09-18

## Decision 1: Drag-and-drop mechanism (HTML5 native vs. library)

**Decision**: Use HTML5 native drag-and-drop (`draggable="true"`, `dragstart`/`dragover`/`drop` events)

**Rationale**: The existing frontend is zero-dependency vanilla JS. Native HTML5 drag-and-drop is supported in all modern browsers, requires no new package, and is sufficient for the two use cases here (horizontal lane reordering, vertical project reordering within a lane). A library would add bundle weight and violate Principle IV.

**Alternatives considered**:
- SortableJS / interact.js — better touch support and smoother UX, but add a dependency and require a CDN or bundler. Out of scope (mobile/touch is explicitly excluded in spec assumptions).

---

## Decision 2: Order persistence strategy

**Decision**: Array position in the JSON data file is the authoritative order. `reorder_lane(lane_id, new_index)` and `reorder_project(project_id, new_index)` splice the target element out of its list and insert it at `new_index`, then call `save_data()`.

**Rationale**: The data model already stores lanes as `data["lanes"]` (an ordered list) and projects as `lane["projects"]` (an ordered list). Position in the array already implies display order — the existing `render()` function iterates `data.lanes.forEach(lane => ...)` and `lane.projects.forEach(project => ...)` in array order. No new schema field is needed; persisting order is free.

**Alternatives considered**:
- Adding an explicit `order: int` field to each lane/project — unnecessary indirection; the array position is already the order.
- Storing a separate order map — unnecessary complexity.

---

## Decision 3: API shape for position updates

**Decision**:
- `PATCH /api/lanes/<lane_id>/position` with body `{ "index": <int> }`
- `PATCH /api/projects/<project_id>/position` with body `{ "index": <int> }`

Both return 200 with the updated full data snapshot (same shape as `/api/data`) so the frontend can re-render immediately without a second poll.

**Rationale**: `PATCH` on a sub-resource (`/position`) is idiomatic REST for partial updates. Returning updated data avoids a round-trip `GET /api/data` after each drop. Index is 0-based, matching Python list semantics.

**Alternatives considered**:
- `PUT` on the full lane/project — would require sending the full entity to just move it.
- Using `before_id`/`after_id` references — more complex to implement and parse; 0-based index is simpler.

---

## Decision 4: this_weekend serialisation / backward compatibility

**Decision**: Add `this_weekend: bool = False` to `Item` dataclass. In `store.py`, items are already deserialized from raw JSON dicts; any existing item without the key will naturally get `False` via `item.get("this_weekend", False)` in read paths and the dataclass default in write paths. No migration script needed.

**Rationale**: The existing `today` and `this_week` fields already use this pattern — `item.get("today", False)` guards every read in `list_items()` and `get_item()`. Adding `this_weekend` identically means zero migration risk.

**Alternatives considered**:
- Schema version bump + migration script — unnecessary overhead for a backward-compatible default-False field.

---

## Decision 5: LLM tool for this_weekend

**Decision**: Add a `set_this_weekend` tool to `tools.py` with the same schema shape as `set_today` / `set_this_week`. Dispatch it in `cli/agent.py` alongside those two.

**Rationale**: Exact symmetry with existing flag tools. The LLM already knows the pattern; adding one more named tool is the minimal and predictable approach.

**Alternatives considered**:
- A single generic `set_flag(flag_name, value)` tool — would require the LLM to know flag names as strings, making the schema less self-documenting. Not worth changing the established pattern for one new flag.

# Research: Deadline Auto-Flags

## Decision 1: Where to apply deadline flag computation

**Decision**: Inside `store.load_data()`, immediately before returning the parsed data dict.

**Rationale**: `load_data()` is the single read entry point (Principle II). Every consumer — CLI, GUI polling, tests — calls it. One insertion point guarantees consistent behavior across all surfaces with no risk of a caller forgetting to apply flags.

**Alternatives considered**:
- Apply in `operations.py` functions — rejected: each operation would need its own call, and new operations could easily forget it.
- Apply in GUI server before rendering — rejected: CLI callers would never see auto-flags.
- Persist flags back to JSON — rejected: violates Principle V (human-readable state) and creates write-back logic that can race with GUI polling.

---

## Decision 2: "Current week" definition

**Decision**: Monday–Sunday ISO calendar week (`date.isocalendar()`).

**Rationale**: Spec explicitly states "Monday–Sunday calendar week." Python's `datetime.date.isocalendar()` returns `(ISO year, week number, weekday)`, making it trivial to compare two dates' `(year, week)` tuples without any arithmetic.

**Alternatives considered**:
- Sunday–Saturday week — rejected: spec is explicit about Mon–Sun.
- Rolling 7-day window from today — rejected: spec defines a calendar week, not a sliding window.

---

## Decision 3: Overdue items

**Decision**: Items with `deadline < today` do NOT auto-set `today` or `this_week`.

**Rationale**: Spec edge case: "What if an item's deadline was yesterday (overdue)? It does NOT auto-set `today`." Overdue handling is explicitly out of scope.

---

## Decision 4: Malformed deadline values

**Decision**: Silently skip — treat as no deadline, set no flags (FR-007).

**Rationale**: Spec requirement. A bad date string should not crash the app or surface as an error to the user; it simply has no effect on flags.

**Implementation**: Wrap `date.fromisoformat(deadline)` in a try/except, continue on any exception.

---

## Decision 5: stdlib only

**Decision**: Use `datetime.date` from the standard library. No third-party date library.

**Rationale**: Principle IV (simplicity). `datetime.date.today()`, `date.fromisoformat()`, and `date.isocalendar()` are all that's needed. No dependency addition justified.

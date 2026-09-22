# Data Model: Deadline Auto-Flags

## No Schema Changes

This feature adds **no new fields** to the data schema and makes **no changes** to `data.json`. The `today` and `this_week` boolean flags on `Item` already exist in the schema. The feature only changes how those fields are populated at read time.

## Existing Fields Used

### Item (existing, in each `lane.projects[].items[]` entry)

| Field       | Type            | Source     | Description |
|-------------|-----------------|------------|-------------|
| `deadline`  | `string\|null`  | Stored     | ISO 8601 date (`YYYY-MM-DD`) or `null` |
| `today`     | `bool`          | Stored + computed | Stored value is the baseline; `apply_deadline_flags()` may OR it to `True` |
| `this_week` | `bool`          | Stored + computed | Stored value is the baseline; `apply_deadline_flags()` may OR it to `True` |

## Computed Behavior (in-memory only)

`apply_deadline_flags(data)` is called by `load_data()` before returning. It walks `data["lanes"] → projects → items` and applies:

```
for each item:
  if item.deadline is a valid ISO date:
    if item.deadline == today:
      item.today = True          # additive only
    if item.deadline falls in current Mon-Sun week:
      item.this_week = True      # additive only
```

The mutations happen on the in-memory dict only. `save_data()` is never called from this path.

## Invariants

- `today` and `this_week` in the JSON file are authoritative for manually-set values.
- The computed overlay can only raise flags, never lower them.
- Items with `deadline = null` are untouched.
- Items with malformed deadline strings are untouched (silently skipped).
- Items with `deadline` outside today/this-week are untouched.

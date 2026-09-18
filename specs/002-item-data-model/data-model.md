# Data Model: Item Data Model Enhancements

## Modified Entity: Item

The `Item` entity gains two new optional fields. All existing fields are unchanged.

| Field | Type | Default | Constraints | Notes |
|-------|------|---------|-------------|-------|
| `id` | string (UUID) | auto | required | unchanged |
| `title` | string | required | non-empty | unchanged |
| `status` | string enum | `"not-started"` | one of: `not-started`, `in-progress`, `completed` | unchanged |
| `today` | boolean | `false` | — | unchanged |
| `this_week` | boolean | `false` | — | unchanged |
| `deadline` | string \| null | `null` | ISO date `YYYY-MM-DD` or null | unchanged |
| `push_count` | integer | `0` | ≥ 0 | unchanged |
| `notes` | array | `[]` | — | unchanged |
| **`description`** | string \| null | `null` | free text; empty string stored as null | **NEW** |
| **`importance`** | integer | `50` | 0 ≤ importance ≤ 100 | **NEW** |

## Backward Compatibility

Items stored before this change will not have `description` or `importance` keys. The application MUST handle missing keys by applying the defaults:

- Missing `description` → treated as `null`
- Missing `importance` → treated as `50`

No migration script is required. The JSON file is read at runtime and defaults are applied in the operations layer.

## Derived Display Rule

Items are visually highlighted in the GUI when `importance > 80`. This is a display rule only — it does not change stored data.

## JSON Example

```json
{
  "id": "f3a2c1d4-...",
  "title": "Design homepage",
  "status": "not-started",
  "today": false,
  "this_week": true,
  "deadline": "2026-10-01",
  "push_count": 0,
  "notes": [],
  "description": "needs mobile-first approach, focus on hero section",
  "importance": 90
}
```

# Data Model: CLI Multi-Tool Dispatch and Read Tools

No new fields are added to the JSON data schema. This feature exposes existing data through new read operations and restructures the agent conversation loop.

## Existing Schema (unchanged)

```
data.json
├── lanes[]
│   ├── id: string (UUID)
│   ├── name: string
│   └── projects[]
│       ├── id: string (UUID)
│       ├── name: string
│       ├── status: enum ["not-started", "scheduled", "in-progress", "completed"]
│       ├── importance: integer 0–100
│       ├── percent_complete: integer 0–100
│       ├── start_date: string|null (ISO 8601)
│       ├── notes: [{id, text, created_at}]
│       └── items[]
│           ├── id: string (UUID)
│           ├── title: string
│           ├── status: enum ["not-started", "in-progress", "completed"]
│           ├── today: boolean
│           ├── this_week: boolean
│           ├── deadline: string|null (ISO 8601)
│           ├── importance: integer 0–100 (default 50)
│           ├── description: string|null
│           ├── notes: [{id, text, created_at}]
│           ├── push_count: integer (Phase 2 placeholder)
│           └── percent_complete: integer (item-level, unused)
```

## New Read Operation Return Shapes

These are the data shapes returned by the new core operations — not new stored fields.

### `list_lanes()` → list[dict]
```
[
  {
    "id": "...",
    "name": "Work",
    "project_count": 3
  },
  ...
]
```

### `list_projects(lane_name=None)` → list[dict]
```
[
  {
    "id": "...",
    "name": "Website",
    "lane": "Work",
    "importance": 75,
    "status": "in-progress",
    "percent_complete": 40,
    "item_count": 5
  },
  ...
]
```

### `list_items(project_name=None, lane_name=None)` → list[dict]
```
[
  {
    "id": "...",
    "title": "Homepage",
    "project": "Website",
    "lane": "Work",
    "status": "not-started",
    "today": false,
    "this_week": true,
    "deadline": "2026-09-30",
    "importance": 80,
    "description": "Design the landing page"
  },
  ...
]
```

### `get_item(item_title, project_name=None, lane_name=None)` → dict
```
{
  "id": "...",
  "title": "Homepage",
  "project": "Website",
  "lane": "Work",
  "status": "not-started",
  "today": false,
  "this_week": true,
  "deadline": "2026-09-30",
  "importance": 80,
  "description": "Design the landing page",
  "notes": [
    {"id": "...", "text": "...", "created_at": "..."}
  ]
}
```
If no match: raises `ValueError("No item found with title '...'.")`.
If ambiguous: raises `AmbiguousMatchError` listing all matching locations.

## Agent Conversation Structure

The agentic loop maintains a `messages` list per user turn:

```
Round 0 (first LLM call):
  messages = [{"role": "user", "content": user_text}]
  tool_choice = "any"

Round N (tool results fed back):
  messages += [
    {"role": "assistant", "content": [tool_use_block_1, tool_use_block_2, ...]},
    {"role": "user",      "content": [tool_result_1, tool_result_2, ...]}
  ]
  tool_choice = "auto"

Terminal state:
  LLM returns stop_reason == "end_turn" with no tool_use blocks.
  Final text content is returned to main.py for printing.
```

Max 10 rounds per user turn (FR-004).

# LLM Tool Contract Additions: Board Enhancements

**Date**: 2026-09-18
**File**: `todo_agent/tools.py`

---

## New tool: set_this_weekend

```json
{
  "name": "set_this_weekend",
  "description": "Mark or unmark an item as something to work on this weekend. Does not affect the today or this_week flags.",
  "input_schema": {
    "type": "object",
    "properties": {
      "item_title": {
        "type": "string",
        "description": "Title of the item."
      },
      "value": {
        "type": "boolean",
        "description": "true to mark as this-weekend, false to unmark."
      },
      "project_name": {
        "type": "string",
        "description": "Project name for disambiguation."
      },
      "lane_name": {
        "type": "string",
        "description": "Lane name for disambiguation."
      }
    },
    "required": ["item_title", "value"]
  }
}
```

**Dispatch** (in `cli/agent.py`): `operations.set_this_weekend(item_title, value, project_name, lane_name)`

**Natural language examples the LLM should resolve to this tool**:
- "add task X to this weekend"
- "mark X for this weekend"
- "remove X from this weekend"
- "X is not a this-weekend item anymore"

---

## No new tools for drag-and-drop

Lane and project reordering are GUI-only interactions. They are not exposed as LLM tools because the CLI/agent interface has no meaningful way to express positional reordering by natural language (users would say "move Website project before Finance project", which is ambiguous and not part of the current scope). This may be revisited in a future feature.

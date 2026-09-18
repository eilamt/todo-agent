# Tool Schema Contracts: New Read Tools and Agent Loop

## New Tool Schemas (additions to `tools.py`)

These four tools are added to the existing `TOOLS` list. After this feature, the list contains 22 tools.

---

### `list_lanes`

```json
{
  "name": "list_lanes",
  "description": "Return all lanes with their id, name, and number of projects. Use this to answer questions like 'what lanes do I have?' or 'show me all categories'.",
  "input_schema": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

**Returns** (via dispatch, as tool_result content):
```
[{"id": "...", "name": "Work", "project_count": 3}, ...]
```
Empty list `[]` if no lanes exist.

---

### `list_projects`

```json
{
  "name": "list_projects",
  "description": "Return all projects, optionally filtered by lane_name. Each result includes id, name, lane, importance, status, percent_complete, and item_count. Use this to answer questions like 'list all projects in Work lane' or 'show me in-progress projects'.",
  "input_schema": {
    "type": "object",
    "properties": {
      "lane_name": {
        "type": "string",
        "description": "Filter to only projects in this lane. Omit to return projects from all lanes."
      }
    },
    "required": []
  }
}
```

**Returns** (via dispatch, as tool_result content):
```
[{"id": "...", "name": "Website", "lane": "Work", "importance": 75, "status": "in-progress", "percent_complete": 40, "item_count": 5}, ...]
```
Empty list `[]` if no matching projects.

---

### `list_items`

```json
{
  "name": "list_items",
  "description": "Return all items, optionally filtered by project_name and/or lane_name. Each result includes id, title, project, lane, status, today, this_week, deadline, importance, and description. Use this to answer questions like 'what items are due today?', 'list all tasks in Website project', or 'show me everything in Work lane'.",
  "input_schema": {
    "type": "object",
    "properties": {
      "project_name": {
        "type": "string",
        "description": "Filter to only items in this project. Omit to return items from all projects."
      },
      "lane_name": {
        "type": "string",
        "description": "Filter to only items in projects within this lane. Can be combined with project_name."
      }
    },
    "required": []
  }
}
```

**Returns** (via dispatch, as tool_result content):
```
[{"id": "...", "title": "Homepage", "project": "Website", "lane": "Work", "status": "not-started", "today": false, "this_week": true, "deadline": "2026-09-30", "importance": 80, "description": "Design the landing page"}, ...]
```
Empty list `[]` if no matching items.

---

### `get_item`

```json
{
  "name": "get_item",
  "description": "Return full details for a single item by title, including notes. Use this when the user asks about a specific task by name. If the title is ambiguous (matches multiple items), returns an error listing all matches — in that case, call again with project_name or lane_name to disambiguate.",
  "input_schema": {
    "type": "object",
    "properties": {
      "item_title": {
        "type": "string",
        "description": "Title of the item to look up."
      },
      "project_name": {
        "type": "string",
        "description": "Project name to disambiguate when multiple items share the same title."
      },
      "lane_name": {
        "type": "string",
        "description": "Lane name for further disambiguation."
      }
    },
    "required": ["item_title"]
  }
}
```

**Returns on success** (via dispatch, as tool_result content):
```
{"id": "...", "title": "Homepage", "project": "Website", "lane": "Work", "status": "not-started", "today": false, "this_week": true, "deadline": "2026-09-30", "importance": 80, "description": "...", "notes": [...]}
```

**Returns on not-found** (as tool_result content, `is_error: true`):
```
No item found with title 'Homepage'.
```

**Returns on ambiguous** (as tool_result content, `is_error: true`):
```
Ambiguous: 'Homepage' found in: Work/Website, Personal/Blog
```

---

## `run_agent()` Interface Contract

`todo_agent/cli/agent.py` exports:

```python
def run_agent(user_text: str, data: dict, config: dict, dispatch_fn) -> str:
    """
    Run the agentic conversation loop.

    Args:
        user_text:    The user's free-text command.
        data:         Current data snapshot (read-only; dispatch_fn manages writes).
        config:       Agent configuration (model name, etc.).
        dispatch_fn:  Callable(tool_name: str, tool_input: dict) -> str
                      Executes the tool and returns a result string for the LLM.

    Returns:
        The LLM's final text response after all tool calls complete.

    Raises:
        ValueError: If ANTHROPIC_API_KEY is not set, or if max rounds (10) exceeded.
    """
```

## `_dispatch()` Return Value Contract

`todo_agent/cli/main.py` `_dispatch()` is modified to return `str`:

| Tool category | Example return string |
|---------------|-----------------------|
| Add operations | `"Added lane 'Work'."` |
| Status/flag updates | `"Updated 'Task A' status to 'in-progress'."` |
| Delete (confirmed) | `"Deleted item 'Task A'."` |
| Delete (cancelled) | `"Deletion cancelled by user."` |
| Read tools | JSON-serialized result (list or dict) as string |
| `request_clarification` | The question text |
| Unknown tool | `"ERROR: Unknown tool 'xyz'."` |

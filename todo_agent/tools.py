"""Static list of 22 LLM-callable tool definitions.

Passed verbatim as the `tools` parameter to client.messages.create().
The LLM selects exactly one tool per invocation; all subsequent logic
is deterministic Python (constitution Principle III).
"""

TOOLS = [
    {
        "name": "add_lane",
        "description": (
            "Create a new lane (top-level grouping). "
            "A blank Markdown instructions file is auto-created for the lane."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name for the new lane. Must be unique across all lanes.",
                }
            },
            "required": ["name"],
        },
    },
    {
        "name": "add_project",
        "description": "Create a new project inside a lane.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lane_name": {
                    "type": "string",
                    "description": "Name of the lane to add the project to.",
                },
                "project_name": {
                    "type": "string",
                    "description": "Name of the new project. Must be unique within the lane.",
                },
                "importance": {
                    "type": "integer",
                    "description": "Importance score 0–100. Defaults to 50 if not specified.",
                    "minimum": 0,
                    "maximum": 100,
                },
            },
            "required": ["lane_name", "project_name"],
        },
    },
    {
        "name": "add_item",
        "description": "Create a new item (task) inside a project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "Name of the project to add the item to.",
                },
                "item_title": {
                    "type": "string",
                    "description": "Title of the new item. Must be unique within the project.",
                },
                "lane_name": {
                    "type": "string",
                    "description": (
                        "Name of the lane containing the project. "
                        "Provide when the project name alone is ambiguous."
                    ),
                },
                "description": {
                    "type": "string",
                    "description": "Optional free-text description of the item.",
                },
            },
            "required": ["project_name", "item_title"],
        },
    },
    {
        "name": "delete_lane",
        "description": (
            "Delete a lane and all its projects and items. "
            "A confirmation step will be shown to the user before deletion proceeds."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "lane_name": {
                    "type": "string",
                    "description": "Name of the lane to delete.",
                }
            },
            "required": ["lane_name"],
        },
    },
    {
        "name": "delete_project",
        "description": (
            "Delete a project and all its items. "
            "A confirmation step will be shown to the user before deletion proceeds."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "Name of the project to delete.",
                },
                "lane_name": {
                    "type": "string",
                    "description": (
                        "Name of the lane containing the project. "
                        "Provide when the project name alone is ambiguous."
                    ),
                },
            },
            "required": ["project_name"],
        },
    },
    {
        "name": "delete_item",
        "description": (
            "Delete an item. "
            "A confirmation step will be shown to the user before deletion proceeds."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "item_title": {
                    "type": "string",
                    "description": "Title of the item to delete.",
                },
                "project_name": {
                    "type": "string",
                    "description": (
                        "Name of the project containing the item. "
                        "Provide when the item title alone is ambiguous."
                    ),
                },
                "lane_name": {
                    "type": "string",
                    "description": "Name of the lane. Provide when further disambiguation is needed.",
                },
            },
            "required": ["item_title"],
        },
    },
    {
        "name": "set_project_status",
        "description": (
            "Change the status of a project. "
            "When setting status to 'scheduled', provide start_date."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "Name of the project.",
                },
                "status": {
                    "type": "string",
                    "enum": ["not-started", "scheduled", "in-progress", "completed"],
                    "description": "New status value.",
                },
                "start_date": {
                    "type": "string",
                    "description": (
                        "ISO 8601 date (YYYY-MM-DD). "
                        "Required when status is 'scheduled'; ignored otherwise."
                    ),
                },
                "lane_name": {
                    "type": "string",
                    "description": "Lane name for disambiguation.",
                },
            },
            "required": ["project_name", "status"],
        },
    },
    {
        "name": "set_item_status",
        "description": (
            "Change the status of an item. "
            "Triggers automatic recalculation of the parent project's percent_complete."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "item_title": {
                    "type": "string",
                    "description": "Title of the item.",
                },
                "status": {
                    "type": "string",
                    "enum": ["not-started", "in-progress", "completed"],
                    "description": "New status value.",
                },
                "project_name": {
                    "type": "string",
                    "description": "Project name for disambiguation.",
                },
                "lane_name": {
                    "type": "string",
                    "description": "Lane name for disambiguation.",
                },
            },
            "required": ["item_title", "status"],
        },
    },
    {
        "name": "set_today",
        "description": (
            "Mark or unmark an item as something to work on today. "
            "Does not affect the this_week flag."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "item_title": {
                    "type": "string",
                    "description": "Title of the item.",
                },
                "value": {
                    "type": "boolean",
                    "description": "true to mark as today, false to unmark.",
                },
                "project_name": {
                    "type": "string",
                    "description": "Project name for disambiguation.",
                },
                "lane_name": {
                    "type": "string",
                    "description": "Lane name for disambiguation.",
                },
            },
            "required": ["item_title", "value"],
        },
    },
    {
        "name": "set_this_week",
        "description": (
            "Mark or unmark an item as something to work on this week. "
            "Does not affect the today flag."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "item_title": {
                    "type": "string",
                    "description": "Title of the item.",
                },
                "value": {
                    "type": "boolean",
                    "description": "true to mark as this-week, false to unmark.",
                },
                "project_name": {
                    "type": "string",
                    "description": "Project name for disambiguation.",
                },
                "lane_name": {
                    "type": "string",
                    "description": "Lane name for disambiguation.",
                },
            },
            "required": ["item_title", "value"],
        },
    },
    {
        "name": "set_deadline",
        "description": "Set or clear the deadline on an item.",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_title": {
                    "type": "string",
                    "description": "Title of the item.",
                },
                "deadline": {
                    "type": ["string", "null"],
                    "description": "ISO 8601 date (YYYY-MM-DD), or null to clear the deadline.",
                },
                "project_name": {
                    "type": "string",
                    "description": "Project name for disambiguation.",
                },
                "lane_name": {
                    "type": "string",
                    "description": "Lane name for disambiguation.",
                },
            },
            "required": ["item_title", "deadline"],
        },
    },
    {
        "name": "set_importance",
        "description": "Set the importance score (0–100) of a project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "Name of the project.",
                },
                "importance": {
                    "type": "integer",
                    "description": "New importance value, 0 (least) to 100 (most important).",
                    "minimum": 0,
                    "maximum": 100,
                },
                "lane_name": {
                    "type": "string",
                    "description": "Lane name for disambiguation.",
                },
            },
            "required": ["project_name", "importance"],
        },
    },
    {
        "name": "add_project_note",
        "description": (
            "Append a timestamped free-text note to a project. "
            "Notes are append-only and cannot be edited or deleted."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "Name of the project.",
                },
                "text": {
                    "type": "string",
                    "description": "Note content.",
                },
                "lane_name": {
                    "type": "string",
                    "description": "Lane name for disambiguation.",
                },
            },
            "required": ["project_name", "text"],
        },
    },
    {
        "name": "add_item_note",
        "description": (
            "Append a timestamped free-text note to an item. "
            "Notes are append-only and cannot be edited or deleted."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "item_title": {
                    "type": "string",
                    "description": "Title of the item.",
                },
                "text": {
                    "type": "string",
                    "description": "Note content.",
                },
                "project_name": {
                    "type": "string",
                    "description": "Project name for disambiguation.",
                },
                "lane_name": {
                    "type": "string",
                    "description": "Lane name for disambiguation.",
                },
            },
            "required": ["item_title", "text"],
        },
    },
    {
        "name": "list_notes",
        "description": (
            "Display all timestamped notes for a project or item in chronological order. "
            "Read-only — does not modify any data."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_type": {
                    "type": "string",
                    "enum": ["project", "item"],
                    "description": "Whether to show notes for a project or an item.",
                },
                "name": {
                    "type": "string",
                    "description": "Name of the project or title of the item.",
                },
                "project_name": {
                    "type": "string",
                    "description": (
                        "Project name for disambiguation "
                        "(useful when entity_type is 'item' and the title appears in multiple projects)."
                    ),
                },
                "lane_name": {
                    "type": "string",
                    "description": "Lane name for further disambiguation.",
                },
            },
            "required": ["entity_type", "name"],
        },
    },
    {
        "name": "set_item_description",
        "description": "Set or clear the free-text description of an item. Pass null or an empty string to clear it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_title": {
                    "type": "string",
                    "description": "Title of the item.",
                },
                "description": {
                    "type": ["string", "null"],
                    "description": "New description text, or null to clear.",
                },
                "project_name": {
                    "type": "string",
                    "description": "Project name for disambiguation.",
                },
                "lane_name": {
                    "type": "string",
                    "description": "Lane name for disambiguation.",
                },
            },
            "required": ["item_title", "description"],
        },
    },
    {
        "name": "set_item_importance",
        "description": "Set an item's importance score (0–100). Items with importance > 80 are highlighted in the GUI.",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_title": {
                    "type": "string",
                    "description": "Title of the item.",
                },
                "importance": {
                    "type": "integer",
                    "description": "New importance value, 0 (least) to 100 (most important).",
                    "minimum": 0,
                    "maximum": 100,
                },
                "project_name": {
                    "type": "string",
                    "description": "Project name for disambiguation.",
                },
                "lane_name": {
                    "type": "string",
                    "description": "Lane name for disambiguation.",
                },
            },
            "required": ["item_title", "importance"],
        },
    },
    {
        "name": "list_lanes",
        "description": (
            "Return all lanes with their id, name, and number of projects. "
            "Use this to answer questions like 'what lanes do I have?' or 'show me all categories'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "list_projects",
        "description": (
            "Return all projects, optionally filtered by lane_name. "
            "Each result includes id, name, lane, importance, status, percent_complete, and item_count. "
            "Use this to answer questions like 'list all projects in Work lane' or 'show me in-progress projects'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "lane_name": {
                    "type": "string",
                    "description": "Filter to only projects in this lane. Omit to return projects from all lanes.",
                }
            },
            "required": [],
        },
    },
    {
        "name": "list_items",
        "description": (
            "Return all items, optionally filtered by project_name and/or lane_name. "
            "Each result includes id, title, project, lane, status, today, this_week, deadline, importance, and description. "
            "Use this to answer questions like 'what items are due today?', 'list all tasks in Website', or 'show me everything in Work lane'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "Filter to only items in this project. Omit to return items from all projects.",
                },
                "lane_name": {
                    "type": "string",
                    "description": "Filter to only items in projects within this lane. Can be combined with project_name.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_item",
        "description": (
            "Return full details for a single item by title, including notes. "
            "Use when the user asks about a specific task by name. "
            "If the title matches multiple items, returns an error listing all matches — "
            "call again with project_name or lane_name to disambiguate."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "item_title": {
                    "type": "string",
                    "description": "Title of the item to look up.",
                },
                "project_name": {
                    "type": "string",
                    "description": "Project name to disambiguate when multiple items share the same title.",
                },
                "lane_name": {
                    "type": "string",
                    "description": "Lane name for further disambiguation.",
                },
            },
            "required": ["item_title"],
        },
    },
    {
        "name": "request_clarification",
        "description": (
            "Use when the user's command is genuinely ambiguous and cannot be safely resolved "
            "from the current data. Ask the user a specific question rather than guessing. "
            "Never use this for commands that are clear."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": (
                        "A specific question to ask the user, e.g. "
                        "'Did you mean the Budget item in Work/Finance or in Personal/Budget?'"
                    ),
                }
            },
            "required": ["question"],
        },
    },
]

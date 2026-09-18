"""Static list of 16 LLM-callable tool definitions.

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

# CLI Tools Contract Patch: Item Data Model Enhancements

This document describes the additive changes to the CLI tool set defined in
`specs/001-todo-agent/contracts/cli-tools.md`. The total tool count increases from 16 to 18.

## Modified Tool: `add_item`

Add `description` as an optional property to the existing `add_item` input schema.

```json
{
  "name": "add_item",
  "description": "Create a new item inside a project.",
  "input_schema": {
    "type": "object",
    "properties": {
      "project_name": { "type": "string" },
      "item_title":   { "type": "string" },
      "lane_name":    { "type": "string" },
      "description":  { "type": "string", "description": "Optional free-text description of the item." }
    },
    "required": ["project_name", "item_title"]
  }
}
```

## New Tool 17: `set_item_description`

```json
{
  "name": "set_item_description",
  "description": "Set or clear the free-text description of an item. Pass null or an empty string to clear it.",
  "input_schema": {
    "type": "object",
    "properties": {
      "item_title":    { "type": "string" },
      "description":   { "type": ["string", "null"], "description": "New description text, or null to clear." },
      "project_name":  { "type": "string" },
      "lane_name":     { "type": "string" }
    },
    "required": ["item_title", "description"]
  }
}
```

## New Tool 18: `set_item_importance`

```json
{
  "name": "set_item_importance",
  "description": "Set an item's importance score (0–100). Items with importance > 80 are highlighted in the GUI.",
  "input_schema": {
    "type": "object",
    "properties": {
      "item_title":    { "type": "string" },
      "importance":    { "type": "integer", "minimum": 0, "maximum": 100 },
      "project_name":  { "type": "string" },
      "lane_name":     { "type": "string" }
    },
    "required": ["item_title", "importance"]
  }
}
```

## Updated Tool Count

| Version | Tool Count |
|---------|-----------|
| 001-todo-agent | 16 |
| 002-item-data-model | **18** |

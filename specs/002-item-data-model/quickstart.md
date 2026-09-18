# Quickstart Validation: Item Data Model Enhancements

## Prerequisites

- `todo-agent` installed (`pip install -e .`)
- `ANTHROPIC_API_KEY` set in environment
- A lane and project already exist (or create them first)

## Setup

```bash
todo "add a lane called Work"
todo "add a project to Work called Website"
todo "add an item to Website called Design homepage"
```

## Scenario S1 — Set item description

```bash
todo "set description of Design homepage to: needs mobile-first approach"
```

**Expected**: `Description for 'Design homepage' set.`

## Scenario S2 — Description persists after reload

```bash
cat ~/.todo-agent/todos.json | python3 -m json.tool | grep description
```

**Expected**: `"description": "needs mobile-first approach"`

## Scenario S3 — Clear item description

```bash
todo "clear description of Design homepage"
```

**Expected**: `Description for 'Design homepage' cleared.`

Verify: `cat ~/.todo-agent/todos.json` shows `"description": null`

## Scenario S4 — Create item with description

```bash
todo "add an item to Website called Write copy with description: SEO-focused"
```

**Expected**: `Added item 'Write copy' to project 'Website'.`

Verify JSON shows `"description": "SEO-focused"` on the new item.

## Scenario S5 — Set item importance

```bash
todo "set importance of Design homepage to 90"
```

**Expected**: `Importance for 'Design homepage' set to 90.`

## Scenario S6 — Reject out-of-range importance

```bash
todo "set importance of Design homepage to 150"
```

**Expected**: Error message, data unchanged.

## Scenario S7 — Default importance on new item

```bash
todo "add an item to Website called Review analytics"
cat ~/.todo-agent/todos.json | python3 -m json.tool | grep importance
```

**Expected**: New item shows `"importance": 50`.

## Scenario S8 — GUI highlights high-importance items

```bash
todo "set importance of Design homepage to 90"
todo visualize
```

**Expected**: "Design homepage" card has a distinct visual highlight (coloured left border or background tint). "Review analytics" (importance 50) has no highlight.

## Scenario S9 — Backward compatibility

Manually remove `description` and `importance` keys from an item in `todos.json`, then run:

```bash
todo visualize
```

**Expected**: Board loads without error; item displays without description; no highlight applied.

## Validation Checklist

- [ ] S1: description set via CLI
- [ ] S2: description persists in JSON
- [ ] S3: description cleared via CLI
- [ ] S4: item created with description
- [ ] S5: importance set via CLI
- [ ] S6: invalid importance rejected
- [ ] S7: default importance is 50
- [ ] S8: GUI highlights importance > 80
- [ ] S9: old items without new fields load correctly

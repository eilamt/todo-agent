# todo-agent

A personal to-do management agent with a natural-language CLI and a local browser GUI,
sharing one JSON data store. All data stays on your machine.

## Prerequisites

- Python 3.11+
- An Anthropic API key set as `ANTHROPIC_API_KEY` in your environment

## Installation

```bash
pip install -e .
```

## First Run

On first run, `~/.todo-agent/` is created automatically with:

- `config.json` — stores the data file path and default model
- `todos.json` — the main data store (path is configurable in `config.json`)

```bash
todo "list everything"
```

## Usage

### Natural-language commands

```bash
todo "add a new lane called Work"
todo "add a project to Work called Website Redesign"
todo "add a task to Website Redesign called Design homepage"
todo "mark Design homepage as done"
todo "move Design homepage to today"
todo "set deadline on Design homepage to 2026-10-15"
todo "set importance of Website Redesign to 80"
todo "note on the Website Redesign project: kickoff done"
todo "show notes for the Website Redesign project"
todo "delete the Work lane"
```

### Browser GUI

```bash
todo visualize          # show all items
todo visualize today    # show today's items only
todo visualize this-week
```

The GUI auto-refreshes every 5 seconds to reflect CLI changes.

## Configuration

Edit `~/.todo-agent/config.json` to change the data file path or default model:

```json
{
  "data_file": "~/.todo-agent/todos.json",
  "model": "claude-haiku-3"
}
```

Set `TODO_DATA_FILE` environment variable to override the data file path without editing the config.

## Development

```bash
pip install -e ".[dev]"
pytest
```

# Research: Personal To-Do Agent

**Phase**: 0 — Technology decisions
**Feature**: `specs/001-todo-agent`
**Date**: 2026-09-17

All decisions below resolve unknowns from the Technical Context and are cross-checked against
the project constitution before design proceeds.

---

## Decision 1: Programming Language

**Decision**: Python 3.11+

**Rationale**: Best fit across all concurrent requirements — first-class Anthropic SDK, stdlib
JSON/file handling, clean local web server story (Flask), argparse for CLI, and pytest for
testing. Python 3.11 brings ~25% performance uplift over 3.10 and improved error messages.

**Alternatives considered**:
- *Node.js 20+*: Also has official Anthropic SDK; rejected because async file I/O adds
  complexity for a synchronous JSON-file store and the CLI story is less ergonomic.
- *Go 1.22+*: Excellent stdlib HTTP server; rejected because the Anthropic Go SDK is
  community-maintained (not official), and typed struct boilerplate for tool-calling adds
  disproportionate friction.

---

## Decision 2: LLM SDK and Provider

**Decision**: Anthropic Python SDK (`anthropic` package); model `claude-haiku-3` as default
(fast, cost-effective for CLI latency); `claude-sonnet-4-6` as configurable override for
higher accuracy on complex intent.

**Rationale**: Tool-calling is a first-class API feature — `tools` parameter accepts JSON
Schema-described function definitions; the model returns `tool_use` content blocks naming the
selected tool and its arguments. This directly implements the "deterministic core, generative
edges" architecture: the LLM selects from the fixed operation set, never writes data itself.
The SDK is officially maintained by Anthropic, typed, and ships as a single dependency.

**Alternatives considered**:
- *OpenAI Python SDK*: Equivalent tool-calling capability; rejected for coherence (project
  already uses Anthropic infrastructure; avoids requiring a second API key).
- *Raw HTTP*: Eliminates the dependency; rejected because the SDK provides retries, typed
  responses, and streaming that would otherwise need reimplementing.

---

## Decision 3: CLI Framework

**Decision**: `argparse` (Python stdlib)

**Rationale**: The CLI surface is intentionally small — one main natural-language path
(`todo "<text>"`) and a handful of reserved subcommands (`todo visualize [scope]`). `argparse`
handles subcommand routing via `add_subparsers` and free-text strings via a positional
argument. Zero dependencies; satisfies the constitution's "prefer stdlib" principle directly.

**Alternatives considered**:
- *click*: More ergonomic for large option surfaces; rejected because that complexity does not
  exist here — adding a dependency to replace two `add_parser` calls is not justified.
- *typer*: Built on click; also pulls in `rich` transitively. Rejected for same reason plus
  higher dependency weight.

---

## Decision 4: Local Web Framework

**Decision**: Flask 3.x

**Rationale**: Minimal, synchronous, well-understood. Serves static files + JSON REST API
+ HTML templates with no ceremony. The synchronous model is correct: every GUI request is a
short-lived JSON fetch; there is no concurrency requirement for a single-user local app.
Flask 3.x is actively maintained; brings in only `Werkzeug` and `Jinja2`.

**Alternatives considered**:
- *FastAPI*: Excellent framework; requires `uvicorn` + `pydantic` + `starlette`. Async model
  creates friction when the rest of the stack is synchronous. Rejected: overhead without benefit.
- *`http.server` (stdlib)*: Zero deps; rejected because routing, JSON parsing, and static file
  serving all need manual implementation — Flask is far more maintainable for the same cost.
- *bottle*: Single-file, zero deps, similar API to Flask; rejected because Flask has better
  CORS/JSON handling, larger ecosystem, and more active development.

---

## Decision 5: GUI Live-Update Mechanism

**Decision**: Client-side polling every 5 seconds against `GET /api/data`, using
`Last-Modified` (from `os.path.getmtime` on the JSON file) + `If-Modified-Since` to return
`304 Not Modified` when unchanged.

**Rationale**: Satisfies the ≤10 second update requirement with zero extra dependencies or
server-side complexity. The Flask endpoint reads the JSON file and returns the current state;
the browser replaces its in-memory state on each non-304 response. Requires only stdlib calls
on the server (`os.path.getmtime`, `http.HTTPStatus`).

**Alternatives considered**:
- *Server-Sent Events*: More efficient; rejected because holding open connections conflicts
  with Flask's synchronous request model, adding async complexity.
- *`watchdog` library*: OS-level file events; rejected because it only solves detection, not
  delivery — still needs SSE or WebSockets, adding complexity without benefit.
- *WebSockets*: Excluded by requirements.

---

## Decision 6: Testing Framework

**Decision**: `pytest` with `unittest.mock` (stdlib) for LLM call stubbing.

**Rationale**: `pytest` is the standard for Python projects — plain `assert`, fixture system,
parametrize, excellent error messages. LLM calls (`client.messages.create`) are patched with
`unittest.mock.patch`, returning fabricated `Message` objects with deterministic `tool_use`
content. No additional mocking library needed.

**Alternatives considered**:
- *`unittest` (stdlib)*: Zero deps; rejected for inferior ergonomics (`self.assert*` ceremony,
  verbose test classes).
- *`pytest-mock`*: Thin fixture wrapper around `unittest.mock`; not needed — `patch` as a
  decorator or context manager is sufficient. Can be added later if mocking surface grows.

---

## Decision 7: Configuration Approach

**Decision**: `~/.todo-agent/config.json`, read at startup via `pathlib.Path` + `json`
(both stdlib). Default written on first run if the file does not exist.

**Default config**:
```json
{
  "data_file": "~/.todo-agent/todos.json",
  "model": "claude-haiku-3"
}
```

**Rationale**: Human-readable, editable without tooling, consistent with the project's JSON
data store, entirely stdlib. `pathlib.Path.home()` resolves `~` cleanly.

**Alternatives considered**:
- *Environment variable only*: Invisible to users who don't know to look; can't be set from
  within the tool. Accepted as a secondary override (env var takes precedence over config file).
- *XDG `~/.config/todo-agent/`*: More correct on Linux; `tomllib` is read-only (write needs
  `tomli-w`). Rejected: additional complexity for a personal local tool.
- *Hardcoded path*: Simpler but removes relocation flexibility. Rejected.

---

## Resolved Unknowns Summary

| Unknown | Resolution |
|---|---|
| Language/version | Python 3.11+ |
| LLM SDK | `anthropic` (official), tool-calling API |
| Default model | `claude-haiku-3` (configurable) |
| CLI framework | `argparse` (stdlib) |
| Web framework | Flask 3.x |
| Live updates | Client polling every 5s + `Last-Modified`/304 |
| Testing | `pytest` + `unittest.mock` |
| Config file | `~/.todo-agent/config.json` (JSON, stdlib) |
| Data file default | `~/.todo-agent/todos.json` (path in config) |
| Lane instructions dir | `~/.todo-agent/lanes/<slug>.md` (auto-created) |

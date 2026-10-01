Technical approach for this build:

**Language & runtime:** Python 3.11+, standard library wherever practical.

**Data store:** A single local JSON file (e.g. `data.json`) as the sole persistent store for lanes, projects, and items. No database engine. Lane-level instruction files are separate plain Markdown files, one per lane, in a `lanes/` directory, named after the lane.

**Core module (`core.py`):** Contains every function that reads or mutates `data.json` — add/delete lane, add/delete project, add/delete item, set status, set today/this-week flags, set deadline, set importance, set project status/start-date, add note, and a `recompute_percent_complete(project)` helper called after any item status change. This module is the only code allowed to touch `data.json`. Both the CLI and the local web server import and call into this module directly — no shared state via network calls between them, since they run on the same machine and share the same filesystem.

**CLI (`cli.py`):** Entry point invoked as `todo "<free text>"`. Sends the free text to the Claude API along with (a) tool/function definitions matching the `core.py` functions, and (b) a compact snapshot of current lane/project/item names so the model can resolve references without needing explicit IDs. The model's tool-call response is executed against `core.py`. Confirm before executing any delete. A separate invocation form (e.g. `todo visualize [all|today|week]`) launches the local web server if it isn't already running and opens the browser to it.

**Local web app (`server.py`):** A lightweight Python web framework (Flask or FastAPI — pick whichever keeps dependencies minimal) serving:
- A single-page frontend (plain HTML/CSS/JS, no heavy frontend framework needed at this scale) rendering the Kanban-style lane/project/item view described in the spec.
- A small JSON API (`GET /api/state`, plus mutation endpoints like `POST /api/item/<id>/status`, `DELETE /api/item/<id>`, `POST /api/item`, etc.) that all call straight into `core.py`.
- The frontend polls `GET /api/state` every few seconds to pick up changes made via the CLI while the page is open.
- Binds to localhost only; not intended to be exposed beyond the local machine.

**Lane Markdown files:** Read as raw text and included as context whenever the CLI is resolving a free-text command that touches that lane, so the user's stated preferences for that lane can influence how Claude interprets ambiguous instructions (e.g. tone, priorities) — without needing separate structured config in v1.

**Testing:** Favor a handful of direct tests against `core.py`'s functions (pure logic, no LLM involved) over trying to test the free-text parsing layer deterministically — the parsing layer should be validated by trying representative phrasings manually rather than unit-tested for exact wording.

**Explicitly not part of this plan:** any scheduler/cron process, any SMS/Twilio integration, any hosted deployment target. Fields that anticipate those (importance, start_date, push_count) exist in the schema but nothing consumes them yet.

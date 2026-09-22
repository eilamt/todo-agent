"""Inbox note management — sole reader/writer of ~/.todo-agent/inbox/*.md files.

Note format:
    ---
    title: My Note Title
    promoted: false
    created_at: 2026-09-22T10:30:00Z
    ---

    Body text here, including an optional ## Promote to section.
"""
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from todo_agent.config import get_inbox_dir


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_note(path: Path) -> dict | None:
    """Parse a single inbox .md file into a note dict.

    Returns None if the file is malformed or unreadable.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None

    # Frontmatter must start at the very first line
    if not text.startswith("---\n"):
        return None

    # Find closing ---
    end = text.find("\n---\n", 4)
    if end == -1:
        return None

    frontmatter_block = text[4:end]
    body = text[end + 5:]  # skip "\n---\n"

    fm: dict = {}
    for line in frontmatter_block.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip()

    title = fm.get("title", "").strip()
    if not title:
        return None

    promoted_raw = fm.get("promoted", "false").lower()
    promoted = promoted_raw == "true"
    created_at = fm.get("created_at") or None

    return {
        "slug": path.stem,
        "title": title,
        "promoted": promoted,
        "created_at": created_at,
        "body": body,
    }


def _write_note_file(path: Path, title: str, promoted: bool, created_at: str, body: str) -> None:
    """Write (or overwrite) a note file with the given frontmatter and body."""
    promoted_str = "true" if promoted else "false"
    content = f"---\ntitle: {title}\npromoted: {promoted_str}\ncreated_at: {created_at}\n---\n{body}"
    path.write_text(content, encoding="utf-8")


def _slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9-]", "", title.lower().replace(" ", "-"))


def _find_note_path(title: str) -> Path:
    """Return the path of the first note whose title matches (case-insensitive).

    Raises ValueError if not found.
    """
    inbox_dir = get_inbox_dir()
    if not inbox_dir.exists():
        raise ValueError(f"Inbox note '{title}' not found.")
    for path in sorted(inbox_dir.glob("*.md")):
        note = _parse_note(path)
        if note and note["title"].lower() == title.lower():
            return path
    raise ValueError(f"Inbox note '{title}' not found.")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def add_inbox_note(title: str, body: str = "") -> dict:
    """Create a new inbox note file. Returns the note dict (including body)."""
    title = title.strip() if title else ""
    if not title:
        raise ValueError("Note title must not be empty.")

    inbox_dir = get_inbox_dir()
    inbox_dir.mkdir(parents=True, exist_ok=True)

    slug = _slugify(title) or "note"
    path = inbox_dir / f"{slug}.md"
    if path.exists():
        # Collision — append short UUID suffix
        slug = f"{slug}-{str(uuid.uuid4())[:8]}"
        path = inbox_dir / f"{slug}.md"

    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_note_file(path, title, promoted=False, created_at=created_at, body=body)

    return {
        "slug": slug,
        "title": title,
        "promoted": False,
        "created_at": created_at,
        "body": body,
    }


def list_inbox_notes() -> list[dict]:
    """Return all inbox notes sorted by created_at descending (nulls last). No body included."""
    inbox_dir = get_inbox_dir()
    if not inbox_dir.exists():
        return []

    notes = []
    for path in inbox_dir.glob("*.md"):
        note = _parse_note(path)
        if note is None:
            continue
        notes.append({
            "slug": note["slug"],
            "title": note["title"],
            "promoted": note["promoted"],
            "created_at": note["created_at"],
        })

    # Sort newest-first; notes without created_at sort to the end
    notes.sort(key=lambda n: (n["created_at"] is None, n["created_at"] or ""), reverse=False)
    notes.sort(key=lambda n: n["created_at"] or "", reverse=True)
    # Move nulls to end
    with_date = [n for n in notes if n["created_at"]]
    without_date = [n for n in notes if not n["created_at"]]
    return with_date + without_date


def get_inbox_note(title: str) -> dict:
    """Return full note dict including body for the first note matching title (case-insensitive).

    Raises ValueError if not found.
    """
    path = _find_note_path(title)
    note = _parse_note(path)
    if note is None:
        raise ValueError(f"Inbox note '{title}' could not be parsed.")
    return note


def mark_note_promoted(title: str) -> dict:
    """Set promoted=True on the note matching title. Idempotent. Returns updated note dict (no body)."""
    path = _find_note_path(title)
    note = _parse_note(path)
    if note is None:
        raise ValueError(f"Inbox note '{title}' could not be parsed.")
    _write_note_file(path, note["title"], promoted=True, created_at=note["created_at"] or "", body=note["body"])
    return {
        "slug": note["slug"],
        "title": note["title"],
        "promoted": True,
        "created_at": note["created_at"],
    }

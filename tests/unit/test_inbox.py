"""Unit tests for todo_agent/core/inbox.py."""
import os
from pathlib import Path

import pytest

from todo_agent.core import inbox as inbox_ops


@pytest.fixture(autouse=True)
def tmp_inbox(tmp_path, monkeypatch):
    """Redirect get_inbox_dir() to a fresh temp directory for each test."""
    monkeypatch.setattr("todo_agent.core.inbox.get_inbox_dir", lambda: tmp_path / "inbox")
    return tmp_path / "inbox"


# ---------------------------------------------------------------------------
# add_inbox_note
# ---------------------------------------------------------------------------

class TestAddInboxNote:
    def test_creates_file_with_correct_frontmatter(self, tmp_inbox):
        note = inbox_ops.add_inbox_note("Lake Book Ideas", "Some body text.")
        assert note["title"] == "Lake Book Ideas"
        assert note["promoted"] is False
        assert note["slug"] == "lake-book-ideas"
        assert note["created_at"] is not None
        path = tmp_inbox / "lake-book-ideas.md"
        assert path.exists()
        content = path.read_text()
        assert "title: Lake Book Ideas" in content
        assert "promoted: false" in content

    def test_body_stored_in_file(self, tmp_inbox):
        inbox_ops.add_inbox_note("My Note", "Hello world\n## Promote to\nDo stuff.")
        path = tmp_inbox / "my-note.md"
        content = path.read_text()
        assert "Hello world" in content
        assert "## Promote to" in content

    def test_empty_body_allowed(self, tmp_inbox):
        note = inbox_ops.add_inbox_note("Empty Body")
        assert note["body"] == ""

    def test_empty_title_raises(self, tmp_inbox):
        with pytest.raises(ValueError, match="must not be empty"):
            inbox_ops.add_inbox_note("   ")

    def test_slug_collision_appends_suffix(self, tmp_inbox):
        n1 = inbox_ops.add_inbox_note("Same Title", "first")
        n2 = inbox_ops.add_inbox_note("Same Title", "second")
        assert n1["slug"] != n2["slug"]
        assert n2["slug"].startswith("same-title-")

    def test_creates_inbox_dir_if_missing(self, tmp_inbox):
        assert not tmp_inbox.exists()
        inbox_ops.add_inbox_note("First Note")
        assert tmp_inbox.exists()


# ---------------------------------------------------------------------------
# list_inbox_notes
# ---------------------------------------------------------------------------

class TestListInboxNotes:
    def test_empty_when_dir_missing(self, tmp_inbox):
        result = inbox_ops.list_inbox_notes()
        assert result == []

    def test_returns_created_notes(self, tmp_inbox):
        inbox_ops.add_inbox_note("Alpha", "body a")
        inbox_ops.add_inbox_note("Beta", "body b")
        notes = inbox_ops.list_inbox_notes()
        titles = {n["title"] for n in notes}
        assert "Alpha" in titles
        assert "Beta" in titles

    def test_no_body_in_list(self, tmp_inbox):
        inbox_ops.add_inbox_note("Note", "some body")
        notes = inbox_ops.list_inbox_notes()
        assert "body" not in notes[0]

    def test_skips_malformed_files(self, tmp_inbox):
        tmp_inbox.mkdir(parents=True, exist_ok=True)
        (tmp_inbox / "broken.md").write_text("no frontmatter here")
        inbox_ops.add_inbox_note("Good Note")
        notes = inbox_ops.list_inbox_notes()
        titles = [n["title"] for n in notes]
        assert "Good Note" in titles
        assert len(titles) == 1  # broken.md skipped

    def test_ignores_non_md_files(self, tmp_inbox):
        tmp_inbox.mkdir(parents=True, exist_ok=True)
        (tmp_inbox / "readme.txt").write_text("not a note")
        inbox_ops.add_inbox_note("Real Note")
        notes = inbox_ops.list_inbox_notes()
        assert len(notes) == 1

    def test_notes_without_created_at_sort_to_end(self, tmp_inbox):
        inbox_ops.add_inbox_note("Dated Note")
        # Hand-place a note without created_at
        tmp_inbox.mkdir(parents=True, exist_ok=True)
        (tmp_inbox / "no-date.md").write_text("---\ntitle: No Date\npromoted: false\n---\nBody")
        notes = inbox_ops.list_inbox_notes()
        titles = [n["title"] for n in notes]
        assert titles[-1] == "No Date"


# ---------------------------------------------------------------------------
# get_inbox_note
# ---------------------------------------------------------------------------

class TestGetInboxNote:
    def test_returns_full_note_with_body(self, tmp_inbox):
        inbox_ops.add_inbox_note("My Idea", "The body text here.")
        note = inbox_ops.get_inbox_note("My Idea")
        assert note["title"] == "My Idea"
        assert "The body text here." in note["body"]

    def test_case_insensitive_lookup(self, tmp_inbox):
        inbox_ops.add_inbox_note("Case Test", "body")
        note = inbox_ops.get_inbox_note("case test")
        assert note["title"] == "Case Test"

    def test_raises_if_not_found(self, tmp_inbox):
        with pytest.raises(ValueError, match="not found"):
            inbox_ops.get_inbox_note("Nonexistent")


# ---------------------------------------------------------------------------
# mark_note_promoted
# ---------------------------------------------------------------------------

class TestMarkNotePromoted:
    def test_sets_promoted_true(self, tmp_inbox):
        inbox_ops.add_inbox_note("To Promote", "body")
        result = inbox_ops.mark_note_promoted("To Promote")
        assert result["promoted"] is True
        # Verify file was updated
        note = inbox_ops.get_inbox_note("To Promote")
        assert note["promoted"] is True

    def test_idempotent_when_already_promoted(self, tmp_inbox):
        inbox_ops.add_inbox_note("Already Done", "body")
        inbox_ops.mark_note_promoted("Already Done")
        result = inbox_ops.mark_note_promoted("Already Done")
        assert result["promoted"] is True

    def test_raises_if_not_found(self, tmp_inbox):
        with pytest.raises(ValueError, match="not found"):
            inbox_ops.mark_note_promoted("Ghost Note")

    def test_body_preserved_after_promote(self, tmp_inbox):
        inbox_ops.add_inbox_note("Keep Body", "Important content\n## Promote to\nSome instructions.")
        inbox_ops.mark_note_promoted("Keep Body")
        note = inbox_ops.get_inbox_note("Keep Body")
        assert "Important content" in note["body"]
        assert "## Promote to" in note["body"]

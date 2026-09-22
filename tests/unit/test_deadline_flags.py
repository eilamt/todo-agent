"""Unit tests for apply_deadline_flags() in store.py."""
from datetime import date, timedelta
from unittest.mock import patch

import pytest

from todo_agent.core.store import apply_deadline_flags


def _make_data(*items):
    """Build a minimal data dict with a single lane, single project, and given items."""
    return {
        "lanes": [
            {
                "projects": [
                    {"items": list(items)}
                ]
            }
        ]
    }


def _item(deadline=None, today=False, this_week=False):
    return {"deadline": deadline, "today": today, "this_week": False if not this_week else True}


TODAY = date.today().isoformat()
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()
TOMORROW = (date.today() + timedelta(days=1)).isoformat()

# A day in the current ISO week that is NOT today (skip if today is the only day left)
_today_obj = date.today()
_weekday = _today_obj.isoweekday()  # 1=Mon … 7=Sun
# Pick Monday of this week if today is not Monday, else pick Tuesday
_monday = _today_obj - timedelta(days=_weekday - 1)
THIS_WEEK_NOT_TODAY = (
    (_monday + timedelta(days=1)).isoformat()  # Tuesday
    if _monday != _today_obj
    else (_monday + timedelta(days=1)).isoformat()
)
# A date in next week
NEXT_WEEK = (_monday + timedelta(weeks=1)).isoformat()


class TestApplyDeadlineFlagsToday:
    def test_deadline_today_sets_today_flag(self):
        item = _item(deadline=TODAY)
        data = _make_data(item)
        apply_deadline_flags(data)
        assert item["today"] is True

    def test_deadline_today_also_sets_this_week(self):
        item = _item(deadline=TODAY)
        data = _make_data(item)
        apply_deadline_flags(data)
        assert item["this_week"] is True

    def test_deadline_yesterday_does_not_set_today(self):
        item = _item(deadline=YESTERDAY)
        data = _make_data(item)
        apply_deadline_flags(data)
        assert item["today"] is False

    def test_deadline_tomorrow_does_not_set_today(self):
        item = _item(deadline=TOMORROW)
        data = _make_data(item)
        apply_deadline_flags(data)
        assert item["today"] is False


class TestApplyDeadlineFlagsThisWeek:
    def test_deadline_in_current_week_sets_this_week(self):
        # Use a date in this week that may or may not be today
        item = _item(deadline=THIS_WEEK_NOT_TODAY)
        data = _make_data(item)
        apply_deadline_flags(data)
        assert item["this_week"] is True

    def test_deadline_next_week_does_not_set_this_week(self):
        item = _item(deadline=NEXT_WEEK)
        data = _make_data(item)
        apply_deadline_flags(data)
        assert item["this_week"] is False

    def test_deadline_yesterday_does_not_set_this_week(self):
        # yesterday is in the past; the week check is purely by ISO week number
        # so only matters if yesterday was in a different week — but either way
        # the flag should only be True if in the current week
        item = _item(deadline=YESTERDAY)
        data = _make_data(item)
        apply_deadline_flags(data)
        yesterday_obj = date.today() - timedelta(days=1)
        expected = yesterday_obj.isocalendar()[:2] == date.today().isocalendar()[:2]
        assert item["this_week"] is expected


class TestApplyDeadlineFlagsPreservation:
    def test_manually_set_today_no_deadline_preserved(self):
        item = {"deadline": None, "today": True, "this_week": False}
        data = _make_data(item)
        apply_deadline_flags(data)
        assert item["today"] is True

    def test_manually_set_this_week_no_deadline_preserved(self):
        item = {"deadline": None, "today": False, "this_week": True}
        data = _make_data(item)
        apply_deadline_flags(data)
        assert item["this_week"] is True

    def test_no_deadline_leaves_flags_unchanged(self):
        item = {"deadline": None, "today": False, "this_week": False}
        data = _make_data(item)
        apply_deadline_flags(data)
        assert item["today"] is False
        assert item["this_week"] is False


class TestApplyDeadlineFlagsMalformed:
    def test_malformed_deadline_silently_skipped(self):
        item = {"deadline": "not-a-date", "today": False, "this_week": False}
        data = _make_data(item)
        apply_deadline_flags(data)  # must not raise
        assert item["today"] is False
        assert item["this_week"] is False

    def test_empty_string_deadline_silently_skipped(self):
        item = {"deadline": "", "today": False, "this_week": False}
        data = _make_data(item)
        apply_deadline_flags(data)
        assert item["today"] is False
        assert item["this_week"] is False


class TestApplyDeadlineFlagsNoPersist:
    def test_save_data_never_called(self):
        """apply_deadline_flags must not write to disk."""
        item = _item(deadline=TODAY)
        data = _make_data(item)
        with patch("todo_agent.core.store.save_data") as mock_save:
            apply_deadline_flags(data)
            mock_save.assert_not_called()

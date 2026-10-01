"""Unit tests for todo_agent/instrumentation.py."""
import json
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from todo_agent import instrumentation as inst


@pytest.fixture(autouse=True)
def tmp_log(tmp_path, monkeypatch):
    """Redirect get_log_path() to a temp file for each test."""
    log_file = tmp_path / "api-calls.jsonl"
    monkeypatch.setattr("todo_agent.instrumentation.get_log_path", lambda: log_file)
    return log_file


def _make_usage(input_tokens=100, output_tokens=50,
                cache_creation=None, cache_read_input_tokens=0,
                cache_creation_input_tokens=0):
    u = MagicMock()
    u.input_tokens = input_tokens
    u.output_tokens = output_tokens
    u.cache_creation = cache_creation
    u.cache_read_input_tokens = cache_read_input_tokens
    u.cache_creation_input_tokens = cache_creation_input_tokens
    return u


def _make_response(usage=None, model="claude-haiku-4-5-20251001"):
    r = MagicMock()
    r.usage = usage or _make_usage()
    r.model = model
    return r


# ---------------------------------------------------------------------------
# compute_cost
# ---------------------------------------------------------------------------

class TestComputeCost:
    def test_standard_tokens_only(self):
        usage = _make_usage(input_tokens=1_000_000, output_tokens=1_000_000)
        cost = inst.compute_cost(usage)
        assert abs(cost - (1.00 + 5.00)) < 1e-9

    def test_cache_read_tokens(self):
        usage = _make_usage(input_tokens=0, output_tokens=0, cache_read_input_tokens=1_000_000)
        cost = inst.compute_cost(usage)
        assert abs(cost - 0.10) < 1e-9

    def test_tier_specific_prices_when_cache_creation_present(self):
        cc = MagicMock()
        cc.ephemeral_5m_input_tokens = 1_000_000
        cc.ephemeral_1h_input_tokens = 1_000_000
        usage = _make_usage(input_tokens=0, output_tokens=0, cache_creation=cc)
        cost = inst.compute_cost(usage)
        assert abs(cost - (1.25 + 2.00)) < 1e-9

    def test_fallback_aggregate_when_cache_creation_none(self):
        usage = _make_usage(input_tokens=0, output_tokens=0,
                            cache_creation=None, cache_creation_input_tokens=1_000_000)
        cost = inst.compute_cost(usage)
        assert abs(cost - 1.25) < 1e-9  # cache_write_5m price

    def test_zero_tokens_gives_zero_cost(self):
        usage = _make_usage(input_tokens=0, output_tokens=0)
        assert inst.compute_cost(usage) == 0.0


# ---------------------------------------------------------------------------
# build_log_record
# ---------------------------------------------------------------------------

class TestBuildLogRecord:
    def test_required_fields_present(self):
        r = _make_response()
        rec = inst.build_log_record("req-1", r, 123, 45.0)
        for field in ("timestamp", "request_id", "model", "input_tokens", "output_tokens",
                      "cache_creation_5m_tokens", "cache_creation_1h_tokens",
                      "cache_read_input_tokens", "latency_ms",
                      "seconds_since_previous_call", "estimated_cost_usd"):
            assert field in rec, f"Missing field: {field}"

    def test_replay_key_absent_when_false(self):
        rec = inst.build_log_record("req-1", _make_response(), 10, None, replay=False)
        assert "replay" not in rec

    def test_replay_key_true_when_set(self):
        rec = inst.build_log_record("req-1", _make_response(), 10, None, replay=True)
        assert rec["replay"] is True

    def test_seconds_since_null_propagated(self):
        rec = inst.build_log_record("req-1", _make_response(), 10, None)
        assert rec["seconds_since_previous_call"] is None

    def test_latency_stored(self):
        rec = inst.build_log_record("req-1", _make_response(), 777, None)
        assert rec["latency_ms"] == 777


# ---------------------------------------------------------------------------
# append_log_record
# ---------------------------------------------------------------------------

class TestAppendLogRecord:
    def test_creates_file_and_writes_valid_json(self, tmp_log):
        rec = {"key": "value", "num": 42}
        inst.append_log_record(rec)
        assert tmp_log.exists()
        loaded = json.loads(tmp_log.read_text().strip())
        assert loaded == rec

    def test_appends_multiple_records(self, tmp_log):
        inst.append_log_record({"a": 1})
        inst.append_log_record({"b": 2})
        lines = tmp_log.read_text().strip().splitlines()
        assert len(lines) == 2

    def test_does_not_raise_on_unwritable_dir(self, tmp_path, monkeypatch):
        bad_path = tmp_path / "no-such-dir" / "sub" / "log.jsonl"
        monkeypatch.setattr("todo_agent.instrumentation.get_log_path", lambda: bad_path)
        bad_path.parent.mkdir(parents=True)
        bad_path.parent.chmod(0o000)
        try:
            inst.append_log_record({"x": 1})  # must not raise
        finally:
            bad_path.parent.chmod(0o755)


# ---------------------------------------------------------------------------
# load_log_records
# ---------------------------------------------------------------------------

class TestLoadLogRecords:
    def test_empty_when_file_absent(self, tmp_log):
        assert inst.load_log_records() == []

    def test_returns_all_valid_records(self, tmp_log):
        tmp_log.write_text('{"a":1}\n{"b":2}\n')
        records = inst.load_log_records()
        assert len(records) == 2

    def test_skips_malformed_lines(self, tmp_log):
        tmp_log.write_text('{"ok":1}\nnot json\n{"ok":2}\n')
        records = inst.load_log_records()
        assert len(records) == 2

    def test_skips_blank_lines(self, tmp_log):
        tmp_log.write_text('{"a":1}\n\n{"b":2}\n')
        records = inst.load_log_records()
        assert len(records) == 2


# ---------------------------------------------------------------------------
# get_last_call_timestamp
# ---------------------------------------------------------------------------

class TestGetLastCallTimestamp:
    def test_returns_none_when_file_absent(self, tmp_log):
        assert inst.get_last_call_timestamp() is None

    def test_parses_utc_timestamp_from_last_line(self, tmp_log):
        tmp_log.write_text(
            '{"timestamp":"2026-09-22T10:00:00.000Z","other":"x"}\n'
            '{"timestamp":"2026-09-22T11:00:00.000Z","other":"y"}\n'
        )
        dt = inst.get_last_call_timestamp()
        assert dt is not None
        assert dt.hour == 11

    def test_returns_none_when_last_line_malformed(self, tmp_log):
        tmp_log.write_text('{"timestamp":"2026-09-22T10:00:00.000Z"}\nnot json\n')
        assert inst.get_last_call_timestamp() is None

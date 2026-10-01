"""Unit tests for todo_agent/cli/cost.py cmd_report()."""
import json
from io import StringIO
from unittest.mock import patch

import pytest

from todo_agent.cli import cost as cost_cmds
from todo_agent import instrumentation


def _write_records(tmp_log, records):
    with open(tmp_log, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def _make_record(request_id="req-1", timestamp="2026-09-22T10:00:00.000Z",
                 input_tokens=100, output_tokens=50, cost=0.0005,
                 cache_w5=0, cache_w1=0, cache_r=0,
                 seconds_since=None, replay=False):
    r = {
        "timestamp": timestamp,
        "request_id": request_id,
        "model": "claude-haiku-4-5-20251001",
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_creation_5m_tokens": cache_w5,
        "cache_creation_1h_tokens": cache_w1,
        "cache_read_input_tokens": cache_r,
        "latency_ms": 200,
        "seconds_since_previous_call": seconds_since,
        "estimated_cost_usd": cost,
    }
    if replay:
        r["replay"] = True
    return r


@pytest.fixture(autouse=True)
def tmp_log(tmp_path, monkeypatch):
    log_file = tmp_path / "api-calls.jsonl"
    monkeypatch.setattr("todo_agent.instrumentation.get_log_path", lambda: log_file)
    monkeypatch.setattr("todo_agent.cli.cost.instrumentation", instrumentation)
    return log_file


class TestCmdReport:
    def test_no_data_message_when_log_empty(self, capsys):
        cost_cmds.cmd_report()
        out = capsys.readouterr().out
        assert "No API call data yet" in out

    def test_overall_row_present(self, tmp_log, capsys):
        _write_records(tmp_log, [
            _make_record("req-1", cost=0.001),
            _make_record("req-2", cost=0.002),
        ])
        cost_cmds.cmd_report()
        out = capsys.readouterr().out
        assert "OVERALL" in out

    def test_request_count_equals_distinct_request_ids(self, tmp_log, capsys):
        _write_records(tmp_log, [
            _make_record("req-A", cost=0.001),
            _make_record("req-A", cost=0.001),  # second round-trip same request
            _make_record("req-B", cost=0.001),
        ])
        cost_cmds.cmd_report()
        out = capsys.readouterr().out
        # OVERALL row: 2 requests, 3 calls
        lines = [l for l in out.splitlines() if "OVERALL" in l]
        assert lines, "OVERALL row missing"
        # 2 distinct request IDs
        assert "2" in lines[0]

    def test_groups_by_local_date(self, tmp_log, capsys):
        _write_records(tmp_log, [
            _make_record("req-1", timestamp="2026-09-22T10:00:00.000Z", cost=0.001),
            _make_record("req-2", timestamp="2026-09-23T10:00:00.000Z", cost=0.002),
        ])
        cost_cmds.cmd_report()
        out = capsys.readouterr().out
        assert "2026-09-22" in out or "2026-09-23" in out  # at least one date row

    def test_cache_hit_potential_counts_calls_under_300s(self, tmp_log, capsys):
        _write_records(tmp_log, [
            _make_record("req-1", seconds_since=None),
            _make_record("req-2", seconds_since=60.0),   # within 5 min → hit
            _make_record("req-3", seconds_since=400.0),  # over 5 min → miss
            _make_record("req-4", seconds_since=120.0),  # within 5 min → hit
        ])
        cost_cmds.cmd_report()
        out = capsys.readouterr().out
        # 2 hits out of 3 calls with prior context
        assert "2 of 3" in out

    def test_price_table_disclaimer_shown(self, tmp_log, capsys):
        _write_records(tmp_log, [_make_record(cost=0.001)])
        cost_cmds.cmd_report()
        out = capsys.readouterr().out
        assert "console.anthropic.com" in out

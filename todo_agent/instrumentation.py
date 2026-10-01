"""API call instrumentation: cost estimation, JSONL logging, log reading.

This module is the single owner of log I/O and cost arithmetic.
It must never raise — all I/O failures are swallowed with a stderr warning.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from todo_agent.config import PRICE_TABLE, get_log_path

_skipped_lines = 0


def compute_cost(usage) -> float:
    """Estimate USD cost from an Anthropic usage object."""
    p = PRICE_TABLE
    cost = (getattr(usage, "input_tokens", 0) or 0) * p["input"] / 1_000_000
    cost += (getattr(usage, "output_tokens", 0) or 0) * p["output"] / 1_000_000
    cost += (getattr(usage, "cache_read_input_tokens", 0) or 0) * p["cache_read"] / 1_000_000

    cache_creation = getattr(usage, "cache_creation", None)
    if cache_creation is not None:
        cost += (getattr(cache_creation, "ephemeral_5m_input_tokens", 0) or 0) * p["cache_write_5m"] / 1_000_000
        cost += (getattr(cache_creation, "ephemeral_1h_input_tokens", 0) or 0) * p["cache_write_1h"] / 1_000_000
    else:
        # Fallback: aggregate field, priced at 5-min rate
        cost += (getattr(usage, "cache_creation_input_tokens", 0) or 0) * p["cache_write_5m"] / 1_000_000

    return cost


def build_log_record(
    request_id: str,
    response,
    latency_ms: int,
    seconds_since_previous: "float | None",
    replay: bool = False,
) -> dict:
    """Assemble a log record dict from an Anthropic API response."""
    usage = response.usage
    cache_creation = getattr(usage, "cache_creation", None)

    if cache_creation is not None:
        c5m = getattr(cache_creation, "ephemeral_5m_input_tokens", 0) or 0
        c1h = getattr(cache_creation, "ephemeral_1h_input_tokens", 0) or 0
    else:
        c5m = 0
        c1h = 0

    record = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "request_id": request_id,
        "model": getattr(response, "model", "unknown"),
        "input_tokens": getattr(usage, "input_tokens", 0) or 0,
        "output_tokens": getattr(usage, "output_tokens", 0) or 0,
        "cache_creation_5m_tokens": c5m,
        "cache_creation_1h_tokens": c1h,
        "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", 0) or 0,
        "latency_ms": latency_ms,
        "seconds_since_previous_call": seconds_since_previous,
        "estimated_cost_usd": compute_cost(usage),
    }
    if replay:
        record["replay"] = True
    return record


def append_log_record(record: dict) -> None:
    """Append one JSON record to the log file. Never raises."""
    try:
        log_path = get_log_path()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        print(f"[instrumentation] warning: could not write log: {e}", file=sys.stderr)


def load_log_records() -> list:
    """Read all valid records from the log file. Skips malformed lines."""
    global _skipped_lines
    log_path = get_log_path()
    if not log_path.exists():
        return []
    records = []
    skipped = 0
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                skipped += 1
    _skipped_lines = skipped
    return records


def get_last_call_timestamp() -> "datetime | None":
    """Return the UTC datetime of the last logged API call, or None."""
    log_path = get_log_path()
    if not log_path.exists():
        return None
    try:
        with log_path.open("rb") as f:
            # Seek from end to find last non-empty line
            f.seek(0, 2)
            size = f.tell()
            if size == 0:
                return None
            pos = size - 1
            while pos > 0:
                f.seek(pos)
                ch = f.read(1)
                if ch == b"\n" and pos < size - 1:
                    break
                pos -= 1
            f.seek(pos + 1 if pos > 0 else 0)
            last_line = f.read().decode("utf-8").strip()
        if not last_line:
            return None
        record = json.loads(last_line)
        ts = record.get("timestamp", "")
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None

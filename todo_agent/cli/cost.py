"""CLI handlers for `todo cost {report,prefix,replay}` subcommands."""
import json
import os
import sys
import time
from datetime import datetime, timezone

import anthropic

from todo_agent import instrumentation
from todo_agent.cli.agent import _build_data_summary, run_agent
from todo_agent.config import MIN_CACHEABLE_PREFIX_TOKENS, PRICE_TABLE, load_config
from todo_agent.core.store import load_data
from todo_agent.tools import TOOLS

# Tools that write state — intercepted in dry-run/replay mode.
_DRY_RUN_WRITE_TOOLS = {
    "add_lane", "add_project", "add_item",
    "delete_lane", "delete_project", "delete_item",
    "set_project_status", "set_item_status",
    "set_today", "set_this_week", "set_this_weekend",
    "set_deadline", "set_importance",
    "add_project_note", "add_item_note",
    "set_item_description", "set_item_importance",
    "add_inbox_note", "mark_note_promoted",
}


def cmd_report() -> None:
    records = instrumentation.load_log_records()
    if not records:
        print("No API call data yet. Use the CLI agent to start collecting data.")
        return

    # Group by local date and request_id
    from collections import defaultdict
    by_date = defaultdict(list)
    for r in records:
        try:
            dt = datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")).astimezone()
            date_key = dt.date().isoformat()
        except Exception:
            date_key = "unknown"
        by_date[date_key].append(r)

    header = (
        f"{'Date':<12} {'Req':>5} {'Calls':>6} {'C/Req':>6}  "
        f"{'Input Tok':>10} {'Out Tok':>8} {'Cache-W Tok':>12} {'Cache-R Tok':>12}  "
        f"{'Total Cost':>12} {'Mean/Req':>10}"
    )
    sep = "-" * len(header)

    print("API Cost Report")
    print("===============")
    print()
    print(header)
    print(sep)

    overall = {
        "requests": 0, "calls": 0,
        "input": 0, "output": 0, "cache_w": 0, "cache_r": 0, "cost": 0.0,
    }

    cache_hit_calls = 0
    total_calls_with_prev = 0

    for date_key in sorted(by_date.keys()):
        day_recs = by_date[date_key]
        req_ids = {r.get("request_id") for r in day_recs}
        n_req = len(req_ids)
        n_calls = len(day_recs)
        inp = sum(r.get("input_tokens", 0) for r in day_recs)
        out = sum(r.get("output_tokens", 0) for r in day_recs)
        cw = sum(r.get("cache_creation_5m_tokens", 0) + r.get("cache_creation_1h_tokens", 0) for r in day_recs)
        cr = sum(r.get("cache_read_input_tokens", 0) for r in day_recs)
        cost = sum(r.get("estimated_cost_usd", 0.0) for r in day_recs)

        calls_per_req = n_calls / n_req if n_req else 0
        mean_cost = cost / n_req if n_req else 0

        print(
            f"{date_key:<12} {n_req:>5} {n_calls:>6} {calls_per_req:>6.2f}  "
            f"{inp:>10,} {out:>8,} {cw:>12,} {cr:>12,}  "
            f"${cost:>11.6f} ${mean_cost:>9.6f}"
        )

        overall["requests"] += n_req
        overall["calls"] += n_calls
        overall["input"] += inp
        overall["output"] += out
        overall["cache_w"] += cw
        overall["cache_r"] += cr
        overall["cost"] += cost

        for r in day_recs:
            s = r.get("seconds_since_previous_call")
            if s is not None:
                total_calls_with_prev += 1
                if s < 300:
                    cache_hit_calls += 1

    print(sep)
    n_req = overall["requests"]
    n_calls = overall["calls"]
    cost = overall["cost"]
    print(
        f"{'OVERALL':<12} {n_req:>5} {n_calls:>6} {n_calls/n_req if n_req else 0:>6.2f}  "
        f"{overall['input']:>10,} {overall['output']:>8,} {overall['cache_w']:>12,} {overall['cache_r']:>12,}  "
        f"${cost:>11.6f} ${cost/n_req if n_req else 0:>9.6f}"
    )
    print()
    if total_calls_with_prev > 0:
        pct = cache_hit_calls / total_calls_with_prev * 100
        print(
            f"Cache hit potential: {cache_hit_calls} of {total_calls_with_prev} API calls "
            f"({pct:.1f}%) arrived within 5 minutes of the previous call."
        )
    else:
        print("Cache hit potential: insufficient data (need at least 2 API calls).")
    print(f"Price table last verified: {PRICE_TABLE['last_verified']}. "
          "Verify current prices at console.anthropic.com.")


def cmd_prefix() -> None:
    config = load_config()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    model = config.get("model", "claude-haiku-4-5-20251001")

    from datetime import date
    system_prompt = (
        f"You are a to-do management assistant. Today's date is {date.today().isoformat()}.\n\n"
        "Current to-do state:\n"
        f"{_build_data_summary({})}\n\n"
        "Use the available tools to fulfill the user's request."
    )

    try:
        result = client.messages.count_tokens(
            model=model,
            system=system_prompt,
            tools=TOOLS,
            messages=[{"role": "user", "content": "x"}],
        )
        token_count = result.input_tokens
    except anthropic.APIError as e:
        print(f"Error calling token-counting endpoint: {e}", file=sys.stderr)
        sys.exit(1)

    print("Agent Prefix Token Count")
    print("========================")
    print(f"Static prefix tokens:                {token_count:,}")
    print(f"Minimum cacheable length (Haiku 4.5): {MIN_CACHEABLE_PREFIX_TOKENS:,} tokens")
    if token_count >= MIN_CACHEABLE_PREFIX_TOKENS:
        print("Result: Prefix MEETS the minimum — prompt caching is viable.")
    else:
        print("Result: Prefix does NOT meet the minimum — caching would have no effect.")


def cmd_replay(utterances_path: str, gap: float = 1.0, output: str = "replay_output.jsonl") -> None:
    # Load utterances
    try:
        with open(utterances_path, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()
    except OSError as e:
        print(f"Error reading utterances file: {e}", file=sys.stderr)
        sys.exit(1)

    utterances = [
        line.strip() for line in raw_lines
        if line.strip() and not line.strip().startswith("#")
    ]

    if not utterances:
        print("No utterances to replay.")
        return

    print(f"Replay: {len(utterances)} utterances loaded from {utterances_path}")

    config = load_config()
    data = load_data()

    # Import the real dispatch from main (lazy to avoid circular import issues)
    from todo_agent.cli.main import _dispatch as real_dispatch

    total_calls = 0
    total_cost = 0.0

    with open(output, "w", encoding="utf-8") as out_f:
        for idx, utterance in enumerate(utterances, 1):
            tool_chain = []

            def dry_run_dispatch(tool_name, tool_input, _chain=tool_chain):
                if tool_name in _DRY_RUN_WRITE_TOOLS:
                    _chain.append({"name": tool_name, "input": tool_input, "dry_run": True})
                    return f"[DRY RUN] would call {tool_name} with args: {json.dumps(tool_input)}"
                else:
                    _chain.append({"name": tool_name, "input": tool_input, "dry_run": False})
                    return real_dispatch(tool_name, tool_input)

            records_before = len(instrumentation.load_log_records())
            try:
                run_agent(utterance, data, config, dry_run_dispatch, replay=True)
            except Exception as e:
                print(f"  Error: {e}")

            records_after = instrumentation.load_log_records()
            new_records = records_after[records_before:]
            n_calls = len(new_records)
            utterance_cost = sum(r.get("estimated_cost_usd", 0.0) for r in new_records)
            total_calls += n_calls
            total_cost += utterance_cost

            request_id = new_records[0]["request_id"] if new_records else ""
            chain_record = {
                "utterance": utterance,
                "request_id": request_id,
                "tool_calls": tool_chain,
            }
            out_f.write(json.dumps(chain_record) + "\n")

            tools_summary = ", ".join(
                f"{'[dry-run] ' if tc['dry_run'] else ''}{tc['name']}" for tc in tool_chain
            ) or "(no tools)"
            print(f"[{idx}/{len(utterances)}] {utterance}")
            print(f"      → {tools_summary} | {n_calls} API call(s) | ${utterance_cost:.6f}")

            if idx < len(utterances) and gap > 0:
                time.sleep(gap)

    print(f"\nReplay complete. Tool chains written to {output}.")
    print(f"Total: {len(utterances)} utterances | {total_calls} API calls | ${total_cost:.6f} estimated")

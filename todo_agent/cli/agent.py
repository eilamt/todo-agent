"""LLM tool-call layer.

This is the ONLY file that calls the Anthropic SDK. It takes the user's
free-text input and the current data snapshot, calls the LLM with the 16
declared tools, and returns the selected tool name and its arguments.

All subsequent logic is deterministic Python in core/operations.py.
"""
import os
from datetime import date

import anthropic

from todo_agent.tools import TOOLS

_VALID_TOOL_NAMES = {t["name"] for t in TOOLS}


def _build_data_summary(data: dict) -> str:
    """Return a compact text summary of the current store for the LLM context."""
    lines = []
    for lane in data.get("lanes", []):
        lines.append(f"Lane: {lane['name']}")
        for project in lane.get("projects", []):
            lines.append(f"  Project: {project['name']} (status={project['status']})")
            for item in project.get("items", []):
                flags = []
                if item.get("today"):
                    flags.append("today")
                if item.get("this_week"):
                    flags.append("this-week")
                flag_str = f" [{', '.join(flags)}]" if flags else ""
                lines.append(
                    f"    Item: {item['title']} (status={item['status']}{flag_str})"
                )
    return "\n".join(lines) if lines else "(empty — no lanes yet)"


def resolve_intent(user_text: str, data: dict, config: dict) -> tuple[str, dict]:
    """Call the LLM and return (tool_name, tool_input).

    Raises:
        ValueError: if the LLM returns no tool_use block, or an unknown tool name.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set.")

    client = anthropic.Anthropic(api_key=api_key)
    model = config.get("model", "claude-haiku-4-5-20251001")

    system_prompt = (
        f"You are a to-do management assistant. Today's date is {date.today().isoformat()}.\n\n"
        "Current to-do state:\n"
        f"{_build_data_summary(data)}\n\n"
        "Select exactly one tool to perform the user's request. "
        "Prefer 'request_clarification' over any destructive action when the intent is ambiguous. "
        "For requests to display, list, show, or view data (e.g. 'list projects', 'show me all items'), "
        "use 'request_clarification' to tell the user to run 'todo visualize' instead — "
        "do NOT use 'list_notes' or any other tool to satisfy display requests."
    )

    message = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system_prompt,
        tools=TOOLS,
        tool_choice={"type": "any"},
        messages=[{"role": "user", "content": user_text}],
    )

    # Find the first tool_use block
    for block in message.content:
        if block.type == "tool_use":
            if block.name not in _VALID_TOOL_NAMES:
                raise ValueError(
                    f"LLM returned unknown tool name: {block.name!r}. "
                    "This is a bug — tool list may be out of sync."
                )
            return block.name, block.input

    raise ValueError(
        "LLM did not return a tool_use block. "
        "Response content: " + str(message.content)
    )

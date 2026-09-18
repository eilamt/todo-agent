"""LLM agentic loop layer.

This is the ONLY file that calls the Anthropic SDK. It takes the user's
free-text input and the current data snapshot, runs the agentic tool-call
loop, and returns the LLM's final text summary.

All tool execution is delegated to the dispatch_fn callback (implemented
in cli/main.py). All subsequent data logic is deterministic Python in
core/operations.py (constitution Principle III).
"""
import os
from datetime import date

import anthropic

from todo_agent.tools import TOOLS

_VALID_TOOL_NAMES = {t["name"] for t in TOOLS}

MAX_ROUNDS = 10


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


def run_agent(user_text: str, data: dict, config: dict, dispatch_fn) -> str:
    """Run the agentic conversation loop and return the LLM's final text summary.

    Args:
        user_text:    The user's free-text command.
        data:         Current data snapshot (read-only reference; dispatch_fn manages writes).
        config:       Agent configuration dict (model name, etc.).
        dispatch_fn:  Callable(tool_name: str, tool_input: dict) -> str
                      Executes a tool and returns a result string for the LLM.

    Returns:
        The LLM's final text response after all tool calls complete.

    Raises:
        ValueError: If ANTHROPIC_API_KEY is not set, or if MAX_ROUNDS exceeded.
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
        "Use the available tools to fulfill the user's request. "
        "You may call multiple tools in sequence to complete compound requests. "
        "When you have finished all actions, respond with a brief summary of what was done. "
        "Prefer 'request_clarification' over any destructive action when the intent is ambiguous."
    )

    messages = [{"role": "user", "content": user_text}]

    for round_num in range(MAX_ROUNDS):
        tool_choice = {"type": "any"} if round_num == 0 else {"type": "auto"}
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,
            tools=TOOLS,
            tool_choice=tool_choice,
            messages=messages,
        )

        # Collect all tool_use blocks from this response
        tool_uses = [b for b in response.content if b.type == "tool_use"]

        if not tool_uses:
            # LLM finished — extract and return the final text
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return "(No response from assistant.)"

        # Validate and execute all tool calls in sequence
        tool_results = []
        for block in tool_uses:
            if block.name not in _VALID_TOOL_NAMES:
                raise ValueError(
                    f"LLM returned unknown tool name: {block.name!r}. "
                    "This is a bug — tool list may be out of sync."
                )
            result_str = dispatch_fn(block.name, block.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result_str,
            })

        # Append the assistant's tool-use turn and our tool results to the message history
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    raise ValueError(
        f"Agent exceeded {MAX_ROUNDS} tool-call rounds. "
        "Partial results were printed above."
    )

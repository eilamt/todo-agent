"""CLI entry point for todo-agent.

Handles two paths:
  - Reserved subcommands: `todo visualize [scope]`
  - Free text: `todo "add a lane called Work"` → LLM agent loop → operations dispatch
"""
import json
import sys

from todo_agent.config import load_config
from todo_agent.core import operations
from todo_agent.core.operations import AmbiguousMatchError
from todo_agent.core.store import load_data


def _confirm(prompt: str) -> bool:
    """Print prompt and return True if the user types 'y'."""
    sys.stdout.write(prompt)
    sys.stdout.flush()
    answer = sys.stdin.readline().strip().lower()
    return answer == "y"


def _dispatch(tool_name: str, tool_input: dict) -> str:
    """Route a resolved tool call to the appropriate operation, print a result, and return it."""

    # --- Add operations ---
    if tool_name == "add_lane":
        lane = operations.add_lane(tool_input["name"])
        msg = f"Added lane '{lane['name']}'."
        print(msg)
        return msg

    elif tool_name == "add_project":
        project = operations.add_project(
            lane_name=tool_input["lane_name"],
            project_name=tool_input["project_name"],
            importance=tool_input.get("importance", 50),
        )
        msg = f"Added project '{project['name']}' to lane '{tool_input['lane_name']}'."
        print(msg)
        return msg

    elif tool_name == "add_item":
        item = operations.add_item(
            project_name=tool_input["project_name"],
            item_title=tool_input["item_title"],
            lane_name=tool_input.get("lane_name"),
            description=tool_input.get("description"),
        )
        msg = f"Added item '{item['title']}' to project '{tool_input['project_name']}'."
        print(msg)
        return msg

    # --- Status / flag / field updates ---
    elif tool_name == "set_item_status":
        item = operations.set_item_status(
            item_title=tool_input["item_title"],
            status=tool_input["status"],
            project_name=tool_input.get("project_name"),
            lane_name=tool_input.get("lane_name"),
        )
        msg = f"Updated '{item['title']}' status to '{item['status']}'."
        print(msg)
        return msg

    elif tool_name == "set_today":
        item = operations.set_today(
            item_title=tool_input["item_title"],
            value=tool_input["value"],
            project_name=tool_input.get("project_name"),
            lane_name=tool_input.get("lane_name"),
        )
        state = "marked as today" if item["today"] else "removed from today"
        msg = f"'{item['title']}' {state}."
        print(msg)
        return msg

    elif tool_name == "set_this_week":
        item = operations.set_this_week(
            item_title=tool_input["item_title"],
            value=tool_input["value"],
            project_name=tool_input.get("project_name"),
            lane_name=tool_input.get("lane_name"),
        )
        state = "marked as this-week" if item["this_week"] else "removed from this-week"
        msg = f"'{item['title']}' {state}."
        print(msg)
        return msg

    elif tool_name == "set_deadline":
        item = operations.set_deadline(
            item_title=tool_input["item_title"],
            deadline=tool_input.get("deadline"),
            project_name=tool_input.get("project_name"),
            lane_name=tool_input.get("lane_name"),
        )
        if item["deadline"]:
            msg = f"Deadline for '{item['title']}' set to {item['deadline']}."
        else:
            msg = f"Deadline for '{item['title']}' cleared."
        print(msg)
        return msg

    elif tool_name == "set_project_status":
        project = operations.set_project_status(
            project_name=tool_input["project_name"],
            status=tool_input["status"],
            start_date=tool_input.get("start_date"),
            lane_name=tool_input.get("lane_name"),
        )
        msg = f"Project '{project['name']}' status set to '{project['status']}'."
        if project.get("start_date"):
            msg += f" Start date: {project['start_date']}."
        print(msg)
        return msg

    elif tool_name == "set_importance":
        project = operations.set_importance(
            project_name=tool_input["project_name"],
            importance=tool_input["importance"],
            lane_name=tool_input.get("lane_name"),
        )
        msg = f"Project '{project['name']}' importance set to {project['importance']}."
        print(msg)
        return msg

    elif tool_name == "set_item_description":
        item = operations.set_item_description(
            item_title=tool_input["item_title"],
            description=tool_input.get("description"),
            project_name=tool_input.get("project_name"),
            lane_name=tool_input.get("lane_name"),
        )
        if item["description"] is not None:
            msg = f"Description for '{item['title']}' set."
        else:
            msg = f"Description for '{item['title']}' cleared."
        print(msg)
        return msg

    elif tool_name == "set_item_importance":
        item = operations.set_item_importance(
            item_title=tool_input["item_title"],
            importance=tool_input["importance"],
            project_name=tool_input.get("project_name"),
            lane_name=tool_input.get("lane_name"),
        )
        msg = f"Importance for '{item['title']}' set to {item['importance']}."
        print(msg)
        return msg

    # --- Delete operations (with confirmation) ---
    elif tool_name == "delete_lane":
        data = load_data()
        preview = operations.get_delete_preview(
            data, "lane", lane_name=tool_input["lane_name"]
        )
        plural_p = "project" if preview["projects_count"] == 1 else "projects"
        plural_i = "item" if preview["items_count"] == 1 else "items"
        confirmed = _confirm(
            f"This will permanently delete '{preview['name']}', "
            f"{preview['projects_count']} {plural_p}, and "
            f"{preview['items_count']} {plural_i}. Confirm? (y/n): "
        )
        if not confirmed:
            print("Deletion cancelled.")
            return "Deletion cancelled by user."
        result = operations.delete_lane(tool_input["lane_name"])
        msg = (
            f"Deleted lane '{result['lane_name']}' "
            f"({result['projects_deleted']} projects, {result['items_deleted']} items removed)."
        )
        print(msg)
        return msg

    elif tool_name == "delete_project":
        data = load_data()
        preview = operations.get_delete_preview(
            data,
            "project",
            project_name=tool_input["project_name"],
            lane_name=tool_input.get("lane_name"),
        )
        plural_i = "item" if preview["items_count"] == 1 else "items"
        confirmed = _confirm(
            f"This will permanently delete '{preview['name']}' "
            f"and {preview['items_count']} {plural_i}. Confirm? (y/n): "
        )
        if not confirmed:
            print("Deletion cancelled.")
            return "Deletion cancelled by user."
        result = operations.delete_project(
            project_name=tool_input["project_name"],
            lane_name=tool_input.get("lane_name"),
        )
        msg = (
            f"Deleted project '{result['project_name']}' "
            f"({result['items_deleted']} items removed)."
        )
        print(msg)
        return msg

    elif tool_name == "delete_item":
        data = load_data()
        preview = operations.get_delete_preview(
            data,
            "item",
            item_title=tool_input["item_title"],
            project_name=tool_input.get("project_name"),
            lane_name=tool_input.get("lane_name"),
        )
        confirmed = _confirm(
            f"This will permanently delete '{preview['name']}'. Confirm? (y/n): "
        )
        if not confirmed:
            print("Deletion cancelled.")
            return "Deletion cancelled by user."
        result = operations.delete_item(
            item_title=tool_input["item_title"],
            project_name=tool_input.get("project_name"),
            lane_name=tool_input.get("lane_name"),
        )
        msg = f"Deleted item '{result['item_title']}'."
        print(msg)
        return msg

    # --- Note operations ---
    elif tool_name == "add_project_note":
        note = operations.add_project_note(
            project_name=tool_input["project_name"],
            text=tool_input["text"],
            lane_name=tool_input.get("lane_name"),
        )
        msg = f"Note added to project '{tool_input['project_name']}' at {note['created_at']}."
        print(msg)
        return msg

    elif tool_name == "add_item_note":
        note = operations.add_item_note(
            item_title=tool_input["item_title"],
            text=tool_input["text"],
            project_name=tool_input.get("project_name"),
            lane_name=tool_input.get("lane_name"),
        )
        msg = f"Note added to item '{tool_input['item_title']}' at {note['created_at']}."
        print(msg)
        return msg

    elif tool_name == "list_notes":
        notes = operations.list_notes(
            entity_type=tool_input["entity_type"],
            name=tool_input["name"],
            project_name=tool_input.get("project_name"),
            lane_name=tool_input.get("lane_name"),
        )
        entity_label = f"{tool_input['entity_type']} '{tool_input['name']}'"
        if not notes:
            msg = f"No notes for {entity_label}."
            print(msg)
        else:
            lines = [f"Notes for {entity_label}:"]
            for note in notes:
                lines.append(f"\n[{note['created_at']}] {note['text']}")
            msg = "\n".join(lines)
            print(msg)
        return msg

    # --- Read tools ---
    elif tool_name == "list_lanes":
        result = operations.list_lanes()
        print(f"Found {len(result)} lane(s).")
        return json.dumps(result)

    elif tool_name == "list_projects":
        result = operations.list_projects(lane_name=tool_input.get("lane_name"))
        print(f"Found {len(result)} project(s).")
        return json.dumps(result)

    elif tool_name == "list_items":
        result = operations.list_items(
            project_name=tool_input.get("project_name"),
            lane_name=tool_input.get("lane_name"),
        )
        print(f"Found {len(result)} item(s).")
        return json.dumps(result)

    elif tool_name == "get_item":
        try:
            result = operations.get_item(
                item_title=tool_input["item_title"],
                project_name=tool_input.get("project_name"),
                lane_name=tool_input.get("lane_name"),
            )
            print(f"Found item '{result['title']}' in {result['lane']}/{result['project']}.")
            return json.dumps(result)
        except AmbiguousMatchError as exc:
            msg = str(exc)
            print(msg)
            return msg
        except ValueError as exc:
            msg = str(exc)
            print(msg)
            return msg

    # --- Clarification ---
    elif tool_name == "request_clarification":
        print(tool_input["question"])
        return tool_input["question"]

    else:
        msg = f"ERROR: Unknown tool '{tool_name}'."
        print(msg, file=sys.stderr)
        return msg


def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]
    argv = list(argv)

    if not argv:
        print(
            "Usage: todo \"<natural language command>\"\n"
            "       todo visualize [all|today|this-week]"
        )
        sys.exit(0)

    # Reserved subcommand: visualize
    if argv[0] == "visualize":
        scope = "all"
        if len(argv) > 1 and argv[1] in ("all", "today", "this-week"):
            scope = argv[1]
        try:
            from todo_agent.gui import server
            server.launch(scope=scope)
        except OSError:
            print(
                "Could not start GUI server: port unavailable. "
                "Try closing other instances.",
                file=sys.stderr,
            )
            sys.exit(1)
        return

    # Free-text path — join all args as the natural-language input
    free_text = " ".join(argv).strip()

    try:
        config = load_config()
        data = load_data()
        from todo_agent.cli.agent import run_agent
        summary = run_agent(free_text, data, config, _dispatch)
        print(summary)
    except AmbiguousMatchError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()

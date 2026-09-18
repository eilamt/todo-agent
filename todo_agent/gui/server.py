"""Flask local web server for the to-do agent GUI.

All routes call core.operations functions — this module never touches the
data file directly (constitution Principle II).

The server binds to 127.0.0.1 only and is never reachable from outside the
local machine (constitution Principle I).
"""
import os
import socket
import webbrowser
from email.utils import formatdate

from flask import Flask, jsonify, render_template, request

from todo_agent.config import get_data_file_path
from todo_agent.core import operations
from todo_agent.core.store import load_data, recalculate_percent_complete, save_data

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _http_date(timestamp: float) -> str:
    """Convert a POSIX timestamp to an HTTP-date string (RFC 7231)."""
    return formatdate(timestamp, usegmt=True)


def _mtime() -> float:
    """Return the mtime of the data file, or 0 if it does not exist."""
    path = get_data_file_path()
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0.0


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/data", methods=["GET"])
def get_data():
    mtime = _mtime()
    last_modified = _http_date(mtime)

    if_modified_since = request.headers.get("If-Modified-Since")
    if if_modified_since and if_modified_since == last_modified:
        return ("", 304)

    data = load_data()
    response = jsonify(data)
    response.headers["Last-Modified"] = last_modified
    return response


@app.route("/api/lanes", methods=["POST"])
def create_lane():
    body = request.get_json(force=True) or {}
    name = body.get("name", "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400
    try:
        lane = operations.add_lane(name)
        return jsonify(lane), 201
    except ValueError as exc:
        status = 409 if "already exists" in str(exc) else 400
        return jsonify({"error": str(exc)}), status


@app.route("/api/lanes/<lane_id>", methods=["DELETE"])
def delete_lane(lane_id: str):
    data = load_data()
    try:
        lane = operations._find_lane_by_id(data, lane_id)
    except ValueError:
        return jsonify({"error": "Lane not found"}), 404
    result = operations.delete_lane(lane["name"])
    return jsonify({"deleted": result}), 200


@app.route("/api/lanes/<lane_id>/projects", methods=["POST"])
def create_project(lane_id: str):
    data = load_data()
    try:
        lane = operations._find_lane_by_id(data, lane_id)
    except ValueError:
        return jsonify({"error": "Lane not found"}), 404

    body = request.get_json(force=True) or {}
    name = body.get("name", "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400
    importance = body.get("importance", 50)
    try:
        project = operations.add_project(
            lane_name=lane["name"],
            project_name=name,
            importance=importance,
        )
        return jsonify(project), 201
    except ValueError as exc:
        status = 409 if "already exists" in str(exc) else 400
        return jsonify({"error": str(exc)}), status


@app.route("/api/projects/<project_id>", methods=["PATCH"])
def update_project(project_id: str):
    data = load_data()
    try:
        lane, project = operations._find_project_by_id(data, project_id)
    except ValueError:
        return jsonify({"error": "Project not found"}), 404

    body = request.get_json(force=True) or {}
    current_name = project["name"]
    try:
        # Process name first — subsequent handlers use the updated name
        if "name" in body:
            operations.rename_project(
                project_name=current_name,
                new_name=body["name"],
                lane_name=lane["name"],
            )
            current_name = body["name"].strip()
        if "status" in body:
            operations.set_project_status(
                project_name=current_name,
                status=body["status"],
                start_date=body.get("start_date"),
                lane_name=lane["name"],
            )
        if "importance" in body:
            operations.set_importance(
                project_name=current_name,
                importance=body["importance"],
                lane_name=lane["name"],
            )
    except ValueError as exc:
        status_code = 409 if "already exists" in str(exc) else 400
        return jsonify({"error": str(exc)}), status_code

    # Return the fresh project state
    data = load_data()
    lane, project = operations._find_project_by_id(data, project_id)
    return jsonify(project), 200


@app.route("/api/projects/<project_id>", methods=["DELETE"])
def delete_project(project_id: str):
    data = load_data()
    try:
        lane, project = operations._find_project_by_id(data, project_id)
    except ValueError:
        return jsonify({"error": "Project not found"}), 404
    result = operations.delete_project(
        project_name=project["name"],
        lane_name=lane["name"],
    )
    return jsonify({"deleted": result}), 200


@app.route("/api/projects/<project_id>/items", methods=["POST"])
def create_item(project_id: str):
    data = load_data()
    try:
        lane, project = operations._find_project_by_id(data, project_id)
    except ValueError:
        return jsonify({"error": "Project not found"}), 404

    body = request.get_json(force=True) or {}
    title = body.get("title", "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400
    try:
        item = operations.add_item(
            project_name=project["name"],
            item_title=title,
            lane_name=lane["name"],
        )
        return jsonify(item), 201
    except ValueError as exc:
        status = 409 if "already exists" in str(exc) else 400
        return jsonify({"error": str(exc)}), status


@app.route("/api/items/<item_id>", methods=["PATCH"])
def update_item(item_id: str):
    data = load_data()
    try:
        lane, project, item = operations._find_item_by_id(data, item_id)
    except ValueError:
        return jsonify({"error": "Item not found"}), 404

    body = request.get_json(force=True) or {}
    current_title = item["title"]
    try:
        # Process title first — subsequent handlers use the updated title
        if "title" in body:
            operations.rename_item(
                item_title=current_title,
                new_title=body["title"],
                project_name=project["name"],
                lane_name=lane["name"],
            )
            current_title = body["title"].strip()
        if "status" in body:
            operations.set_item_status(
                item_title=current_title,
                status=body["status"],
                project_name=project["name"],
                lane_name=lane["name"],
            )
        if "today" in body:
            operations.set_today(
                item_title=current_title,
                value=body["today"],
                project_name=project["name"],
                lane_name=lane["name"],
            )
        if "this_week" in body:
            operations.set_this_week(
                item_title=current_title,
                value=body["this_week"],
                project_name=project["name"],
                lane_name=lane["name"],
            )
        if "deadline" in body:
            operations.set_deadline(
                item_title=current_title,
                deadline=body["deadline"],
                project_name=project["name"],
                lane_name=lane["name"],
            )
        if "description" in body:
            operations.set_item_description(
                item_title=current_title,
                description=body.get("description"),
                project_name=project["name"],
                lane_name=lane["name"],
            )
        if "importance" in body:
            operations.set_item_importance(
                item_title=current_title,
                importance=body["importance"],
                project_name=project["name"],
                lane_name=lane["name"],
            )
    except ValueError as exc:
        status_code = 409 if "already exists" in str(exc) else 400
        return jsonify({"error": str(exc)}), status_code

    # Return fresh state including updated percent_complete
    data = load_data()
    lane, project, item = operations._find_item_by_id(data, item_id)
    return jsonify({
        "item": item,
        "project_percent_complete": project["percent_complete"],
    }), 200


@app.route("/api/items/<item_id>", methods=["DELETE"])
def delete_item(item_id: str):
    data = load_data()
    try:
        lane, project, item = operations._find_item_by_id(data, item_id)
    except ValueError:
        return jsonify({"error": "Item not found"}), 404
    result = operations.delete_item(
        item_title=item["title"],
        project_name=project["name"],
        lane_name=lane["name"],
    )
    return jsonify({
        "deleted": {"item_title": result["item_title"]},
        "project_percent_complete": result["project_percent_complete"],
    }), 200


# ---------------------------------------------------------------------------
# Launch helper
# ---------------------------------------------------------------------------

def _find_free_port(start: int = 5173) -> int:
    """Find an available port starting from `start`."""
    for port in range(start, start + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise OSError("No available port found in range 5173–5272.")


def launch(scope: str = "all") -> None:
    """Start the Flask server and open the browser."""
    port = _find_free_port()
    url = f"http://127.0.0.1:{port}/?view={scope}"
    webbrowser.open(url)
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)

"""Contract tests — validate all 22 tool definitions are well-formed JSON Schema."""
from todo_agent.tools import TOOLS


def test_tool_count():
    assert len(TOOLS) == 22, f"Expected 22 tools, got {len(TOOLS)}"


def test_all_tool_names_present_and_non_empty():
    for tool in TOOLS:
        assert "name" in tool, f"Tool missing 'name': {tool}"
        assert isinstance(tool["name"], str) and tool["name"], f"Tool 'name' must be non-empty string"


def test_all_tools_have_description():
    for tool in TOOLS:
        assert "description" in tool, f"Tool '{tool.get('name')}' missing 'description'"
        assert tool["description"], f"Tool '{tool['name']}' has empty 'description'"


def test_all_tools_have_valid_input_schema():
    for tool in TOOLS:
        schema = tool.get("input_schema", {})
        name = tool.get("name")
        assert schema.get("type") == "object", f"Tool '{name}': input_schema.type must be 'object'"
        assert isinstance(schema.get("properties"), dict), f"Tool '{name}': input_schema.properties must be a dict"
        assert isinstance(schema.get("required"), list), f"Tool '{name}': input_schema.required must be a list"


def test_required_fields_exist_in_properties():
    for tool in TOOLS:
        schema = tool.get("input_schema", {})
        name = tool.get("name")
        properties = schema.get("properties", {})
        for req in schema.get("required", []):
            assert req in properties, (
                f"Tool '{name}': required field '{req}' not found in properties"
            )


def test_project_status_enum():
    tool = next(t for t in TOOLS if t["name"] == "set_project_status")
    enum = tool["input_schema"]["properties"]["status"]["enum"]
    assert set(enum) == {"not-started", "scheduled", "in-progress", "completed"}


def test_item_status_enum():
    tool = next(t for t in TOOLS if t["name"] == "set_item_status")
    enum = tool["input_schema"]["properties"]["status"]["enum"]
    assert set(enum) == {"not-started", "in-progress", "completed"}


def test_list_notes_entity_type_enum():
    tool = next(t for t in TOOLS if t["name"] == "list_notes")
    enum = tool["input_schema"]["properties"]["entity_type"]["enum"]
    assert set(enum) == {"project", "item"}


def test_set_item_description_required_fields():
    tool = next(t for t in TOOLS if t["name"] == "set_item_description")
    assert tool["input_schema"]["required"] == ["item_title", "description"]


def test_set_item_importance_required_fields_and_range():
    tool = next(t for t in TOOLS if t["name"] == "set_item_importance")
    assert tool["input_schema"]["required"] == ["item_title", "importance"]
    importance_prop = tool["input_schema"]["properties"]["importance"]
    assert importance_prop["minimum"] == 0
    assert importance_prop["maximum"] == 100


def test_list_lanes_no_required_fields():
    tool = next(t for t in TOOLS if t["name"] == "list_lanes")
    assert tool["input_schema"]["required"] == []


def test_list_projects_optional_lane_name():
    tool = next(t for t in TOOLS if t["name"] == "list_projects")
    assert "lane_name" in tool["input_schema"]["properties"]
    assert "lane_name" not in tool["input_schema"]["required"]


def test_list_items_optional_filters():
    tool = next(t for t in TOOLS if t["name"] == "list_items")
    props = tool["input_schema"]["properties"]
    required = tool["input_schema"]["required"]
    assert "project_name" in props
    assert "lane_name" in props
    assert "project_name" not in required
    assert "lane_name" not in required


def test_get_item_required_fields():
    tool = next(t for t in TOOLS if t["name"] == "get_item")
    assert tool["input_schema"]["required"] == ["item_title"]
    props = tool["input_schema"]["properties"]
    assert "project_name" in props
    assert "lane_name" in props

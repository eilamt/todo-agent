"""Contract tests — validate all 16 tool definitions are well-formed JSON Schema."""
from todo_agent.tools import TOOLS


def test_tool_count():
    assert len(TOOLS) == 16, f"Expected 16 tools, got {len(TOOLS)}"


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

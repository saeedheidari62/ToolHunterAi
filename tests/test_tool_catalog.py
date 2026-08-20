from backend.tool_catalog import ToolCatalog


def test_catalog_loads_all_canonical_tools():
    catalog = ToolCatalog()
    tools = catalog.all()
    assert len(tools) == 8
    assert all(tool["id"] for tool in tools)


def test_catalog_selects_requested_tools_only():
    catalog = ToolCatalog()
    selected = catalog.select(["bosch_gbh_2_26", "makita_hr2470"])
    assert [tool["id"] for tool in selected] == ["bosch_gbh_2_26", "makita_hr2470"]

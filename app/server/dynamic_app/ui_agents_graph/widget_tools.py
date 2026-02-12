import json
from langchain.tools import tool
from dynamic_app.configs.schemas.widget_schemas.a2ui_custom_catalog_list import CUSTOM_CATALOG
from dynamic_app.configs.schemas.native_examples.catalog import NATIVE_EXAMPLES_CATALOG

@tool()
async def get_widget_schema(widget_name: str) -> str:
    """Returns the widget template schema for the given widget name

    Args:
        widget_name: name of the widget to discover the template schema
    """
    for widget in CUSTOM_CATALOG:
        if widget["widget-name"] == widget_name:
            return widget["schema"]
    return f"No schema found for widget '{widget_name}'"

@tool()
async def get_widget_catalog() -> str:
    """Returns the list of widget names and short descriptions in JSON format"""
    catalog = [
        {"name": widget["widget-name"], "description": widget["description"]}
        for widget in CUSTOM_CATALOG
    ]
    return json.dumps(catalog, indent=2)

@tool()
async def get_native_component_example(component_name: str) -> str:
    """Returns a complete A2UI message example for the given native component

    Args:
        component_name: name of the native component (e.g., "Text", "Button", "Image")
    """
    for example in NATIVE_EXAMPLES_CATALOG:
        if example["component-name"] == component_name:
            return example["example"]
    return f"No example found for native component '{component_name}'"

@tool()
async def get_native_component_catalog() -> str:
    """Returns the list of available native component names and descriptions in JSON format"""
    catalog = [
        {"name": example["component-name"], "description": example["description"]}
        for example in NATIVE_EXAMPLES_CATALOG
    ]
    return json.dumps(catalog, indent=2)

import json
from langchain.tools import tool
from core.dynamic_app.schemas.widget_schemas.a2ui_custom_catalog_list import CUSTOM_CATALOG
from core.dynamic_app.schemas.native_examples.catalog import NATIVE_EXAMPLES_CATALOG

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

def create_custom_component_tools(inline_catalog, allowed_components=None):
    """Creates tools for custom components from the inline catalog

    Args:
        inline_catalog: List of custom component definitions
        allowed_components: Optional list of allowed component names. If provided,
                           only these components will be available to the tools.
    """

    @tool()
    async def get_custom_component_catalog() -> str:
        """Returns the list of available custom component names"""
        if allowed_components:
            # Filter to only allowed components
            component_names = [name for name in allowed_components if any((item.get("name") or item.get("widget-name", "")).lower() == name.lower() for item in inline_catalog)]
        else:
            component_names = [(item.get("name") or item.get("widget-name", "")) for item in inline_catalog if item.get("name") or item.get("widget-name")]
        return json.dumps({"available_components": component_names})

    @tool()
    async def get_custom_component_example(component_name: str) -> str:
        """Returns the A2UI message example for a custom component

        Args:
            component_name: name of the custom component (e.g., "BarGraph")
        """
        # Check if component is allowed
        if allowed_components and component_name not in [comp.lower() for comp in allowed_components]:
            return f"Component '{component_name}' is not in the allowed list: {allowed_components}"

        # Get example from inline catalog first
        for item in inline_catalog:
            item_name = item.get("name") or item.get("widget-name", "")
            if item_name.lower() == component_name.lower():
                return item.get("schema", str(item))

        # Fallback to CUSTOM_CATALOG
        for cat in CUSTOM_CATALOG:
            if cat["widget-name"].lower() == component_name.lower():
                return cat["schema"]

        return f"No example found for custom component '{component_name}'"

    return get_custom_component_catalog, get_custom_component_example

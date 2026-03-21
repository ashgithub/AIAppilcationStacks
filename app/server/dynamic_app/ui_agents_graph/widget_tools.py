import json
from langchain.tools import tool
from core.dynamic_app.schemas.widget_schemas.a2ui_custom_catalog_list import CUSTOM_CATALOG
from core.dynamic_app.schemas.native_examples.catalog import NATIVE_EXAMPLES_CATALOG

def _normalize_component_name(value: str) -> str:
    return "".join(ch for ch in str(value).strip().lower() if ch.isalnum())


def _build_native_alias_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for example in NATIVE_EXAMPLES_CATALOG:
        canonical = example.get("component-name", "")
        if not canonical:
            continue
        lookup[_normalize_component_name(canonical)] = canonical

    # Helpful aliases frequently produced by models.
    aliases = {
        "text": "Text",
        "card": "Card",
        "row": "Row",
        "column": "Column",
        "table": "Table",
        "timeline": "Timeline",
        "map": "Map",
    }
    for alias, canonical in aliases.items():
        if _normalize_component_name(canonical) in lookup:
            lookup[_normalize_component_name(alias)] = lookup[_normalize_component_name(canonical)]
    return lookup


NATIVE_COMPONENT_LOOKUP = _build_native_alias_lookup()


#region Catalog Tools
@tool()
async def get_widget_schema(widget_name: str) -> str:
    """Return the widget template schema for a given widget name."""
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
    """Return a complete A2UI example for a native component."""
    normalized = _normalize_component_name(component_name)
    canonical = NATIVE_COMPONENT_LOOKUP.get(normalized, component_name)
    for example in NATIVE_EXAMPLES_CATALOG:
        if example["component-name"] == canonical:
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
#endregion


#region Dynamic Tools
def create_custom_component_tools(inline_catalog, allowed_components=None):
    """Create custom-component tool wrappers from inline catalog definitions."""
    def _catalog_name(item):
        return item.get("name") or item.get("widget-name", "")

    @tool()
    async def get_custom_component_catalog() -> str:
        """Returns the list of available custom component names"""
        if allowed_components:
            allowed_lookup = {name.lower() for name in allowed_components}
            component_names = [
                _catalog_name(item)
                for item in inline_catalog
                if _catalog_name(item) and _catalog_name(item).lower() in allowed_lookup
            ]
        else:
            component_names = [
                _catalog_name(item)
                for item in inline_catalog
                if _catalog_name(item)
            ]
        return json.dumps({"available_components": component_names})

    @tool()
    async def get_custom_component_example(component_name: str) -> str:
        """Return the A2UI example schema for a custom component."""
        if allowed_components and component_name.lower() not in [comp.lower() for comp in allowed_components]:
            return f"Component '{component_name}' is not in the allowed list: {allowed_components}"

        for item in inline_catalog:
            item_name = item.get("name") or item.get("widget-name", "")
            if item_name.lower() == component_name.lower():
                return item.get("schema", str(item))

        for cat in CUSTOM_CATALOG:
            if cat["widget-name"].lower() == component_name.lower():
                return cat["schema"]

        return f"No example found for custom component '{component_name}'"

    return get_custom_component_catalog, get_custom_component_example
#endregion

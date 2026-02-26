"""
Utilities for A2UI schema loading and manipulation.
"""
import json
import logging
import os
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def load_a2ui_schema() -> str:
    """Load the A2UI schema from file."""
    schema_path = os.path.join(os.path.dirname(__file__), 'schemas', 'a2ui_native_schema.json')
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            return json.dumps(json.load(f), indent=2)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load a2ui schema: {e}")
        return "{}"

def inject_custom_schemas_into_schema(schema_str: str, custom_schemas: List[Dict], allowed_components: List[str] = None) -> str:
    """Inject custom component schemas into the A2UI schema, optionally filtering to allowed components."""
    if not custom_schemas:
        return schema_str
    try:
        schema_obj = json.loads(schema_str)
        component_properties = schema_obj["properties"]["surfaceUpdate"]["properties"]["components"]["items"]["properties"]["component"]["properties"]
        for custom_schema in custom_schemas:
            if "name" in custom_schema and "schema" in custom_schema:
                component_name = custom_schema["name"]
                # If allowed_components specified, only include those
                if allowed_components and component_name.lower() not in [c.lower() for c in allowed_components]:
                    continue
                component_schema = custom_schema["schema"]
                component_properties[component_name] = component_schema
        return json.dumps(schema_obj, indent=2)
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Failed to inject custom schemas: {e}")
        return schema_str

def create_array_schema_validator(single_message_schema_str: str) -> Dict[str, Any]:
    """Create an array schema validator from a single message schema."""
    try:
        single_message_schema = json.loads(single_message_schema_str)
        return {"type": "array", "items": single_message_schema}
    except json.JSONDecodeError as e:
        logger.error(f"Failed to create array schema validator: {e}")
        return None
    
def extract_allowed_components(data: str) -> List[str]:
    """Extract the list of allowed component names from orchestrator output."""
    try:
        parsed = json.loads(data)
        if isinstance(parsed, dict) and 'widgets' in parsed:
            widget_names = [widget.get('name', '').lower() for widget in parsed['widgets']]
            return widget_names if widget_names else None
    except (json.JSONDecodeError, TypeError):
        pass
    # Return None to indicate no filtering should be applied
    return None

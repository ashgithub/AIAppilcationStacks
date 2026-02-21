import importlib
import os

def _get_widget_modules():
    """Automatically discover widget modules in this directory."""
    current_dir = os.path.dirname(__file__)
    excluded_files = {"__init__.py", "a2ui_custom_catalog_list.py"}

    modules = []
    for filename in os.listdir(current_dir):
        if filename.endswith('.py') and filename not in excluded_files:
            module_name = filename[:-3]  # Remove .py extension
            modules.append(module_name)
    return modules

def _load_widget(module_name):
    """Load a widget module and return its definition."""
    try:
        module = importlib.import_module(f"core.dynamic_app.schemas.widget_schemas.{module_name}")
        return {
            "widget-name": module.WIDGET_NAME,
            "description": module.WIDGET_DESCRIPTION,
            "schema": module.WIDGET_SCHEMA
        }
    except (ImportError, AttributeError) as e:
        print(f"Warning: Could not load widget from {module_name}: {e}")
        return None

# Automatically build the catalog from all widget modules in the directory
WIDGET_MODULES = _get_widget_modules()
CUSTOM_CATALOG = [
    widget for module in WIDGET_MODULES
    if (widget := _load_widget(module)) is not None
]

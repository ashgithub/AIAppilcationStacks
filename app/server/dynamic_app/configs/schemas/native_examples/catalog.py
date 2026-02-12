import importlib
import os

def _get_native_example_modules():
    """Automatically discover native component example modules in this directory."""
    current_dir = os.path.dirname(__file__)
    excluded_files = {"__init__.py", "catalog.py"}

    modules = []
    for filename in os.listdir(current_dir):
        if filename.endswith('.py') and filename not in excluded_files:
            module_name = filename[:-3]  # Remove .py extension
            modules.append(module_name)
    return modules

def _load_native_example(module_name):
    """Load a native component example module and return its definition."""
    try:
        module = importlib.import_module(f"dynamic_app.configs.schemas.native_examples.{module_name}")
        return {
            "component-name": module.COMPONENT_NAME,
            "description": module.COMPONENT_DESCRIPTION,
            "example": module.EXAMPLE_A2UI_MESSAGE
        }
    except (ImportError, AttributeError) as e:
        print(f"Warning: Could not load native example from {module_name}: {e}")
        return None

# Automatically build the catalog from all native example modules in the directory
NATIVE_MODULES = _get_native_example_modules()
NATIVE_EXAMPLES_CATALOG = [
    example for module in NATIVE_MODULES
    if (example := _load_native_example(module)) is not None
]
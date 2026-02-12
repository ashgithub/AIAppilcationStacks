#!/usr/bin/env python3
import sys
sys.path.append('app/server')

from dynamic_app.configs.schemas.widget_schemas.a2ui_custom_catalog_list import CUSTOM_CATALOG

print(f'Catalog loaded: {len(CUSTOM_CATALOG)} widgets')
for widget in CUSTOM_CATALOG:
    print(f'- {widget["widget-name"]}: {widget["description"][:50]}...')

# Test the tools
from dynamic_app.ui_agents_graph.widget_tools import get_widget_catalog, get_widget_schema
import asyncio

async def test_tools():
    print("\nTesting get_widget_catalog:")
    catalog = await get_widget_catalog()
    print(catalog)

    print("\nTesting get_widget_schema for 'bar-graph':")
    schema = await get_widget_schema("bar-graph")
    print(f"Schema length: {len(schema)} characters")
    print(f"Schema starts with: {schema[:100]}...")

asyncio.run(test_tools())
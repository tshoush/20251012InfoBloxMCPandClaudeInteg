#!/usr/bin/env python3
"""
InfoBlox MCP Server
Dynamic Model Context Protocol server for InfoBlox WAPI
Automatically discovers and exposes all WAPI endpoints as tools
"""

import json
import os
import hashlib
from typing import Any, Dict, List, Optional
from datetime import datetime
import requests
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, GetPromptResult, Prompt, PromptMessage

# InfoBlox Configuration
INFOBLOX_HOST = os.getenv("INFOBLOX_HOST", "192.168.1.224")
INFOBLOX_USER = os.getenv("INFOBLOX_USER", "admin")
INFOBLOX_PASSWORD = os.getenv("INFOBLOX_PASSWORD", "infoblox")
WAPI_VERSION = os.getenv("WAPI_VERSION", "v2.13.1")
BASE_URL = f"https://{INFOBLOX_HOST}/wapi/{WAPI_VERSION}"

# Cache configuration
CACHE_DIR = os.path.expanduser("~/.infoblox-mcp")
SCHEMAS_CACHE = os.path.join(CACHE_DIR, "schemas.json")
TOOLS_CACHE = os.path.join(CACHE_DIR, "tools.json")
CUSTOM_TOOLS_FILE = os.path.join(CACHE_DIR, "custom_tools.json")
SCHEMA_HASH_FILE = os.path.join(CACHE_DIR, "schema_hash.txt")

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)


class InfoBloxClient:
    """Client for InfoBlox WAPI"""

    def __init__(self):
        self.session = requests.Session()
        self.session.auth = (INFOBLOX_USER, INFOBLOX_PASSWORD)
        self.session.verify = False
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make WAPI request"""
        url = f"{BASE_URL}/{path.lstrip('/')}"
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            response.raise_for_status()

            # Handle empty responses
            if not response.text or response.text.strip() == "":
                return {"success": True, "message": "Operation completed"}

            return response.json()
        except requests.exceptions.HTTPError as e:
            return {"error": str(e), "status_code": e.response.status_code}
        except Exception as e:
            return {"error": str(e)}

    def get(self, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """GET request"""
        return self.request("GET", path, params=params)

    def post(self, path: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """POST request"""
        return self.request("POST", path, json=data)

    def put(self, path: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """PUT request"""
        return self.request("PUT", path, json=data)

    def delete(self, path: str) -> Dict[str, Any]:
        """DELETE request"""
        return self.request("DELETE", path)

    def get_object_schema(self, object_type: str) -> Optional[Dict]:
        """Get schema for specific object type"""
        result = self.get(f"{object_type}?_schema")
        if "error" not in result:
            return result
        return None

    def test_object_exists(self, object_type: str) -> bool:
        """Test if object type exists"""
        result = self.get(f"{object_type}?_max_results=1")
        return "error" not in result


class SchemaManager:
    """Manages InfoBlox WAPI schemas"""

    def __init__(self, client: InfoBloxClient):
        self.client = client
        self.schemas = {}

    def discover_schemas(self) -> Dict[str, Any]:
        """Discover all WAPI object schemas"""
        print("Discovering InfoBlox WAPI objects...")

        # Load common object types
        object_types = self._get_common_objects()

        discovered = {}
        for obj_type in object_types:
            if self.client.test_object_exists(obj_type):
                schema = self.client.get_object_schema(obj_type)
                if schema:
                    discovered[obj_type] = schema

        self.schemas = discovered
        return discovered

    def _get_common_objects(self) -> List[str]:
        """Get list of common InfoBlox object types"""
        # This list is based on InfoBlox WAPI 2.13.1 documentation
        return [
            "network", "networkcontainer", "networkview", "ipv6network", "ipv6networkcontainer",
            "range", "ipv6range", "fixedaddress", "ipv6fixedaddress",
            "record:a", "record:aaaa", "record:ptr", "record:cname", "record:mx",
            "record:txt", "record:srv", "record:host", "record:ns",
            "zone_auth", "zone_forward", "zone_delegated", "zone_stub",
            "view", "member", "grid", "dhcpfailover",
            "adminuser", "admingroup", "permission",
            "lease", "roaminghost", "sharednetwork", "ipv6sharednetwork",
            "dhcpoptiondefinition", "ipv6dhcpoptiondefinition",
            "extensibleattributedef", "vlanview", "vlan",
            "discovery:device", "discovery:deviceinterface",
            "networkuser", "macfilteraddress",
            "threatprotection:profile", "threatprotection:rule"
        ]

    def load_cached_schemas(self) -> Optional[Dict[str, Any]]:
        """Load schemas from cache"""
        if os.path.exists(SCHEMAS_CACHE):
            try:
                with open(SCHEMAS_CACHE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading cached schemas: {e}")
        return None

    def save_schemas(self, schemas: Dict[str, Any]):
        """Save schemas to cache"""
        with open(SCHEMAS_CACHE, 'w') as f:
            json.dump(schemas, f, indent=2)

    def get_schema_hash(self, schemas: Dict[str, Any]) -> str:
        """Calculate hash of schemas for change detection"""
        schema_str = json.dumps(schemas, sort_keys=True)
        return hashlib.sha256(schema_str.encode()).hexdigest()

    def has_schema_changed(self, new_schemas: Dict[str, Any]) -> bool:
        """Check if schemas have changed (e.g., after upgrade)"""
        new_hash = self.get_schema_hash(new_schemas)

        if os.path.exists(SCHEMA_HASH_FILE):
            with open(SCHEMA_HASH_FILE, 'r') as f:
                old_hash = f.read().strip()
                if old_hash == new_hash:
                    return False

        # Save new hash
        with open(SCHEMA_HASH_FILE, 'w') as f:
            f.write(new_hash)

        return True


class ToolGenerator:
    """Generates MCP tools from InfoBlox WAPI schemas"""

    def __init__(self):
        self.generated_tools = []

    def generate_tools(self, schemas: Dict[str, Any]) -> List[Tool]:
        """Generate MCP tools from schemas"""
        tools = []

        for obj_type, schema in schemas.items():
            # Generate CRUD tools for each object type
            tools.extend(self._generate_crud_tools(obj_type, schema))

        self.generated_tools = tools
        return tools

    def _generate_crud_tools(self, obj_type: str, schema: Dict[str, Any]) -> List[Tool]:
        """Generate CRUD tools for an object type"""
        tools = []
        fields = schema.get('fields', [])

        # Clean object type name for tool naming
        clean_name = obj_type.replace(':', '_').replace('-', '_')

        # LIST tool
        tools.append(Tool(
            name=f"infoblox_list_{clean_name}",
            description=f"List {obj_type} objects from InfoBlox. Returns a list of {obj_type} records with their references and basic fields.",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 100)",
                        "default": 100
                    },
                    "return_fields": {
                        "type": "string",
                        "description": "Comma-separated list of fields to return (optional)"
                    },
                    "search_fields": {
                        "type": "object",
                        "description": "Field-value pairs for filtering results"
                    }
                }
            }
        ))

        # GET tool
        tools.append(Tool(
            name=f"infoblox_get_{clean_name}",
            description=f"Get a specific {obj_type} object by reference. Returns detailed information about a single {obj_type} record.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ref": {
                        "type": "string",
                        "description": f"The _ref of the {obj_type} object to retrieve"
                    },
                    "return_fields": {
                        "type": "string",
                        "description": "Comma-separated list of fields to return (optional)"
                    }
                },
                "required": ["ref"]
            }
        ))

        # CREATE tool
        searchable_fields = self._extract_searchable_fields(fields)
        tools.append(Tool(
            name=f"infoblox_create_{clean_name}",
            description=f"Create a new {obj_type} object in InfoBlox. Returns the reference of the created object.",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "object",
                        "description": f"Object data for creating {obj_type}. Common fields: {', '.join(searchable_fields[:10])}"
                    }
                },
                "required": ["data"]
            }
        ))

        # UPDATE tool
        tools.append(Tool(
            name=f"infoblox_update_{clean_name}",
            description=f"Update an existing {obj_type} object. Requires the object reference (_ref).",
            inputSchema={
                "type": "object",
                "properties": {
                    "ref": {
                        "type": "string",
                        "description": f"The _ref of the {obj_type} object to update"
                    },
                    "data": {
                        "type": "object",
                        "description": "Fields to update"
                    }
                },
                "required": ["ref", "data"]
            }
        ))

        # DELETE tool
        tools.append(Tool(
            name=f"infoblox_delete_{clean_name}",
            description=f"Delete a {obj_type} object by reference. This operation cannot be undone.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ref": {
                        "type": "string",
                        "description": f"The _ref of the {obj_type} object to delete"
                    }
                },
                "required": ["ref"]
            }
        ))

        # SEARCH tool with advanced options
        tools.append(Tool(
            name=f"infoblox_search_{clean_name}",
            description=f"Advanced search for {obj_type} objects with filters and pagination. Returns matching records.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filters": {
                        "type": "object",
                        "description": "Search filters as field-value pairs"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results (default: 100)",
                        "default": 100
                    },
                    "return_fields": {
                        "type": "string",
                        "description": "Fields to return (comma-separated)"
                    },
                    "paging": {
                        "type": "integer",
                        "description": "Enable paging with page size"
                    }
                }
            }
        ))

        return tools

    def _extract_searchable_fields(self, fields: List[Dict]) -> List[str]:
        """Extract searchable field names from schema"""
        searchable = []
        for field in fields:
            if isinstance(field, dict):
                name = field.get('name', '')
                is_searchable = field.get('searchable_by', False)
                if name and is_searchable:
                    searchable.append(name)
                elif name:  # Include all field names as potential
                    searchable.append(name)
        return searchable


class CustomToolManager:
    """Manages custom user-defined tools"""

    def __init__(self):
        self.custom_tools = []

    def load_custom_tools(self) -> List[Tool]:
        """Load custom tools from file"""
        if os.path.exists(CUSTOM_TOOLS_FILE):
            try:
                with open(CUSTOM_TOOLS_FILE, 'r') as f:
                    data = json.load(f)
                    # Convert dict to Tool objects
                    self.custom_tools = [Tool(**tool) for tool in data]
                    return self.custom_tools
            except Exception as e:
                print(f"Error loading custom tools: {e}")
        return []

    def save_custom_tools(self, tools: List[Tool]):
        """Save custom tools to file"""
        # Convert Tool objects to dicts
        tools_data = [tool.model_dump() for tool in tools]
        with open(CUSTOM_TOOLS_FILE, 'w') as f:
            json.dump(tools_data, f, indent=2)

    def add_custom_tool(self, tool: Tool):
        """Add a custom tool"""
        self.custom_tools.append(tool)
        self.save_custom_tools(self.custom_tools)


# Initialize MCP Server
app = Server("infoblox-mcp")

# Global state
client = InfoBloxClient()
schema_manager = SchemaManager(client)
tool_generator = ToolGenerator()
custom_tool_manager = CustomToolManager()

all_tools = []


def initialize_tools():
    """Initialize tools from schemas"""
    global all_tools

    print("=" * 80)
    print("InfoBlox MCP Server Initialization")
    print("=" * 80)

    # Check for cached schemas
    cached_schemas = schema_manager.load_cached_schemas()

    if cached_schemas:
        print("✓ Found cached schemas")
        schemas = cached_schemas
    else:
        print("Discovering WAPI schemas...")
        schemas = schema_manager.discover_schemas()
        schema_manager.save_schemas(schemas)
        print(f"✓ Discovered {len(schemas)} object types")

    # Check if schemas changed (upgrade detection)
    if schema_manager.has_schema_changed(schemas):
        print("⚠ Schema changes detected - regenerating tools")
        # Re-discover to get latest
        schemas = schema_manager.discover_schemas()
        schema_manager.save_schemas(schemas)

    # Generate tools from schemas
    print("Generating MCP tools...")
    generated_tools = tool_generator.generate_tools(schemas)
    print(f"✓ Generated {len(generated_tools)} tools from {len(schemas)} object types")

    # Load custom tools
    custom_tools = custom_tool_manager.load_custom_tools()
    if custom_tools:
        print(f"✓ Loaded {len(custom_tools)} custom tools")

    # Combine all tools
    all_tools = generated_tools + custom_tools

    print("=" * 80)
    print(f"Server ready with {len(all_tools)} total tools")
    print(f"  - Auto-generated: {len(generated_tools)}")
    print(f"  - Custom tools: {len(custom_tools)}")
    print("=" * 80)
    print()


# MCP Server Handlers

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List all available tools"""
    return all_tools


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Execute a tool"""
    try:
        # Parse tool name
        parts = name.split('_')
        if len(parts) < 3 or parts[0] != 'infoblox':
            return [TextContent(type="text", text=json.dumps({"error": "Invalid tool name"}))]

        operation = parts[1]  # list, get, create, update, delete, search
        object_type = '_'.join(parts[2:]).replace('_', ':')  # Convert back to InfoBlox format

        # Handle different operations
        result = None

        if operation == "list":
            max_results = arguments.get('max_results', 100)
            return_fields = arguments.get('return_fields', '')
            search_fields = arguments.get('search_fields', {})

            # Build query string
            params = {'_max_results': max_results}
            if return_fields:
                params['_return_fields'] = return_fields

            # Add search filters
            for field, value in search_fields.items():
                params[field] = value

            result = client.get(object_type, params=params)

        elif operation == "get":
            ref = arguments.get('ref')
            return_fields = arguments.get('return_fields', '')

            params = {}
            if return_fields:
                params['_return_fields'] = return_fields

            result = client.get(ref, params=params)

        elif operation == "create":
            data = arguments.get('data', {})
            result = client.post(object_type, data=data)

        elif operation == "update":
            ref = arguments.get('ref')
            data = arguments.get('data', {})
            result = client.put(ref, data=data)

        elif operation == "delete":
            ref = arguments.get('ref')
            result = client.delete(ref)

        elif operation == "search":
            filters = arguments.get('filters', {})
            max_results = arguments.get('max_results', 100)
            return_fields = arguments.get('return_fields', '')

            params = {'_max_results': max_results}
            if return_fields:
                params['_return_fields'] = return_fields

            # Add filters
            params.update(filters)

            result = client.get(object_type, params=params)

        else:
            result = {"error": f"Unknown operation: {operation}"}

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


@app.list_prompts()
async def list_prompts() -> List[Prompt]:
    """List available prompts"""
    return [
        Prompt(
            name="infoblox_help",
            description="Get help using the InfoBlox MCP server",
            arguments=[]
        ),
        Prompt(
            name="infoblox_examples",
            description="Show example queries for InfoBlox",
            arguments=[]
        )
    ]


@app.get_prompt()
async def get_prompt(name: str, arguments: dict) -> GetPromptResult:
    """Get prompt content"""
    if name == "infoblox_help":
        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text="Help me use the InfoBlox MCP tools. What can I do?"
                    )
                )
            ]
        )
    elif name == "infoblox_examples":
        examples = """
# InfoBlox MCP Server Examples

## List Networks
infoblox_list_network(max_results=10)

## Get Specific Network
infoblox_get_network(ref="network/ZG5zLm5ldH...:192.168.1.0/24/default")

## Create Network
infoblox_create_network(data={"network": "10.0.0.0/24", "comment": "Test network"})

## Search for Records
infoblox_search_record_a(filters={"name": "server1"}, max_results=50)

## Update Record
infoblox_update_record_a(ref="record:a/ZG5z...:192.168.1.10", data={"comment": "Updated"})

## Delete Object
infoblox_delete_network(ref="network/ZG5zLm5ldH...:10.0.0.0/24/default")
        """
        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=examples)
                )
            ]
        )


async def main():
    """Run the MCP server"""
    # Initialize tools before starting server
    initialize_tools()

    # Run server with stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

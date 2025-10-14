# Architecture Flow: Natural Language → WAPI Call

**Complete Request Flow from User Input to InfoBlox API Execution**

## Overview

This system translates natural language queries into InfoBlox WAPI API calls through a multi-stage pipeline involving Claude LLM, MCP protocol, API confirmation, and REST API execution.

## Complete Request Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INPUT                               │
│            "Show me all networks in 192.168.1.0/24"             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Natural Language
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      CLAUDE LLM (Sonnet 4.5)                    │
│  • Analyzes user intent                                         │
│  • Extracts parameters from natural language                    │
│  • Decides which tool to call                                   │
│  • Maps to structured tool call                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Tool Decision
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      MCP TOOL SELECTION                          │
│  Tool: infoblox_list_networks                                   │
│  Parameters: {                                                   │
│    "max_results": 100,                                          │
│    "return_fields": "network,comment"                           │
│  }                                                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Structured Tool Call
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│               API CONFIRMATION SYSTEM (NEW!)                     │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ 🔍 API Call Preview                                        │ │
│  │                                                            │ │
│  │ Method:     GET                                            │ │
│  │ Endpoint:   /wapi/v2.13.1/network                         │ │
│  │ Username:   admin                                          │ │
│  │ Parameters:                                                │ │
│  │   • _max_results: 100                                     │ │
│  │   • _return_fields: network,comment                       │ │
│  │                                                            │ │
│  │ Curl Equivalent:                                           │ │
│  │ curl -X GET -u admin:$INFOBLOX_PASSWORD \                 │ │
│  │   'https://192.168.1.224/wapi/v2.13.1/network?...'        │ │
│  │                                                            │ │
│  │ Execute? (yes/no/edit) [yes]: ▌                           │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ User Confirms
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   INFOBLOX WAPI REST API                         │
│  GET https://192.168.1.224/wapi/v2.13.1/network                │
│  Query Parameters:                                               │
│    _max_results=100                                             │
│    _return_fields=network,comment                               │
│  Authentication: Basic (admin:password)                         │
│  SSL Verification: Configurable                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP Response
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      RESULTS TO USER                             │
│  [                                                               │
│    {                                                             │
│      "_ref": "network/ZG5z....",                                │
│      "network": "192.168.1.0/24",                               │
│      "comment": "Management Network"                            │
│    },                                                            │
│    ...                                                           │
│  ]                                                               │
└─────────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Chat Interface Layer

**Files:**
- `claude-chat-mcp.py` - MCP server integration (140+ tools, all platforms)
- `claude-chat-rag.py` - RAG-enhanced chat with InfoBlox knowledge base (6 common tools)
- `claude-chat-infoblox.py` - Direct InfoBlox WAPI integration (6 common tools)

**Responsibilities:**
- Accept natural language input from user
- Manage conversation history
- Send requests to Claude LLM
- Display results to user

**Example User Input:**
```python
user_input = "Show me all networks in the 192.168.1.0/24 subnet"
```

### 2. Claude LLM (Anthropic API)

**Model:** `claude-sonnet-4-5-20250929`

**Capabilities:**
- Natural language understanding
- Intent extraction
- Parameter identification
- Tool selection
- Multi-turn conversation

**Input:**
```python
{
  "model": "claude-sonnet-4-5-20250929",
  "messages": [
    {"role": "user", "content": "Show me all networks in 192.168.1.0/24"}
  ],
  "tools": [
    {
      "name": "infoblox_list_networks",
      "description": "List networks from InfoBlox WAPI",
      "input_schema": {...}
    },
    ...
  ]
}
```

**Output (Tool Use):**
```python
{
  "type": "tool_use",
  "id": "toolu_123",
  "name": "infoblox_list_networks",
  "input": {
    "max_results": 100,
    "return_fields": "network,comment"
  }
}
```

### 3. MCP Protocol (Model Context Protocol)

**Two Modes:**

#### A. Direct Tool Calls (claude-chat-rag.py, claude-chat-infoblox.py)
```python
# Chat interface has built-in InfoBlox tools
tools = [
    {
        "name": "infoblox_list_networks",
        "description": "List networks from InfoBlox WAPI",
        "input_schema": {...}
    }
]

# Claude calls tool, interface executes directly
def process_tool_call(tool_name, tool_input):
    if tool_name == "infoblox_list_networks":
        return infoblox_list_networks(...)
```

#### B. MCP Server (claude-chat-mcp.py - All Platforms)
```python
# MCP server exposes 140+ InfoBlox WAPI endpoints
# Chat interface connects via stdio
mcp_manager = MCPServerManager()
await mcp_manager.connect_server("infoblox", "python", ["infoblox-mcp-server.py"])

# MCP server provides tools dynamically
tools = mcp_manager.get_all_tools()  # 140+ tools

# Call tool through MCP
result = await mcp_manager.call_tool("infoblox", "infoblox_list_networks", {...})
```

**MCP Server File:** `infoblox-mcp-server.py`
- Exposes 140+ InfoBlox WAPI endpoints as tools
- Uses stdio for communication (works on all platforms)
- Can be auto-configured in Claude Desktop (macOS/Windows)
- Works via CLI on all platforms including RHEL 7.9

### 4. API Confirmation System

**File:** `api_confirmation.py`

**Workflow:**
```python
def confirm_api_call(tool_name, tool_input):
    # 1. Map tool call to API details
    api_info = map_tool_to_api_call(tool_name, tool_input)

    # 2. Generate curl equivalent
    curl_cmd = generate_curl_command(api_info)

    # 3. Display preview
    display_api_preview(api_info, curl_cmd)

    # 4. Get user confirmation
    action = get_user_confirmation()  # yes/no/edit

    # 5. Allow parameter editing
    if action == 'edit':
        api_info = edit_parameters(api_info)

    # 6. Return decision
    return (should_execute, modified_input, username)
```

**Key Features:**
- Shows method, endpoint, parameters before execution
- Generates curl equivalent for manual reproduction
- Allows editing parameters and username
- Password never displayed (uses $INFOBLOX_PASSWORD)
- Cancel capability

### 5. InfoBlox WAPI Layer

**Files:**
- `infoblox-mcp-server.py` - Full WAPI client (140+ endpoints)
- Chat interfaces have embedded WAPI client (6 common tools)

**WAPI Client:**
```python
class InfoBloxClient:
    def wapi_request(self, method: str, path: str, **kwargs):
        url = f"{base_url}/wapi/{version}/{path}"
        response = self.session.request(method, url, **kwargs)
        return response.json()
```

**Supported Methods:**
- GET - Retrieve objects
- POST - Create objects
- PUT - Update objects
- DELETE - Remove objects

**Common Endpoints:**
- `/network` - Network management
- `/record:a` - A record management
- `/record:ptr` - PTR record management
- `/lease` - DHCP lease management
- `/zone_auth` - DNS zone management
- ... (140+ total)

### 6. Security & Configuration

**Files:**
- `config.py` - Centralized configuration management
- `validators.py` - Input validation (SQL injection, command injection prevention)
- `logging_config.py` - Structured logging (application + security audit)
- `interactive_config.py` - Interactive setup for missing configuration

**Security Features:**
- Zero hardcoded credentials
- Input validation on all user inputs
- Configurable SSL verification
- Rate limiting (3 req/sec)
- Retry logic with exponential backoff
- Comprehensive audit logging

## Complete Example Flow

### User Input
```
User: "Create a new network 10.50.0.0/24 with comment 'Test Network'"
```

### Claude LLM Processing
```
Claude analyzes:
  - Intent: CREATE network
  - Parameters extracted:
    * network: "10.50.0.0/24" (from prompt)
    * comment: "Test Network" (from prompt)
  - Tool selected: infoblox_create_network
```

### Tool Call
```json
{
  "tool": "infoblox_create_network",
  "input": {
    "network": "10.50.0.0/24",
    "comment": "Test Network"
  }
}
```

### API Confirmation Preview
```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 API Call Preview                                          │
├─────────────────────────────────────────────────────────────┤
│ Create new network                                           │
│                                                              │
│ Method:     POST                                             │
│ Endpoint:   /wapi/v2.13.1/network                           │
│ Username:   admin                                            │
│ Request Body:                                                │
│   {                                                          │
│     "network": "10.50.0.0/24",                              │
│     "comment": "Test Network"                                │
│   }                                                          │
│                                                              │
│ Curl Equivalent:                                            │
│ curl -X POST \                                              │
│   -u admin:$INFOBLOX_PASSWORD \                             │
│   -H 'Content-Type: application/json' \                     │
│   -d '{"network": "10.50.0.0/24", ...}' \                   │
│   'https://192.168.1.224/wapi/v2.13.1/network'              │
└─────────────────────────────────────────────────────────────┘

Execute? (yes/no/edit) [yes]:
```

### User Confirms
```
User: yes
```

### WAPI Execution
```python
POST https://192.168.1.224/wapi/v2.13.1/network
Headers:
  Content-Type: application/json
  Authorization: Basic YWRtaW46cGFzc3dvcmQ=
Body:
{
  "network": "10.50.0.0/24",
  "comment": "Test Network"
}

Response:
{
  "_ref": "network/ZG5zLm5ldHdvcmskMTAuNTAuMC4wLzI0LzA:10.50.0.0/24/default",
  "network": "10.50.0.0/24"
}
```

### Result to User
```
DDI Assistant: ✓ Network created successfully!

Network: 10.50.0.0/24
Reference: network/ZG5zLm5ldHdvcmskMTAuNTAuMC4wLzI0LzA:10.50.0.0/24/default
```

## RAG System (Optional Enhancement)

**Files:**
- `infoblox-rag-builder.py` - Builds vector database from WAPI schemas
- `claude-chat-rag.py` - Uses RAG for enhanced responses

**How It Works:**
```
User Query: "How do I filter by extensible attributes?"
    ↓
RAG System searches vector database for relevant InfoBlox documentation
    ↓
Retrieves documentation about EA syntax: *<EA_NAME>
    ↓
Enhances user prompt with context:
    [KNOWLEDGE BASE CONTEXT]
    To filter by extensible attributes, use *<EA_NAME> format.
    Example: {'*MARSHA': 'HDQTR2'}
    [END CONTEXT]
    User Question: How do I filter by extensible attributes?
    ↓
Claude generates response with knowledge base context
    ↓
More accurate tool selection and parameter mapping
```

## Tool Mapping: Natural Language → MCP → WAPI

| User Intent | Claude Tool | MCP Tool (if using MCP server) | WAPI Endpoint | Method |
|-------------|-------------|-------------------------------|---------------|--------|
| "List all networks" | infoblox_list_networks | infoblox_list_networks | /network | GET |
| "Get network details" | infoblox_get_network | infoblox_get_network | /network/{ref} | GET |
| "Create network" | infoblox_create_network | infoblox_create_network | /network | POST |
| "Search A records" | infoblox_search_records | infoblox_search_records | /record:a | GET |
| "List DHCP leases" | infoblox_list_dhcp_leases | infoblox_list_dhcp_leases | /lease | GET |
| "Generic query" | infoblox_query | infoblox_query | /{object_type} | GET |

## Platform Differences

### MCP Server: Works on All Platforms

**Important:** MCP works on **all platforms** (macOS, Linux, Windows) via CLI!

```bash
python claude-chat-mcp.py  # 140+ tools via MCP - works everywhere!
```

The MCP server communicates via stdio and works on any platform. The only platform difference is Claude Desktop integration.

### macOS/Windows
- ✅ Claude Desktop GUI available
- ✅ MCP server can be auto-configured in Claude Desktop
- ✅ All 3 chat interfaces work (MCP, RAG, InfoBlox)
- ✅ GUI + CLI options

### RHEL 7.9 / Linux
- ❌ No Claude Desktop GUI
- ✅ **MCP works via CLI** (`claude-chat-mcp.py` - 140+ tools)
- ✅ All 3 CLI chat interfaces work (MCP, RAG, InfoBlox)
- ✅ Full MCP functionality available

**Recommendation:**
- **All platforms**: Use `claude-chat-mcp.py` for most tools (140+ via MCP)
- **Alternative**: Use `claude-chat-rag.py` (6 common tools + InfoBlox knowledge base)
- **macOS/Windows**: Optionally use Claude Desktop GUI with MCP auto-configured

## Configuration Files

```
.env                        # Environment variables (credentials)
config.py                   # Settings management
validators.py               # Input validation
logging_config.py           # Logging setup
api_confirmation.py         # API confirmation system
interactive_config.py       # Interactive setup wizard
```

## Summary: Complete Pipeline

1. **User types natural language** → Chat interface
2. **Chat sends to Claude LLM** → Intent extraction
3. **Claude selects tool** → Structured tool call
4. **API confirmation shows preview** → User reviews
5. **User confirms** → Proceed with execution
6. **WAPI client executes** → HTTP REST call
7. **Results returned** → Displayed to user

**Key Innovation:**
- Natural language input
- AI-powered intent extraction
- User confirmation with full visibility
- Secure, validated API execution
- Copy/paste curl equivalent for manual execution

---

**Related Documentation:**
- [API-CONFIRMATION-GUIDE.md](API-CONFIRMATION-GUIDE.md) - API confirmation system details
- [INFOBLOX-MCP-README.md](INFOBLOX-MCP-README.md) - MCP server documentation
- [RAG-SYSTEM-GUIDE.md](RAG-SYSTEM-GUIDE.md) - RAG system overview
- [README.md](README.md) - Main project documentation

**Last Updated:** October 13, 2025

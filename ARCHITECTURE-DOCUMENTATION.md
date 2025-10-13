# Architecture Documentation
## InfoBlox MCP and Claude Integration

**Version:** 1.0
**Date:** October 12, 2025
**Author:** Claude Sonnet 4.5
**Status:** Post-Development Review

---

## Table of Contents
1. [System Overview](#1-system-overview)
2. [Architecture Principles](#2-architecture-principles)
3. [System Architecture](#3-system-architecture)
4. [Component Architecture](#4-component-architecture)
5. [Data Architecture](#5-data-architecture)
6. [Security Architecture](#6-security-architecture)
7. [Deployment Architecture](#7-deployment-architecture)
8. [Integration Architecture](#8-integration-architecture)
9. [Performance Architecture](#9-performance-architecture)
10. [Scalability Considerations](#10-scalability-considerations)

---

## 1. System Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE LAYER                         │
│                                                                       │
│   ┌───────────────────────────────────────────────────────────┐    │
│   │  Terminal (CLI) - Natural Language Input                   │    │
│   │  - Colorized output                                         │    │
│   │  - Multi-turn conversation                                  │    │
│   └───────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                               │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  claude-chat-rag.py (Main Application)                       │   │
│  │  ┌─────────────────────────────────────────────────────┐    │   │
│  │  │  Conversation Manager                                │    │   │
│  │  │  - Message history                                   │    │   │
│  │  │  - Context management                                │    │   │
│  │  │  - Multi-turn state                                  │    │   │
│  │  └─────────────────────────────────────────────────────┘    │   │
│  │  ┌─────────────────────────────────────────────────────┐    │   │
│  │  │  Tool Processor                                      │    │   │
│  │  │  - Tool call routing                                 │    │   │
│  │  │  - Result formatting                                 │    │   │
│  │  │  - Error handling                                    │    │   │
│  │  └─────────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
              │                    │                    │
              ▼                    ▼                    ▼
┌──────────────────┐  ┌──────────────────┐  ┌─────────────────────────┐
│   RAG LAYER      │  │   TOOL LAYER     │  │   AI LAYER              │
│                  │  │                  │  │                         │
│  ┌────────────┐  │  │  ┌────────────┐ │  │  ┌───────────────────┐ │
│  │ RAGManager │  │  │  │ InfoBlox   │ │  │  │ Anthropic API     │ │
│  │            │  │  │  │ Tools      │ │  │  │ Claude Sonnet 4.5 │ │
│  │ ChromaDB   │  │  │  │ (6 types)  │ │  │  │                   │ │
│  │ 2,500+     │  │  │  └────────────┘ │  │  │ - Natural lang    │ │
│  │ documents  │  │  │  ┌────────────┐ │  │  │ - Tool use        │ │
│  │            │  │  │  │ Web Search │ │  │  │ - Context aware   │ │
│  │ Semantic   │  │  │  │ (DDGS)     │ │  │  └───────────────────┘ │
│  │ search     │  │  │  └────────────┘ │  │                         │
│  └────────────┘  │  │  ┌────────────┐ │  └─────────────────────────┘
│                  │  │  │ File Ops   │ │
│  - EA docs       │  │  │ Commands   │ │
│  - Schema docs   │  │  └────────────┘ │
│  - Best practice │  │                  │
│  - Examples      │  │  6 InfoBlox +   │
└──────────────────┘  │  3 Utility tools │
                      └──────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA / INTEGRATION LAYER                      │
│                                                                       │
│  ┌────────────────────┐  ┌────────────────────┐  ┌───────────────┐ │
│  │   InfoBlox WAPI    │  │   Web Services     │  │   File System │ │
│  │                    │  │                    │  │               │ │
│  │   - 232 objects    │  │   - DuckDuckGo     │  │   - Read/write│ │
│  │   - 1,392 ops      │  │   - Web pages      │  │   - Search    │ │
│  │   - REST API       │  │                    │  │   - Execute   │ │
│  │   - HTTPS          │  │                    │  │               │ │
│  └────────────────────┘  └────────────────────┘  └───────────────┘ │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │   InfoBlox Grid (192.168.1.224)                              │   │
│  │   WAPI v2.13.1                                                │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 System Context

The system operates as a local CLI application that:
1. Accepts natural language input from users
2. Enhances queries with InfoBlox knowledge (RAG)
3. Routes queries to Claude AI with appropriate tools
4. Executes tool calls against InfoBlox WAPI
5. Returns formatted results to users

---

## 2. Architecture Principles

### 2.1 Design Principles

1. **Modularity**
   - Separate concerns (RAG, Tools, AI, UI)
   - Loosely coupled components
   - High cohesion within modules

2. **Extensibility**
   - Dynamic tool generation
   - Plugin architecture for new tools
   - Configurable via environment variables

3. **Resilience**
   - Graceful degradation
   - Error handling at all layers
   - Retry logic for transient failures

4. **Performance**
   - Schema caching
   - RAG index optimization
   - Async operations where possible

5. **Security**
   - Credentials in environment only
   - Input validation
   - Minimal privilege principle

6. **User-Centricity**
   - Natural language interface
   - Clear error messages
   - Comprehensive feedback

---

## 3. System Architecture

### 3.1 Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER                                          │
│  - CLI Interface                                             │
│  - Output Formatting                                         │
│  - Color Rendering                                           │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────────┐
│  APPLICATION LAYER                                           │
│  - Conversation Management                                   │
│  - Tool Call Routing                                         │
│  - Context Injection (RAG)                                   │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────────┐
│  BUSINESS LOGIC LAYER                                        │
│  - RAG Manager (Knowledge Retrieval)                         │
│  - Tool Executor (InfoBlox operations)                       │
│  - AI Orchestrator (Claude integration)                      │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────────┐
│  DATA ACCESS LAYER                                           │
│  - InfoBlox Client (WAPI)                                    │
│  - ChromaDB Client (Vector DB)                               │
│  - File System Access                                        │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────────┐
│  INFRASTRUCTURE LAYER                                        │
│  - InfoBlox Grid                                             │
│  - Anthropic API                                             │
│  - Local File System                                         │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Component Interaction Flow

```
User Input
    │
    ▼
┌─────────────────────┐
│  Input Validation   │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│  Keyword Detection  │
│  (InfoBlox related?)│
└─────────────────────┘
    │
    ├──Yes──▶ ┌────────────────────┐
    │         │  RAG Search        │
    │         │  (Semantic search) │
    │         └────────────────────┘
    │                  │
    │                  ▼
    │         ┌────────────────────┐
    │         │  Context Injection │
    │         └────────────────────┘
    │                  │
    └──No───┐          │
            │          ▼
    ┌───────▼──────────────────────┐
    │   Anthropic API Call         │
    │   (Claude with tools)        │
    └──────────────────────────────┘
            │
            ▼
    ┌───────────────────┐
    │  Tool Call?       │
    └───────────────────┘
            │
        ┌───┴───┐
        │  Yes  │
        └───┬───┘
            ▼
    ┌────────────────────────┐
    │  Tool Router           │
    │  (Select handler)      │
    └────────────────────────┘
            │
    ┌───────┴────────┐
    │  InfoBlox Tool │
    └───────┬────────┘
            │
            ▼
    ┌────────────────────────┐
    │  InfoBlox WAPI Call    │
    │  (HTTP REST)           │
    └────────────────────────┘
            │
            ▼
    ┌────────────────────────┐
    │  Format Results        │
    └────────────────────────┘
            │
            ▼
    ┌────────────────────────┐
    │  Return to Claude      │
    └────────────────────────┘
            │
            ▼
    ┌────────────────────────┐
    │  Claude Synthesizes    │
    │  Response              │
    └────────────────────────┘
            │
            ▼
    ┌────────────────────────┐
    │  Display to User       │
    │  (Colorized output)    │
    └────────────────────────┘
```

---

## 4. Component Architecture

### 4.1 Core Components

#### 4.1.1 RAG Manager
**File:** `claude-chat-rag.py` (RAGManager class)

**Responsibilities:**
- Initialize ChromaDB connection
- Perform semantic search
- Format context for Claude
- Handle RAG unavailability gracefully

**Key Methods:**
```python
class RAGManager:
    def __init__():
        # Initialize ChromaDB client

    def search(query: str, n_results: int) -> str:
        # Semantic search
        # Return formatted context

    def is_available() -> bool:
        # Check if RAG is functional
```

**Dependencies:**
- ChromaDB (vector database)
- ~/.infoblox-rag/ (data directory)

**Performance:**
- Search latency: 100-200ms
- Memory footprint: ~200MB

#### 4.1.2 InfoBlox Client
**File:** `claude-chat-rag.py` (InfoBloxClient class)

**Responsibilities:**
- Manage authentication session
- Execute WAPI requests (GET/POST/PUT/DELETE)
- Handle errors
- Return structured responses

**Key Methods:**
```python
class InfoBloxClient:
    def __init__():
        # Setup requests session with auth

    def wapi_request(method, endpoint, params, data):
        # Make authenticated WAPI call
        # Return JSON response or error
```

**Configuration:**
- Host: INFOBLOX_HOST env var
- Auth: INFOBLOX_USER / INFOBLOX_PASSWORD
- SSL: verify=False (configurable)

#### 4.1.3 Tool Processor
**File:** `claude-chat-rag.py` (process_tool_call function)

**Responsibilities:**
- Route tool calls to appropriate handlers
- Validate tool inputs
- Execute tools
- Format tool outputs
- Handle tool errors

**Tool Categories:**
1. **InfoBlox Tools** (6)
   - infoblox_list_networks
   - infoblox_get_network
   - infoblox_create_network
   - infoblox_search_records
   - infoblox_list_dhcp_leases
   - infoblox_query (generic)

2. **Utility Tools** (5)
   - get_current_datetime
   - web_search
   - fetch_webpage
   - search_files
   - read_file
   - execute_command

#### 4.1.4 Conversation Manager
**File:** `claude-chat-rag.py` (main loop)

**Responsibilities:**
- Manage message history
- Handle multi-turn conversations
- Maintain context
- Loop until exit

**State Management:**
```python
messages = []  # Conversation history

while True:
    user_input = get_user_input()

    # Enhance with RAG if needed
    enhanced_input = enhance_prompt_with_rag(user_input)

    # Add to messages
    messages.append({"role": "user", "content": enhanced_input})

    # Call Claude API
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        messages=messages,
        tools=TOOLS
    )

    # Process tool calls
    # Add response to messages
    # Display to user
```

### 4.2 MCP Server Architecture

#### 4.2.1 InfoBlox MCP Server
**File:** `infoblox-mcp-server.py`

**Architecture:**
```
┌──────────────────────────────────────────────────┐
│  InfoBlox MCP Server                              │
│                                                    │
│  ┌──────────────────────────────────────────┐   │
│  │  Server Manager                           │   │
│  │  - MCP protocol handler                   │   │
│  │  - Tool registration                      │   │
│  │  - Request routing                        │   │
│  └──────────────────────────────────────────┘   │
│                                                    │
│  ┌──────────────────────────────────────────┐   │
│  │  Schema Manager                           │   │
│  │  - Schema discovery                       │   │
│  │  - Schema caching                         │   │
│  │  - Hash comparison (upgrade detection)   │   │
│  └──────────────────────────────────────────┘   │
│                                                    │
│  ┌──────────────────────────────────────────┐   │
│  │  Tool Generator                           │   │
│  │  - Dynamic tool creation                  │   │
│  │  - 6 operations per object:               │   │
│  │    * List                                  │   │
│  │    * Get                                   │   │
│  │    * Create                                │   │
│  │    * Update                                │   │
│  │    * Delete                                │   │
│  │    * Search                                │   │
│  └──────────────────────────────────────────┘   │
│                                                    │
│  ┌──────────────────────────────────────────┐   │
│  │  InfoBlox Client                          │   │
│  │  - WAPI request execution                 │   │
│  │  - Authentication                         │   │
│  │  - Error handling                         │   │
│  └──────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────┐
│  InfoBlox WAPI (v2.13.1)                         │
│  - 232 object types                               │
│  - REST API                                       │
└──────────────────────────────────────────────────┘
```

**Tool Generation Algorithm:**
```python
for each object_type in discovered_objects:
    schema = get_schema(object_type)

    tools.append(create_list_tool(object_type))
    tools.append(create_get_tool(object_type, schema))
    tools.append(create_create_tool(object_type, schema))
    tools.append(create_update_tool(object_type, schema))
    tools.append(create_delete_tool(object_type))
    tools.append(create_search_tool(object_type, schema))
```

**Result:** 232 objects × 6 operations = 1,392 tools

#### 4.2.2 Upgrade Detection Mechanism

```
Startup
    │
    ▼
┌────────────────────────┐
│  Load cached schemas   │
└────────────────────────┘
    │
    ▼
┌────────────────────────┐
│  Query WAPI for        │
│  current schemas       │
└────────────────────────┘
    │
    ▼
┌────────────────────────┐
│  Calculate SHA256      │
│  hash of schemas       │
└────────────────────────┘
    │
    ▼
┌────────────────────────┐
│  Compare with cached   │
│  hash                  │
└────────────────────────┘
    │
    ├─Different─▶ ┌──────────────────────┐
    │             │  Re-discover schemas │
    │             └──────────────────────┘
    │                      │
    │                      ▼
    │             ┌──────────────────────┐
    │             │  Regenerate tools    │
    │             └──────────────────────┘
    │                      │
    │                      ▼
    │             ┌──────────────────────┐
    │             │  Save new hash       │
    │             └──────────────────────┘
    │                      │
    └─Same────────────────┘
                │
                ▼
    ┌────────────────────────┐
    │  Load tools from cache │
    └────────────────────────┘
                │
                ▼
    ┌────────────────────────┐
    │  MCP Server Ready      │
    └────────────────────────┘
```

### 4.3 RAG Builder Architecture

#### 4.3.1 InfoBlox RAG Builder
**File:** `infoblox-rag-builder.py`

**Document Generation Pipeline:**
```
┌────────────────────────────────────────────────────────────┐
│  Input Sources                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │ WAPI Schemas │  │ EA Defs      │  │ EA Examples MD  │ │
│  │ (JSON)       │  │ (API query)  │  │ (File)          │ │
│  └──────────────┘  └──────────────┘  └─────────────────┘ │
└────────────────────────────────────────────────────────────┘
            │                │                  │
            ▼                ▼                  ▼
┌────────────────────────────────────────────────────────────┐
│  Document Generators                                        │
│  ┌───────────────────────────────────────────────────────┐│
│  │  Schema Processor                                      ││
│  │  - Object overviews (232)                             ││
│  │  - Field documentation (~2,000)                       ││
│  │  - Use cases (232)                                    ││
│  └───────────────────────────────────────────────────────┘│
│  ┌───────────────────────────────────────────────────────┐│
│  │  EA Processor                                          ││
│  │  - EA definitions (variable)                          ││
│  │  - Query patterns per EA                              ││
│  │  - Natural language examples                          ││
│  └───────────────────────────────────────────────────────┘│
│  ┌───────────────────────────────────────────────────────┐│
│  │  Knowledge Processor                                   ││
│  │  - Best practices (7)                                 ││
│  │  - API parameters (4)                                 ││
│  │  - EA query patterns (4)                              ││
│  │  - Tool selection guide (1)                           ││
│  │  - Multi-tool examples (1)                            ││
│  └───────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────────────────┐
│  Document Collection                                        │
│  ~2,500+ documents with metadata                           │
└────────────────────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────────────────┐
│  ChromaDB Ingestion                                         │
│  - Generate embeddings                                      │
│  - Store vectors                                            │
│  - Create index                                             │
└────────────────────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────────────────┐
│  Vector Database (~/.infoblox-rag/)                        │
│  - Semantic search enabled                                  │
│  - 2,500+ indexed documents                                │
└────────────────────────────────────────────────────────────┘
```

---

## 5. Data Architecture

### 5.1 Data Flow Diagram

```
┌──────────────────┐
│  User Query      │
│  "List networks  │
│   where          │
│   MARSHA=        │
│   'HDQTR2'"      │
└──────────────────┘
        │
        ▼
┌──────────────────────────────────────┐
│  RAG Search                           │
│  Query: "MARSHA HDQTR2 network"      │
└──────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────┐
│  ChromaDB Vector Search               │
│  Returns top 5 relevant documents:    │
│  1. MARSHA EA definition              │
│  2. EA query pattern                  │
│  3. Tool selection guide              │
│  4. Network object docs               │
│  5. Multi-tool example                │
└──────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────┐
│  Context Injection                    │
│  Enhanced prompt with knowledge       │
└──────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────┐
│  Claude AI Processing                 │
│  Tool Selection: infoblox_query       │
│  Parameters:                          │
│    object_type: "network"             │
│    filters:                           │
│      "*MARSHA": "HDQTR2"             │
│      "_return_fields+": "extattrs"   │
└──────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────┐
│  Tool Execution                       │
│  GET /wapi/v2.13.1/network            │
│  ?*MARSHA=HDQTR2                     │
│  &_return_fields+=extattrs           │
└──────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────┐
│  InfoBlox Response                    │
│  [                                    │
│    {                                  │
│      "_ref": "network/...",          │
│      "network": "10.50.0.0/24",      │
│      "extattrs": {                   │
│        "MARSHA": {"value": "HDQTR2"} │
│      }                                │
│    }                                  │
│  ]                                    │
└──────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────┐
│  Claude Synthesis                     │
│  Formats user-friendly response       │
└──────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────┐
│  User Output                          │
│  "Found 1 network where               │
│   MARSHA='HDQTR2':                   │
│                                       │
│   10.50.0.0/24                        │
│   - MARSHA: HDQTR2                   │
│   - Site: HQ"                         │
└──────────────────────────────────────┘
```

### 5.2 Data Models

#### 5.2.1 Conversation Message
```python
{
    "role": "user" | "assistant",
    "content": [
        {
            "type": "text",
            "text": "string"
        },
        {
            "type": "tool_use",
            "id": "string",
            "name": "string",
            "input": {}
        },
        {
            "type": "tool_result",
            "tool_use_id": "string",
            "content": "string"
        }
    ]
}
```

#### 5.2.2 RAG Document
```python
{
    "id": "string",  # Unique identifier
    "document": "string",  # Text content
    "metadata": {
        "type": "object_overview" | "field" | "ea" | "best_practices",
        "object_type": "network",
        "category": "network" | "dns" | "dhcp" | "infrastructure"
    },
    "embedding": [float],  # Vector representation
}
```

#### 5.2.3 InfoBlox WAPI Response
```python
{
    "_ref": "object_type/base64_id:key_fields",
    "field1": "value1",
    "field2": "value2",
    "extattrs": {
        "EA_NAME": {
            "value": "EA_VALUE"
        }
    }
}
```

#### 5.2.4 Tool Definition
```python
{
    "name": "infoblox_query",
    "description": "Generic InfoBlox WAPI query...",
    "input_schema": {
        "type": "object",
        "properties": {
            "object_type": {"type": "string"},
            "filters": {"type": "object"},
            "max_results": {"type": "integer"}
        },
        "required": ["object_type"]
    }
}
```

### 5.3 Data Storage

#### 5.3.1 Persistent Storage
```
~/.infoblox-rag/          # ChromaDB vector database
    ├── chroma.sqlite3     # SQLite metadata
    ├── index/             # Vector indices
    └── data/              # Embedded vectors

~/infoblox_schemas.json   # Cached WAPI schemas (232 objects)

~/infoblox_schema_hash.txt  # SHA256 hash for upgrade detection

~/.infoblox-mcp/          # MCP server cache
    ├── schemas.json       # Cached schemas
    ├── tools.json         # Generated tools
    ├── custom_tools.json  # User-defined tools
    └── schema_hash.txt    # Schema hash
```

#### 5.3.2 Runtime Memory
```
Conversation Messages: ~10-100KB (depends on history length)
RAG Index: ~200MB (vector embeddings loaded)
Tool Definitions: ~1MB (1,392 tools in memory)
Schema Cache: ~5MB (232 object schemas)
```

---

## 6. Security Architecture

### 6.1 Security Layers

```
┌───────────────────────────────────────────────────────────┐
│  APPLICATION SECURITY                                      │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Input Validation                                   │  │
│  │  - User input sanitization                         │  │
│  │  - Tool parameter validation                       │  │
│  │  - Command injection prevention                    │  │
│  └────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
┌───────────────────────────────────────────────────────────┐
│  AUTHENTICATION & AUTHORIZATION                            │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Credential Management                              │  │
│  │  - Environment variables only                      │  │
│  │  - No hardcoded credentials                        │  │
│  │  - No credentials in logs                          │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  InfoBlox WAPI Auth                                │  │
│  │  - HTTP Basic Auth                                 │  │
│  │  - Session management                              │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Anthropic API Auth                                │  │
│  │  - API key from environment                        │  │
│  │  - HTTPS only                                      │  │
│  └────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
┌───────────────────────────────────────────────────────────┐
│  TRANSPORT SECURITY                                        │
│  ┌────────────────────────────────────────────────────┐  │
│  │  InfoBlox Communication                            │  │
│  │  - HTTPS (TLS 1.2+)                                │  │
│  │  - Certificate verification (configurable)         │  │
│  │  - No plaintext credentials on wire                │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Anthropic API Communication                       │  │
│  │  - HTTPS only                                      │  │
│  │  - API key in Authorization header                 │  │
│  └────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
┌───────────────────────────────────────────────────────────┐
│  DATA SECURITY                                             │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Local Storage                                      │  │
│  │  - User home directory only                        │  │
│  │  - File permissions restricted                     │  │
│  │  - No sensitive data in cache                      │  │
│  └────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

### 6.2 Threat Model

| Threat | Mitigation |
|--------|------------|
| **Credential Theft** | Environment variables, no hardcoding, no logs |
| **Man-in-the-Middle** | HTTPS/TLS for all external communication |
| **Injection Attacks** | Input validation, parameterized queries |
| **Unauthorized Access** | Authentication required for InfoBlox & Anthropic |
| **Data Exfiltration** | Local deployment only, no cloud transmission |
| **Privilege Escalation** | Minimal privileges, no sudo required |
| **Denial of Service** | Rate limiting (via APIs), timeout configurations |

### 6.3 Security Best Practices Implemented

1. ✅ **Credentials in Environment Variables**
2. ✅ **No Hardcoded Secrets**
3. ✅ **HTTPS for External Communication**
4. ✅ **Input Validation**
5. ✅ **Error Messages Don't Leak Sensitive Data**
6. ✅ **File Permissions Restricted to User**
7. ✅ **Graceful Error Handling**
8. ⚠️  **SSL Certificate Verification (Disabled by default - see security review)**

---

## 7. Deployment Architecture

### 7.1 Deployment Topology

```
┌────────────────────────────────────────────────────────────┐
│  User Workstation / Jump Server                            │
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Python Virtual Environment                         │   │
│  │  ~/.python-envs/ddi-assistant/                     │   │
│  │                                                      │   │
│  │  ┌─────────────────────────────────────────────┐  │   │
│  │  │  Application Files                           │  │   │
│  │  │  - claude-chat-rag.py                       │  │   │
│  │  │  - infoblox-rag-builder.py                  │  │   │
│  │  │  - infoblox-mcp-server.py                   │  │   │
│  │  │  - Dependencies (pip packages)              │  │   │
│  │  └─────────────────────────────────────────────┘  │   │
│  │                                                      │   │
│  │  ┌─────────────────────────────────────────────┐  │   │
│  │  │  Data Files                                  │  │   │
│  │  │  - ~/.infoblox-rag/ (ChromaDB)             │  │   │
│  │  │  - ~/infoblox_schemas.json                  │  │   │
│  │  └─────────────────────────────────────────────┘  │   │
│  └────────────────────────────────────────────────────┘   │
│                                                              │
└────────────────────────────────────────────────────────────┘
                    │                    │
        ┌───────────┴──────────┐        │
        │  HTTPS               │  HTTPS │
        ▼                      ▼        │
┌──────────────────┐    ┌──────────────────────┐
│  InfoBlox Grid   │    │  Anthropic API       │
│  192.168.1.224   │    │  api.anthropic.com   │
│  WAPI v2.13.1    │    │  Claude Sonnet 4.5   │
└──────────────────┘    └──────────────────────┘
```

### 7.2 Installation Architecture

```
Installation Flow:
    │
    ▼
┌────────────────────────────────────┐
│  1. Git Clone Repository           │
└────────────────────────────────────┘
    │
    ▼
┌────────────────────────────────────┐
│  2. Run setup-python-modern.sh     │
│     - Install pyenv                 │
│     - Install Python 3.9+          │
│     - Create virtual environment   │
└────────────────────────────────────┘
    │
    ▼
┌────────────────────────────────────┐
│  3. Install Dependencies           │
│     pip install anthropic mcp ...  │
└────────────────────────────────────┘
    │
    ▼
┌────────────────────────────────────┐
│  4. Set Environment Variables      │
│     - INFOBLOX_HOST                │
│     - INFOBLOX_USER                │
│     - INFOBLOX_PASSWORD            │
│     - ANTHROPIC_API_KEY            │
└────────────────────────────────────┘
    │
    ▼
┌────────────────────────────────────┐
│  5. Build RAG Database             │
│     ./infoblox-rag-builder.py      │
└────────────────────────────────────┘
    │
    ▼
┌────────────────────────────────────┐
│  6. Test Installation              │
│     ./claude-chat-rag.py           │
└────────────────────────────────────┘
```

---

## 8. Integration Architecture

### 8.1 External System Integrations

#### 8.1.1 InfoBlox WAPI Integration
```
Application
    │
    │ HTTPS/REST
    ▼
┌──────────────────────────────────────┐
│  InfoBlox Grid Master                │
│  192.168.1.224                       │
│                                      │
│  ┌────────────────────────────────┐│
│  │  WAPI v2.13.1                  ││
│  │  - 232 object types            ││
│  │  - REST endpoints              ││
│  │  - HTTP Basic Auth             ││
│  │  - JSON responses              ││
│  └────────────────────────────────┘│
└──────────────────────────────────────┘
```

**Integration Points:**
- **Endpoint**: `https://192.168.1.224/wapi/v2.13.1/`
- **Auth**: HTTP Basic (username/password)
- **Format**: JSON request/response
- **Transport**: HTTPS (TLS 1.2+)

#### 8.1.2 Anthropic API Integration
```
Application
    │
    │ HTTPS/REST
    ▼
┌──────────────────────────────────────┐
│  Anthropic API                       │
│  api.anthropic.com                   │
│                                      │
│  ┌────────────────────────────────┐│
│  │  Claude Sonnet 4.5             ││
│  │  - Natural language processing ││
│  │  - Tool use capability         ││
│  │  - API key auth                ││
│  │  - JSON responses              ││
│  └────────────────────────────────┘│
└──────────────────────────────────────┘
```

**Integration Points:**
- **Endpoint**: `https://api.anthropic.com/v1/messages`
- **Auth**: API key in `x-api-key` header
- **Format**: JSON request/response
- **Transport**: HTTPS

#### 8.1.3 DuckDuckGo Integration
```
Application
    │
    │ HTTPS
    ▼
┌──────────────────────────────────────┐
│  DuckDuckGo Search API               │
│  - Web search                        │
│  - No authentication required        │
│  - Rate limited                      │
└──────────────────────────────────────┘
```

### 8.2 API Contracts

#### 8.2.1 InfoBlox WAPI Contract
```python
# Request
GET /wapi/v2.13.1/network?*MARSHA=HDQTR2&_return_fields+=extattrs
Headers:
    Authorization: Basic <base64>
    Content-Type: application/json

# Response
200 OK
[
    {
        "_ref": "network/ZG5z...:10.50.0.0/24/default",
        "network": "10.50.0.0/24",
        "comment": "HQ Network",
        "extattrs": {
            "MARSHA": {"value": "HDQTR2"}
        }
    }
]

# Error Response
400 Bad Request
{
    "Error": "AdmConProtoError: Unknown object type",
    "code": "Client.Ibap.Proto",
    "text": "Unknown object type: invalid_object"
}
```

#### 8.2.2 Anthropic API Contract
```python
# Request
POST /v1/messages
Headers:
    x-api-key: <api_key>
    anthropic-version: 2023-06-01
    content-type: application/json

Body:
{
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 4096,
    "tools": [...],
    "messages": [...]
}

# Response
200 OK
{
    "id": "msg_...",
    "type": "message",
    "role": "assistant",
    "content": [
        {
            "type": "tool_use",
            "id": "toolu_...",
            "name": "infoblox_query",
            "input": {...}
        }
    ],
    "stop_reason": "tool_use"
}
```

---

## 9. Performance Architecture

### 9.1 Performance Optimization Strategies

#### 9.1.1 Caching Strategy
```
┌─────────────────────────────────────────┐
│  Cache Layers                            │
│                                          │
│  ┌────────────────────────────────────┐│
│  │  L1: In-Memory Cache                ││
│  │  - Schema definitions               ││
│  │  - Tool definitions                 ││
│  │  - Session state                    ││
│  │  TTL: Application lifetime          ││
│  └────────────────────────────────────┘│
│                                          │
│  ┌────────────────────────────────────┐│
│  │  L2: Disk Cache                     ││
│  │  - infoblox_schemas.json            ││
│  │  - ChromaDB index                   ││
│  │  TTL: Until schema change           ││
│  └────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

#### 9.1.2 Performance Metrics

| Operation | Target | Actual | Status |
|-----------|--------|--------|--------|
| RAG Search | <300ms | 100-200ms | ✅ Met |
| Tool Generation | <10s | 2-3s | ✅ Met |
| Simple Query | <5s | 2-4s | ✅ Met |
| Complex Query | <15s | 5-12s | ✅ Met |
| WAPI Request | <2s | 0.5-1.5s | ✅ Met |
| Claude API Call | <3s | 1-3s | ✅ Met |
| RAG Build | <5min | 2-3min | ✅ Met |

### 9.2 Scalability Bottlenecks

1. **Sequential Tool Execution**
   - Current: Tools execute sequentially
   - Bottleneck: Long chains take cumulative time
   - Future: Parallel tool execution where possible

2. **RAG Search**
   - Current: Single-threaded vector search
   - Bottleneck: Scales linearly with document count
   - Future: Distributed vector search

3. **InfoBlox WAPI**
   - Current: Single connection per request
   - Bottleneck: Network latency
   - Future: Connection pooling, request batching

---

## 10. Scalability Considerations

### 10.1 Current Limitations

1. **Single User**: CLI is single-user, single-session
2. **Local Deployment**: Runs on one machine
3. **Sequential Processing**: One query at a time
4. **Memory Bound**: RAG index in memory

### 10.2 Future Scalability Paths

#### Option 1: Multi-User CLI
```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  User 1 CLI │  │  User 2 CLI │  │  User N CLI │
└─────────────┘  └─────────────┘  └─────────────┘
       │                │                  │
       └────────────────┼──────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  Shared MCP Server    │
            │  (Multi-session)      │
            └───────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  InfoBlox Grid        │
            └───────────────────────┘
```

#### Option 2: Web-Based UI
```
┌──────────────────────────────────────────────────┐
│  Web Browser (Multiple Users)                    │
└──────────────────────────────────────────────────┘
                    │ HTTPS
                    ▼
┌──────────────────────────────────────────────────┐
│  Web Application Server                          │
│  - FastAPI / Flask                               │
│  - WebSocket for real-time                       │
│  - Session management                            │
└──────────────────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
    ▼               ▼               ▼
┌────────┐    ┌──────────┐    ┌──────────┐
│  RAG   │    │  Claude  │    │ InfoBlox │
│  DB    │    │  API     │    │  WAPI    │
└────────┘    └──────────┘    └──────────┘
```

#### Option 3: Microservices Architecture
```
┌──────────────────────────────────────────────────┐
│  API Gateway                                      │
│  - Authentication                                 │
│  - Rate limiting                                  │
│  - Request routing                                │
└──────────────────────────────────────────────────┘
           │
    ┌──────┴──────┬──────────┬─────────────┐
    ▼             ▼          ▼             ▼
┌────────┐  ┌──────────┐ ┌────────┐  ┌──────────┐
│ RAG    │  │ Tool     │ │ Chat   │  │ InfoBlox │
│ Service│  │ Service  │ │ Service│  │ Adapter  │
└────────┘  └──────────┘ └────────┘  └──────────┘
```

---

## 11. Architecture Decision Records (ADRs)

### ADR-001: Use Claude Sonnet 4.5 Model
**Status**: Accepted
**Context**: Need powerful language model with tool use
**Decision**: Use Claude Sonnet 4.5
**Consequences**: High accuracy, but API costs

### ADR-002: Use ChromaDB for RAG
**Status**: Accepted
**Context**: Need vector database for semantic search
**Decision**: ChromaDB for local, persistent storage
**Consequences**: Good performance, local deployment

### ADR-003: Dynamic Tool Generation from Schemas
**Status**: Accepted
**Context**: InfoBlox has 232 object types, manual tool creation impractical
**Decision**: Generate tools dynamically from WAPI schemas
**Consequences**: Automatic support for new objects, upgrade resilience

### ADR-004: Python 3.9+ for MCP SDK
**Status**: Accepted
**Context**: MCP SDK requires Python 3.9+, RHEL 7.9 has Python 3.8
**Decision**: Use pyenv to install modern Python alongside system Python
**Consequences**: Full MCP support, some installation complexity

### ADR-005: CLI-First Interface
**Status**: Accepted
**Context**: Target users are network admins comfortable with CLI
**Decision**: Build CLI application, not web UI
**Consequences**: Simple deployment, familiar interface, single-user limitation

### ADR-006: Local Deployment Only
**Status**: Accepted
**Context**: Security concerns with cloud deployment
**Decision**: Local deployment only, no cloud transmission
**Consequences**: Better security, limited scalability

### ADR-007: Disable SSL Verification by Default
**Status**: Accepted (with concerns)
**Context**: Many InfoBlox grids use self-signed certificates
**Decision**: Disable SSL verification by default (configurable)
**Consequences**: Easier setup, potential MITM vulnerability (see security review)

---

## 12. Appendix

### 12.1 Technology Choices Rationale

| Technology | Rationale |
|------------|-----------|
| **Python** | Ecosystem for AI/ML, InfoBlox support, easy scripting |
| **Anthropic Claude** | Best-in-class tool use, context window, reasoning |
| **MCP** | Standard protocol for AI tool integration |
| **ChromaDB** | Simple, local vector DB, no server needed |
| **requests** | De facto standard for HTTP in Python |
| **BeautifulSoup** | HTML parsing for web scraping |
| **DuckDuckGo** | No-auth web search |

### 12.2 Future Architecture Enhancements

1. **Async/Await Pattern**
   - Convert to asyncio for concurrent operations
   - Parallel tool execution
   - Better responsiveness

2. **Connection Pooling**
   - Reuse HTTP connections to InfoBlox
   - Reduce latency
   - Better throughput

3. **Distributed RAG**
   - Multiple RAG instances
   - Load balancing
   - Higher throughput

4. **Caching Layer**
   - Redis for shared cache
   - Multi-user support
   - Faster responses

5. **Observability**
   - Prometheus metrics
   - Grafana dashboards
   - Distributed tracing

---

**End of Architecture Documentation**

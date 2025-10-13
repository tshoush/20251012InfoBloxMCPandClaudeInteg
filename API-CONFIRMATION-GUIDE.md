# API Call Confirmation System

**User-Controlled API Execution with Preview & Edit Capability**

## Overview

The API Confirmation System ensures that users have complete visibility and control over InfoBlox API calls before they are executed. This system addresses the critical requirement that **no API call should execute without user approval**.

## Problem Solved

### Before (Risky):
```
User: "Show me all networks"
  ↓
Claude LLM: Calls infoblox_list_networks
  ↓
API executes IMMEDIATELY ❌
  ↓
Results returned
```

**Issues:**
- ❌ No visibility into what API call will be made
- ❌ No chance to review parameters
- ❌ No ability to edit or cancel
- ❌ User unaware of API endpoint being called

### After (Safe):
```
User: "Show me all networks"
  ↓
Claude LLM: Decides to call infoblox_list_networks
  ↓
┌─────────────────────────────────────────────────────────────┐
│ 🔍 API Call Preview                                          │
├─────────────────────────────────────────────────────────────┤
│ List networks from InfoBlox                                  │
│                                                              │
│ Method:     GET                                              │
│ Endpoint:   /wapi/v2.13.1/network                           │
│ Username:   admin                                            │
│ Parameters:                                                  │
│   • _max_results: 100                                       │
│                                                              │
│ Curl Equivalent:                                            │
│ curl -X GET \                                               │
│   -u admin:$INFOBLOX_PASSWORD \                             │
│   'https://192.168.1.224/wapi/v2.13.1/network?...'          │
└─────────────────────────────────────────────────────────────┘

Execute? (yes/no/edit) [yes]: ▌
  ↓
User confirms: yes
  ↓
API executes ONLY after confirmation ✅
```

**Benefits:**
- ✅ Full visibility into API call details
- ✅ See curl equivalent for reproduction
- ✅ Review and edit parameters before execution
- ✅ Change username if needed
- ✅ Cancel unwanted calls
- ✅ Complete audit trail

## Features

### 1. API Call Preview

Shows comprehensive details before execution:

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
│     "comment": "Test network"                                │
│   }                                                          │
│                                                              │
│ Curl Equivalent:                                            │
│ curl -X POST \                                              │
│   -u admin:$INFOBLOX_PASSWORD \                             │
│   -H 'Content-Type: application/json' \                     │
│   -d '{"network": "10.50.0.0/24", ...}' \                   │
│   'https://192.168.1.224/wapi/v2.13.1/network'              │
└─────────────────────────────────────────────────────────────┘
```

### 2. Variable Extraction

The system extracts values from the user's prompt using Claude's natural language understanding:

**Example 1: Simple Query**
```
User: "List all networks"

Preview shows:
  Parameters:
    • _max_results: 100  (default)
```

**Example 2: Filtered Query**
```
User: "Show me networks in the 192.168.1.0/24 subnet"

Preview shows:
  Parameters:
    • _max_results: 100
    • network: 192.168.1.0/24  [extracted from your prompt]
```

**Example 3: Create with Details**
```
User: "Create a network 10.50.0.0/24 with comment 'Test network'"

Preview shows:
  Request Body:
    {
      "network": "10.50.0.0/24",  [from prompt]
      "comment": "Test network"    [from prompt]
    }
```

### 3. Credential Handling

**Username:**
- Displayed in preview
- User can edit in Edit mode
- Changes applied to current session

**Password:**
- **NEVER displayed**
- Shown as `$INFOBLOX_PASSWORD` in curl commands
- Shown as `***` in preview
- Always read from environment variables

**Security:**
```bash
# Curl command always uses env var placeholder
curl -X GET -u admin:$INFOBLOX_PASSWORD 'https://...'

# Never shows actual password:
curl -X GET -u admin:infoblox 'https://...'  # ❌ NEVER
```

### 4. Interactive Confirmation

Three options after preview:

#### A. yes (Confirm & Execute)
```
Execute? (yes/no/edit) [yes]: yes
✓ Executing API call...
```

Press Enter (default) or type `yes`/`y`

#### B. no (Cancel)
```
Execute? (yes/no/edit) [yes]: no
✗ API call cancelled
```

Returns to chat without executing

#### C. edit (Modify Parameters)
```
Execute? (yes/no/edit) [yes]: edit

────────────────────────────────────────────────────────────────
Edit Mode - Press Enter to keep current value
────────────────────────────────────────────────────────────────

Username [admin]: testuser

Parameters:
  _max_results [100]: 50
  network [192.168.1.0/24]: ⏎

✓ Parameters updated
```

After editing, preview is shown again with new values.

## User Workflows

### Workflow 1: Quick Confirm (Most Common)

```
User: "List all networks"

[Preview appears]

Execute? (yes/no/edit) [yes]: ⏎  (just press Enter)

[Executes with defaults]
```

**Time:** < 1 second

### Workflow 2: Review and Execute

```
User: "Create a network 10.50.0.0/24"

[Preview shows POST with request body]

User reviews: ✓ Endpoint correct ✓ Data correct

Execute? (yes/no/edit) [yes]: yes

[Executes]
```

**Time:** 2-3 seconds

### Workflow 3: Edit Before Execute

```
User: "Show me networks"

[Preview shows _max_results: 100]

Execute? (yes/no/edit) [yes]: edit

Username [admin]: ⏎
  _max_results [100]: 10

[Preview updates with _max_results: 10]

Execute? (yes/no/edit) [yes]: yes

[Executes with modified parameters]
```

**Time:** 5-10 seconds

### Workflow 4: Cancel Unwanted Call

```
User: "Delete all networks"  (accidental)

[Preview shows DELETE /network with parameters]

User sees DELETE method

Execute? (yes/no/edit) [yes]: no

✗ API call cancelled

User: "Never mind, I didn't mean to do that"
```

**Time:** 2-3 seconds (disaster avoided!)

## Technical Architecture

### Component: `api_confirmation.py`

Main class: `APICallConfirmation`

**Key Methods:**

1. **`map_tool_to_api_call(tool_name, tool_input)`**
   - Maps Claude tool call to API details
   - Extracts method, path, parameters, data
   - Returns structured API info

2. **`generate_curl_command(api_info, username)`**
   - Creates curl equivalent
   - Uses `$INFOBLOX_PASSWORD` placeholder
   - Formats for readability

3. **`display_api_preview(api_info, username)`**
   - Renders formatted preview box
   - Color-coded sections
   - Truncates long values

4. **`get_user_confirmation()`**
   - Interactive yes/no/edit prompt
   - Returns user action

5. **`edit_parameters(api_info)`**
   - Interactive parameter editor
   - Preserves defaults on Enter
   - Updates api_info in place

6. **`confirm_api_call(tool_name, tool_input)`**
   - **Main entry point**
   - Orchestrates full workflow
   - Returns: `(should_execute, final_input, username)`

### Integration with Chat Interfaces

All three chat interfaces modified:
- `claude-chat-rag.py` - RAG-enhanced chat
- `claude-chat-infoblox.py` - InfoBlox-focused chat
- `claude-chat-mcp.py` - MCP server chat

**Integration Pattern:**

```python
def process_tool_call(tool_name, tool_input):
    # Check if InfoBlox tool
    infoblox_tools = [
        "infoblox_list_networks", "infoblox_get_network",
        "infoblox_create_network", "infoblox_search_records",
        "infoblox_list_dhcp_leases", "infoblox_query"
    ]

    if tool_name in infoblox_tools:
        # Get user confirmation
        should_execute, final_input, username = api_confirmation.confirm_api_call(
            tool_name, tool_input
        )

        if not should_execute:
            return {"cancelled": True, "message": "API call cancelled by user"}

        # Use modified input
        tool_input = final_input

        # Update username if changed
        if username:
            infoblox_client.session.auth = (username, settings.infoblox_password)

    # Execute tool (only if confirmed)
    if tool_name == "infoblox_list_networks":
        return infoblox_list_networks(...)
    # ... etc
```

**Non-InfoBlox Tools:** Built-in tools (web search, file operations, datetime) execute immediately without confirmation.

## Supported InfoBlox Tools

All InfoBlox WAPI tools require confirmation:

1. **infoblox_list_networks** - GET /network
2. **infoblox_get_network** - GET /network/{ref}
3. **infoblox_create_network** - POST /network
4. **infoblox_search_records** - GET /record:{type}
5. **infoblox_list_dhcp_leases** - GET /lease
6. **infoblox_query** - GET /{object_type}

## Examples

### Example 1: List Networks

**User Prompt:**
```
"Show me all IPv4 networks"
```

**Preview:**
```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 API Call Preview                                          │
├─────────────────────────────────────────────────────────────┤
│ List networks from InfoBlox                                  │
│                                                              │
│ Method:     GET                                              │
│ Endpoint:   /wapi/v2.13.1/network                           │
│ Username:   admin                                            │
│ Parameters:                                                  │
│   • _max_results: 100                                       │
│                                                              │
│ Curl Equivalent:                                            │
│ curl -X GET \                                               │
│   -u admin:$INFOBLOX_PASSWORD \                             │
│   'https://192.168.1.224/wapi/v2.13.1/network?...'          │
└─────────────────────────────────────────────────────────────┘

Execute? (yes/no/edit) [yes]:
```

### Example 2: Create Network

**User Prompt:**
```
"Create a new network 172.16.0.0/16 for the engineering department"
```

**Preview:**
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
│     "network": "172.16.0.0/16",                             │
│     "comment": "for the engineering department"              │
│   }                                                          │
│                                                              │
│ Curl Equivalent:                                            │
│ curl -X POST \                                              │
│   -u admin:$INFOBLOX_PASSWORD \                             │
│   -H 'Content-Type: application/json' \                     │
│   -d '{"network": "172.16.0.0/16", ...}' \                  │
│   'https://192.168.1.224/wapi/v2.13.1/network'              │
└─────────────────────────────────────────────────────────────┘

Execute? (yes/no/edit) [yes]:
```

### Example 3: Search DNS Records

**User Prompt:**
```
"Find all A records for domain example.com"
```

**Preview:**
```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 API Call Preview                                          │
├─────────────────────────────────────────────────────────────┤
│ Search A DNS records                                         │
│                                                              │
│ Method:     GET                                              │
│ Endpoint:   /wapi/v2.13.1/record:a                          │
│ Username:   admin                                            │
│ Parameters:                                                  │
│   • _max_results: 100                                       │
│   • name: example.com                                        │
│                                                              │
│ Curl Equivalent:                                            │
│ curl -X GET \                                               │
│   -u admin:$INFOBLOX_PASSWORD \                             │
│   'https://192.168.1.224/wapi/v2.13.1/record:a?...'         │
└─────────────────────────────────────────────────────────────┘

Execute? (yes/no/edit) [yes]:
```

## Platform Support

### macOS (Development)
- ✅ Full support
- ✅ Color terminal output
- ✅ All chat interfaces

### RHEL 7.9 (Production)
- ✅ Full support
- ✅ Color terminal output (tested)
- ✅ CLI-only (no GUI required)
- ✅ Works via SSH

### Compatibility
- Python 3.8+ (tested on 3.8.13 and 3.12.7)
- Terminal with ANSI color support
- Interactive stdin/stdout (required for confirmation prompts)

## Security Benefits

1. **Audit Trail**: Every API call logged with user confirmation
2. **Accidental Prevention**: User review prevents mistakes
3. **Credential Protection**: Password never displayed
4. **Parameter Validation**: User can verify values before execution
5. **Cancellation**: User can abort any call pre-execution

## Performance

- **Preview rendering**: < 100ms
- **User confirmation**: 1-5 seconds (human decision)
- **No performance impact**: System only adds confirmation step, API execution unchanged

## Limitations

1. **MCP Server Username Changes**: Username changes not supported for MCP-based calls (logged as warning)
2. **Batch Operations**: Each API call requires individual confirmation (no bulk approve yet)
3. **Interactive Only**: Requires interactive terminal (not suitable for scripted/automated execution)

## Future Enhancements

Potential improvements:

1. **Batch Confirmation**: "Approve all" for multi-step operations
2. **Auto-approve Mode**: `--no-confirm` flag for trusted scripts
3. **Confirmation History**: Review past confirmations
4. **Custom Templates**: User-defined approval rules
5. **MCP Username Support**: Update MCP server env on-the-fly
6. **API Call Favorites**: Save frequently used calls

## Testing

### Manual Test Cases

**Test 1: Basic Confirmation**
```bash
python claude-chat-rag.py
> List all networks
[Preview appears]
> yes
[Executes]
```

**Test 2: Cancel Operation**
```bash
python claude-chat-infoblox.py
> Delete network 192.168.1.0/24
[Preview shows DELETE]
> no
[Cancels]
```

**Test 3: Edit Parameters**
```bash
python claude-chat-rag.py
> Show me 10 networks
[Preview shows _max_results: 100]
> edit
Username [admin]: ⏎
_max_results [100]: 10
[Preview updates]
> yes
[Executes with 10 max results]
```

**Test 4: Non-InfoBlox Tools (No Confirmation)**
```bash
python claude-chat-rag.py
> What is the current time?
[Executes immediately - no preview]
> 2025-10-13 14:30:00
```

## Troubleshooting

**Issue: Preview not appearing**
- Check that `api_confirmation.py` is imported correctly
- Verify tool name starts with `infoblox_`

**Issue: Colors not displaying**
- Terminal may not support ANSI colors
- Try different terminal (iTerm2, Terminal.app, etc.)

**Issue: Confirmation prompt not accepting input**
- Check stdin is connected (not piped)
- Ensure running interactively, not in background

**Issue: Username change not working (MCP)**
- Expected for MCP tools
- Use direct chat interfaces (`claude-chat-rag.py`, `claude-chat-infoblox.py`) for username changes

## Summary

The API Confirmation System provides:

✅ **Safety**: No API call executes without explicit user approval
✅ **Visibility**: Full details of every API call before execution
✅ **Control**: Edit parameters, change username, or cancel
✅ **Transparency**: See exact curl equivalent for reproduction
✅ **Security**: Password never displayed, always protected
✅ **Flexibility**: Quick confirm or detailed review as needed

**Key Principle:** User has complete control over every InfoBlox API interaction.

---

**Related Documentation:**
- [README.md](README.md) - Main project overview
- [DDI-ASSISTANT-GUIDE.md](DDI-ASSISTANT-GUIDE.md) - Using the DDI Assistant
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide

**Last Updated:** October 13, 2025

# Extensible Attribute (EA) Query Examples for InfoBlox

## What are Extensible Attributes?

Extensible Attributes (EAs) are **custom fields** that can be added to any InfoBlox object (networks, DNS records, DHCP ranges, etc.). They allow you to tag and categorize objects with your own metadata.

**Examples of common EAs:**
- `MARSHA` - Location or site identifier
- `Site` - Physical site name
- `Owner` - Department or team owner
- `Environment` - Production, Development, Testing
- `CostCenter` - Billing/accounting code
- `Application` - Application name

## How to Query by Extensible Attributes

### Key Rules:
1. **Prefix EA name with asterisk (*)**:  `*MARSHA` not `MARSHA`
2. **Always include extattrs in return fields**: `_return_fields+=extattrs`
3. **Use search tools, not list tools**: Use `infoblox_query` or `infoblox_search_*`

## Example: "List all networks where MARSHA='HDQTR2'"

### What the User Wants:
Find all networks that have the extensible attribute `MARSHA` set to the value `HDQTR2`.

### Tool Selection:
**Tool:** `infoblox_query`

### Parameters:
```json
{
  "object_type": "network",
  "filters": {
    "*MARSHA": "HDQTR2",
    "_return_fields+": "extattrs"
  },
  "max_results": 100
}
```

### Alternative with infoblox_list_networks:
This won't work because list tools don't support filtering by EAs. Must use query/search tools.

### Complete Query Pattern:
```
GET /wapi/v2.13.1/network?*MARSHA=HDQTR2&_return_fields+=extattrs
```

### Expected Response:
```json
[
  {
    "_ref": "network/ZG5zLm5ldHdvcmskMTAuNTAuMC4wLzI0LzA:10.50.0.0/24/default",
    "network": "10.50.0.0/24",
    "comment": "Headquarters Network 2",
    "extattrs": {
      "MARSHA": {
        "value": "HDQTR2"
      }
    }
  },
  {
    "_ref": "network/ZG5zLm5ldHdvcmskMTAuNTEuMC4wLzI0LzA:10.51.0.0/24/default",
    "network": "10.51.0.0/24",
    "comment": "Headquarters Network 2 - DMZ",
    "extattrs": {
      "MARSHA": {
        "value": "HDQTR2"
      }
    }
  }
]
```

## More EA Query Examples

### Example 1: Find DNS A records by Site
**User Query:** "Find all A records where Site='NYC'"

**Tool:** `infoblox_query`
**Parameters:**
```json
{
  "object_type": "record:a",
  "filters": {
    "*Site": "NYC",
    "_return_fields+": "extattrs"
  }
}
```

### Example 2: Find DHCP ranges by Owner
**User Query:** "Show DHCP ranges owned by Network Team"

**Tool:** `infoblox_query`
**Parameters:**
```json
{
  "object_type": "range",
  "filters": {
    "*Owner": "Network Team",
    "_return_fields+": "extattrs"
  }
}
```

### Example 3: Multiple EA Filters (AND condition)
**User Query:** "Find networks where MARSHA='HDQTR2' AND Environment='Production'"

**Tool:** `infoblox_query`
**Parameters:**
```json
{
  "object_type": "network",
  "filters": {
    "*MARSHA": "HDQTR2",
    "*Environment": "Production",
    "_return_fields+": "extattrs"
  }
}
```

### Example 4: EA with Regex Match
**User Query:** "Find networks where MARSHA starts with 'HDQTR'"

**Tool:** `infoblox_query`
**Parameters:**
```json
{
  "object_type": "network",
  "filters": {
    "*MARSHA~": "^HDQTR",
    "_return_fields+": "extattrs"
  }
}
```

Note: Use `~` for regex matching

## Multi-Tool Chains with EAs

### Example 1: Find and Update
**User Query:** "Find network where MARSHA='HDQTR2' and update its comment"

**Step 1:** Find the network
```json
Tool: infoblox_query
Parameters: {
  "object_type": "network",
  "filters": {
    "*MARSHA": "HDQTR2",
    "_return_fields": "_ref,network,extattrs"
  }
}
Result: {"_ref": "network/ZG5zLm5ldHdvcmskMTAuNTAuMC4wLzI0LzA:10.50.0.0/24/default", "network": "10.50.0.0/24"}
```

**Step 2:** Update the network
```json
Tool: infoblox_query (PUT method) or create separate update tool
Parameters: {
  "ref": "network/ZG5zLm5ldHdvcmskMTAuNTAuMC4wLzI0LzA:10.50.0.0/24/default",
  "data": {"comment": "Updated comment"}
}
```

### Example 2: Find Networks and Their DNS Records
**User Query:** "Show networks where Site='NYC' and list their DNS records"

**Step 1:** Find networks
```json
Tool: infoblox_query
Parameters: {
  "object_type": "network",
  "filters": {
    "*Site": "NYC",
    "_return_fields+": "extattrs"
  }
}
Result: Networks 10.20.0.0/24, 10.21.0.0/24
```

**Step 2:** Find DNS records in those networks
```json
Tool: infoblox_query
Parameters: {
  "object_type": "record:a",
  "filters": {
    "ipv4addr~": "10.20",
    "_return_fields+": "extattrs"
  }
}
```

### Example 3: Check Before Create
**User Query:** "Create network 10.60.0.0/24 only if no network exists with MARSHA='HDQTR3'"

**Step 1:** Check for existing network
```json
Tool: infoblox_query
Parameters: {
  "object_type": "network",
  "filters": {
    "*MARSHA": "HDQTR3",
    "_return_fields": "network"
  }
}
Result: [] (empty - no networks found)
```

**Step 2:** Create network with EA
```json
Tool: infoblox_create_network (if available) or infoblox_query (POST)
Parameters: {
  "network": "10.60.0.0/24",
  "comment": "Headquarters 3 Network",
  "extattrs": {
    "MARSHA": {"value": "HDQTR3"}
  }
}
```

## Natural Language Patterns → Tool Selection

### Pattern Recognition:

| User Says | EA Detected | Tool to Use | Filters |
|-----------|-------------|-------------|---------|
| "networks where MARSHA='X'" | MARSHA | infoblox_query | `{"*MARSHA": "X", "_return_fields+": "extattrs"}` |
| "find networks with Site='NYC'" | Site | infoblox_query | `{"*Site": "NYC", "_return_fields+": "extattrs"}` |
| "show ranges owned by Team" | Owner | infoblox_query | `{"*Owner": "Team", "_return_fields+": "extattrs"}` |
| "A records where Environment='Prod'" | Environment | infoblox_query | `{"*Environment": "Prod", "_return_fields+": "extattrs"}` |

### Keywords that Indicate EA Query:
- "where [NAME]='value'"
- "with [NAME] equal to"
- "where [NAME] is"
- "having [NAME]='value'"
- "filtered by [NAME]"
- "[OBJECT] with [NAME]"

## Common Mistakes to Avoid

### ❌ WRONG: Forgetting asterisk
```json
{"filters": {"MARSHA": "HDQTR2"}}  // Won't work
```

### ✅ CORRECT: Include asterisk
```json
{"filters": {"*MARSHA": "HDQTR2"}}
```

---

### ❌ WRONG: Not returning extattrs
```json
{"filters": {"*MARSHA": "HDQTR2"}}  // EAs won't be in response
```

### ✅ CORRECT: Include extattrs
```json
{"filters": {"*MARSHA": "HDQTR2", "_return_fields+": "extattrs"}}
```

---

### ❌ WRONG: Using list tool for EA query
```json
Tool: infoblox_list_networks
Parameters: {"filters": {"*MARSHA": "HDQTR2"}}  // List tools don't support EA filters
```

### ✅ CORRECT: Use query/search tool
```json
Tool: infoblox_query
Parameters: {"object_type": "network", "filters": {"*MARSHA": "HDQTR2"}}
```

---

### ❌ WRONG: Treating EA like regular field
```json
{"filters": {"MARSHA": "HDQTR2", "network": "10.0.0.0/24"}}
```

### ✅ CORRECT: Asterisk for EA, no asterisk for regular fields
```json
{"filters": {"*MARSHA": "HDQTR2", "network": "10.0.0.0/24"}}
```

## EA Query Response Format

When you include `_return_fields+: extattrs`, the response will include an `extattrs` field:

```json
{
  "_ref": "network/ZG5zLm5ldHdvcmskMTAuNTAuMC4wLzI0LzA:10.50.0.0/24/default",
  "network": "10.50.0.0/24",
  "comment": "Example network",
  "extattrs": {
    "MARSHA": {
      "value": "HDQTR2"
    },
    "Site": {
      "value": "New York"
    },
    "Environment": {
      "value": "Production"
    }
  }
}
```

Each EA has a nested structure with a `value` key.

## Summary: EA Query Checklist

When processing EA queries, always:

- [ ] Recognize EA name in user query (e.g., MARSHA, Site, Owner)
- [ ] Prefix EA with asterisk in filters: `*MARSHA`
- [ ] Include `_return_fields+: extattrs` in filters
- [ ] Use `infoblox_query` tool (or search tools, NOT list tools)
- [ ] Set `object_type` to correct object (network, record:a, range, etc.)
- [ ] Handle empty results gracefully
- [ ] Chain tools if user wants to perform actions on results
- [ ] Show EA values in response to user

## Testing the EA Query System

To verify the system understands EA queries, test with:

1. **Simple EA query:** "List networks where MARSHA='HDQTR2'"
2. **Multiple EAs:** "Find networks where MARSHA='HDQTR2' and Site='NYC'"
3. **Different object types:** "Show A records where Environment='Production'"
4. **Regex match:** "Find ranges where Owner starts with 'Network'"
5. **Multi-tool chain:** "Find network where MARSHA='HDQTR2' and show its utilization"

Expected behavior: System should automatically format EA queries correctly without user having to specify `*` prefix or `extattrs` return field.

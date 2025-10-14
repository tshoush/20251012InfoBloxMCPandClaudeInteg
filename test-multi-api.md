# Multi-API Call Testing

## Test Scenarios to Verify Multi-API Orchestration

### Test 1: Single Workflow Tool (Multi-API Internal)
**Query:** "Find IP 192.168.1.50"

**Expected Behavior:**
- Claude selects: `infoblox_find_ip_detailed`
- Tool internally calls 6 APIs:
  1. GET /ipv4address (status)
  2. GET /fixedaddress (MAC/hostname)
  3. GET /lease (DHCP lease)
  4. GET /record:a (DNS A record with last_queried)
  5. GET /record:ptr (DNS PTR record)
  6. GET /network (parent network info)
- Returns single formatted result

**Status:** ✅ Built and ready to test

---

### Test 2: Sequential Tool Calls (Claude Orchestration)
**Query:** "Find network 192.168.1.0/24 and show me all DHCP leases in that network"

**Expected Behavior:**
- Claude calls TWO tools in sequence:
  1. `infoblox_find_network_detailed` → network info
  2. `infoblox_list_dhcp_leases` with filter `{"network": "192.168.1.0/24"}`
- Claude combines both results in natural language response

**Status:** 🧪 Needs testing

---

### Test 3: Complex Multi-Step Query
**Query:** "Find all networks in 192.168.0.0/16 container, then show me utilization for each"

**Expected Behavior:**
- Claude orchestrates:
  1. Query network container
  2. List all networks in that container
  3. For each network, get utilization stats
- Claude aggregates and presents summary

**Status:** 🧪 Needs testing

---

### Test 4: Cross-Domain Query (Network + DNS)
**Query:** "Find IP 192.168.1.50, then show me all DNS records for that hostname"

**Expected Behavior:**
- Claude orchestrates:
  1. `infoblox_find_ip_detailed` → gets hostname
  2. Extract hostname from result
  3. Search all record types for that hostname
- Claude presents combined view

**Status:** 🧪 Needs testing

---

### Test 5: Validation Query
**Query:** "Is there a DNS A record for IP 192.168.1.50? If yes, is there a matching PTR?"

**Expected Behavior:**
- Claude orchestrates:
  1. Query record:a for IP
  2. Query record:ptr for IP
  3. Compare and validate forward/reverse match
- Claude reports validation status

**Status:** 🧪 Needs testing

---

## How to Test:

```bash
# On RedHat .200 system:
cd ~/REDHAT

# Test with MCP interface (best for multi-tool orchestration)
python claude-chat-mcp.py

# Try each test query above
```

## What To Look For:

✅ **Success Indicators:**
- Multiple API confirmation prompts (one per tool call)
- Claude naturally combines results
- Coherent combined output

❌ **Failure Indicators:**
- Claude only calls one tool when multiple needed
- Results not combined logically
- Error handling issues

## Current Capability Assessment:

| Capability | Built? | Tested? | Notes |
|------------|--------|---------|-------|
| Single tool multi-API (internal) | ✅ Yes | 🧪 Pending | Workflow tools do this |
| Claude sequential tool calls | ✅ Yes | 🧪 Pending | Claude API supports this |
| Result combination by Claude | ✅ Yes | 🧪 Pending | Claude's natural capability |
| Complex orchestration | ✅ Yes | 🧪 Pending | Depends on Claude's reasoning |

---

**Next Step:** Run these tests on RedHat .200 to verify real-world behavior.

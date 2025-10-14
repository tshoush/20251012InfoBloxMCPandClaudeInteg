# InfoBlox DDI Assistant - Operations Use Cases

**Real-world operational use cases for network operations teams**

This document describes specific operational workflows that the DDI Assistant is designed to support. Each use case includes expected input, output format, and business context.

---

## Use Case 1: Find Network - Comprehensive Network Information

### Business Context
When operations teams need to understand a network's current state - for troubleshooting, capacity planning, or provisioning new hosts - they need a complete view of the network including IP utilization, metadata, and parent relationships.

### User Input
```
Find network 192.168.1.0/24
```
or
```
Show me details for network 10.50.0.0/16
```

### Expected Output

```
═══════════════════════════════════════════════════════════════
                    NETWORK INFORMATION
═══════════════════════════════════════════════════════════════

Network:                192.168.1.0/24
Network Container:      192.168.0.0/16 (Corporate HQ)
Comment:                Management Network - Building A

Extensible Attributes:
  • Location:           HQ-BldgA-Floor3
  • Department:         IT Operations
  • Environment:        Production
  • Criticality:        High
  • Cost Center:        CC-12345

IP Address Statistics:
  • Total Usable IPs:   254
  • IPs Used:           142 (55.9%)
  • IPs Free:           112 (44.1%)
  • Network Address:    192.168.1.0
  • Broadcast Address:  192.168.1.255

Gateway Configuration:
  • Default Gateway:    192.168.1.1

DHCP Configuration:
  • DHCP Enabled:       Yes
  • DHCP Range:         192.168.1.100 - 192.168.1.200
  • DHCP Free:          58 addresses

DNS Configuration:
  • DNS Zone:           mgmt.corp.local
  • Reverse Zone:       1.168.192.in-addr.arpa

Last Modified:         2025-10-12 14:32:15 UTC
Modified By:           admin

═══════════════════════════════════════════════════════════════
```

### Required InfoBlox API Calls

1. **GET /wapi/v2.13.1/network**
   - Filter: `network=192.168.1.0/24`
   - Return fields: `network,comment,extattrs,network_container,options,members,_ref`

2. **GET /wapi/v2.13.1/networkcontainer**
   - Filter: `_ref=<container_ref>` (from network response)
   - Return fields: `network,comment`

3. **GET /wapi/v2.13.1/lease**
   - Filter: `network=192.168.1.0/24`
   - Count active leases for "IPs Used"

4. **Calculate IP statistics**
   - Total usable IPs = (2^(32-prefix_length)) - 2
   - IPs used = Count of leases + count of fixed addresses
   - IPs free = Total usable - IPs used

### Implementation Notes

- Extensible attributes should be displayed in alphabetical order
- IP utilization percentage shown with color coding (if CLI supports):
  - Green: < 70% used
  - Yellow: 70-85% used
  - Red: > 85% used
- Gateway typically .1 or .254, check DHCP options field
- Network container provides hierarchical context

### Edge Cases

- Network not found: Display clear error message
- No network container: Display "None (Top-level network)"
- No extensible attributes: Display "None"
- DHCP not configured: Display "DHCP Enabled: No"
- Multiple gateways: Display all

---

## Use Case 2: Find IP - Comprehensive IP Address Information

### Business Context
When operations teams need to investigate an IP address - for conflict resolution, troubleshooting connectivity issues, or verifying allocations - they need to know if it's in use, how it's allocated (DHCP vs fixed), DNS records, and parent network context.

### User Input
```
Find IP 192.168.1.50
```
or
```
Show me details for 10.50.100.25
```

### Expected Output

```
═══════════════════════════════════════════════════════════════
                    IP ADDRESS INFORMATION
═══════════════════════════════════════════════════════════════

IP Address:             192.168.1.50
Status:                 ✓ IN USE

Allocation Type:        Fixed Address
MAC Address:            00:50:56:ab:cd:ef
Host Name:              server01.corp.local
Comment:                Production Web Server

Network Information:
  • Network:            192.168.1.0/24
  • Network Container:  192.168.0.0/16 (Corporate HQ)
  • Gateway:            192.168.1.1

DNS Records:
  • A Record:           server01.corp.local → 192.168.1.50
  • PTR Record:         50.1.168.192.in-addr.arpa → server01.corp.local
  • Last Queried:       2025-10-13 10:45:32 UTC

DHCP Information:
  • Type:               Fixed/Static (not from DHCP pool)
  • DHCP Enabled:       Yes (network has DHCP)

Extensible Attributes:
  • Asset Tag:          SRV-001
  • Department:         Web Services
  • Environment:        Production

Last Modified:         2025-10-10 08:22:11 UTC
Modified By:           admin

═══════════════════════════════════════════════════════════════
```

**If IP is not allocated:**
```
═══════════════════════════════════════════════════════════════
                    IP ADDRESS INFORMATION
═══════════════════════════════════════════════════════════════

IP Address:             192.168.1.150
Status:                 ⚬ AVAILABLE (Not Allocated)

Network Information:
  • Network:            192.168.1.0/24
  • Network Container:  192.168.0.0/16 (Corporate HQ)
  • Gateway:            192.168.1.1
  • DHCP Enabled:       Yes
  • In DHCP Range:      Yes (192.168.1.100 - 192.168.1.200)

DNS Records:           None

═══════════════════════════════════════════════════════════════
```

### Required InfoBlox API Calls

1. **GET /wapi/v2.13.1/ipv4address**
   - Filter: `ip_address=192.168.1.50`
   - Return fields: `ip_address,status,types,objects,network,usage`
   - Tells us if IP is used and what objects reference it

2. **GET /wapi/v2.13.1/fixedaddress**
   - Filter: `ipv4addr=192.168.1.50`
   - Return fields: `ipv4addr,mac,name,comment,extattrs,network`
   - Gets fixed address details if allocated

3. **GET /wapi/v2.13.1/lease**
   - Filter: `address=192.168.1.50`
   - Return fields: `address,binding_state,client_hostname,ends,hardware`
   - Gets DHCP lease info if from DHCP

4. **GET /wapi/v2.13.1/record:a**
   - Filter: `ipv4addr=192.168.1.50`
   - Return fields: `name,ipv4addr,zone,view,last_queried`
   - Gets A record and last query time

5. **GET /wapi/v2.13.1/record:ptr**
   - Filter: `ipv4addr=192.168.1.50`
   - Return fields: `ptrdname,ipv4addr`
   - Gets PTR record

6. **GET /wapi/v2.13.1/network**
   - Filter: Network containing the IP
   - Gets parent network and container info

### Implementation Notes

- Check multiple object types: fixedaddress, lease, host record
- "Last Queried" comes from DNS record statistics
- Status can be: IN USE, AVAILABLE, RESERVED
- Types can be: FIXED, DHCP, HOST, RESERVED
- Show MAC address for both DHCP leases and fixed addresses
- Network context provides troubleshooting info

### Edge Cases

- IP not in any configured network: Display error
- Multiple DNS records: Display all
- IP in DHCP range but not currently leased: Show "Available in DHCP range"
- Conflicting allocations: Highlight with warning

---

## Use Case 3: Find Zone - DNS Zone Information

### Business Context
When operations teams need to understand DNS zone configuration - for delegation planning, troubleshooting resolution issues, or zone transfers - they need to know the authoritative name servers, zone hierarchy, and subzone structure.

### User Input
```
Find zone corp.local
```
or
```
Show me details for zone example.com
```

### Expected Output

```
═══════════════════════════════════════════════════════════════
                    DNS ZONE INFORMATION
═══════════════════════════════════════════════════════════════

Zone Name:              corp.local
Zone Type:              Authoritative (Forward)
View:                   default

Name Server Group:
  • NS Group:           internal-ns
  • Primary NS:         ns1.corp.local (192.168.1.10)
  • Secondary NS:       ns2.corp.local (192.168.1.11)
  • Secondary NS:       ns3.corp.local (192.168.1.12)

Zone Hierarchy:
  • Parent Zone:        local (delegated)
  • This Zone:          corp.local
  • Sub Zones:          3 zones

Sub Zones:
  1. dev.corp.local
     • NS Group:        dev-ns
     • Delegation:      Complete

  2. test.corp.local
     • NS Group:        internal-ns
     • Delegation:      Complete

  3. prod.corp.local
     • NS Group:        prod-ns
     • Delegation:      Complete

Zone Configuration:
  • SOA Serial:         2025101301
  • SOA Refresh:        3600
  • SOA Retry:          600
  • SOA Expire:         604800
  • TTL:                86400

Record Statistics:
  • Total Records:      1,247
  • A Records:          542
  • CNAME Records:      305
  • MX Records:         8
  • TXT Records:        12

Extensible Attributes:
  • Business Unit:      Corporate IT
  • Criticality:        High
  • SLA Tier:           Tier 1

Last Modified:         2025-10-12 16:20:45 UTC
Modified By:           dnsadmin

═══════════════════════════════════════════════════════════════
```

### Required InfoBlox API Calls

1. **GET /wapi/v2.13.1/zone_auth**
   - Filter: `fqdn=corp.local`
   - Return fields: `fqdn,view,ns_group,soa_serial,soa_refresh,soa_retry,soa_expire,ttl,extattrs,_ref`
   - Gets primary zone information

2. **GET /wapi/v2.13.1/zone_auth**
   - Filter: `parent=corp.local` or search for zones with parent FQDN
   - Return fields: `fqdn,ns_group,zone_format`
   - Gets list of subzones

3. **GET /wapi/v2.13.1/nsgroup**
   - Filter: `name=<ns_group_name>`
   - Return fields: `name,primary,secondaries`
   - Gets NS group details and server IPs

4. **GET /wapi/v2.13.1/record:a** (count)
   - Filter: `zone=corp.local`
   - Count records by type for statistics

5. **GET /wapi/v2.13.1/record:cname** (count)
   - Filter: `zone=corp.local`

6. **GET /wapi/v2.13.1/record:mx** (count)
   - Filter: `zone=corp.local`

### Implementation Notes

- NS group provides critical operational info
- Sub zones should show delegation status
- Record counts help understand zone size
- SOA serial indicates last zone update
- Show both forward and reverse zone types
- View field indicates DNS view (default, internal, external)

### Edge Cases

- Zone not found: Display clear error
- No subzones: Display "No sub zones"
- No NS group: Display "NS group not configured (using grid defaults)"
- Multiple views: Display view-specific information
- Reverse zone: Show PTR record counts and network mapping

---

## Implementation Status

| Use Case | Status | Implementation File | Tool Name | Available In |
|----------|--------|---------------------|-----------|--------------|
| Find Network | ✅ Implemented | `network_info.py` | `infoblox_find_network_detailed` | MCP Server, claude-chat-rag.py, claude-chat-infoblox.py |
| Find IP | ✅ Implemented | `ip_info.py` | `infoblox_find_ip_detailed` | MCP Server, claude-chat-rag.py, claude-chat-infoblox.py |
| Find Zone | ✅ Implemented | `zone_info.py` | `infoblox_find_zone_detailed` | MCP Server, claude-chat-rag.py, claude-chat-infoblox.py |

**All 3 use cases are now available through the complete pipeline:**
- **MCP Server** (`infoblox-mcp-server.py`) - 143 tools total (140 auto-generated + 3 use case tools)
- **claude-chat-mcp.py** - Uses MCP Server (all 143 tools, works on all platforms)
- **claude-chat-rag.py** - Direct integration with RAG enhancement
- **claude-chat-infoblox.py** - Direct integration
- **CLI** - Direct execution: `python network_info.py`, `python ip_info.py`, `python zone_info.py`

---

## How to Add New Use Cases

1. Document the business context and user need
2. Define expected input/output format
3. List required InfoBlox API calls
4. Note any special calculations or logic
5. Identify edge cases
6. Implement as specialized tool if needed
7. Add example queries to documentation

---

**Last Updated:** October 13, 2025
**Contact:** Operations Team

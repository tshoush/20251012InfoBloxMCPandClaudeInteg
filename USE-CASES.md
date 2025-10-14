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

## Use Case 2: [Placeholder - More to Come]

### Business Context
*User mentioned "a couple of them to get started" - waiting for additional use cases*

---

## Implementation Status

| Use Case | Status | Implementation File | Tools Required |
|----------|--------|---------------------|----------------|
| Find Network | ✅ Documented | `network_info.py` | `infoblox_find_network_detailed` |
| TBD | 📝 Pending | - | - |

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

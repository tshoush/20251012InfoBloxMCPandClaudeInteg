# InfoBlox Standalone Query Tool

**Self-contained command-line tool for quick InfoBlox WAPI queries**

## Overview

`infoblox-query.py` is a standalone, self-contained script that provides direct access to InfoBlox WAPI for querying networks, IP addresses, and DNS zones. Unlike the AI-powered chat interfaces, this tool provides instant, deterministic results without Claude AI or MCP overhead.

## Key Features

✅ **Self-Contained** - Single script with no dependencies on other project files
✅ **Interactive Configuration** - First-run setup with smart defaults
✅ **Secure Storage** - Credentials saved to `~/.infoblox-query.conf` (600 permissions)
✅ **Quiet Mode** - `-q` flag for automation and scripting
✅ **Multi-API Orchestration** - Combines multiple WAPI calls automatically
✅ **Formatted Output** - Color-coded, structured display
✅ **InfoBlox 9.3 Compatible** - WAPI v2.13.1

## Quick Start

### First Run (Interactive Configuration)

```bash
./infoblox-query.py -n 192.168.1.0/24
```

The script will prompt for:
- InfoBlox Grid IP/Hostname
- Username (default: admin)
- Password (masked input)
- WAPI Version (default: v2.13.1)

Configuration is saved to `~/.infoblox-query.conf` for future use.

### Subsequent Runs

```bash
# Uses saved config, prompts with defaults
./infoblox-query.py -i 192.168.1.50

# Quiet mode - no prompts, uses saved config
./infoblox-query.py -z corp.local -q
```

## Usage Examples

### Network Queries

```bash
# Query single network
./infoblox-query.py -n 192.168.1.0/24

# Query with quiet mode
./infoblox-query.py -n 10.0.0.0/8 -q
```

**Returns:**
- Network details (CIDR, container, comment)
- Extensible attributes
- IP statistics (total IPs, utilization, netmask)
- Gateway configuration
- DHCP configuration (ranges, lease time, DNS servers)
- DNS zone associations
- Last modification timestamp

### IP Address Queries

```bash
# Query single IP
./infoblox-query.py -i 192.168.1.50

# Query with quiet mode
./infoblox-query.py -i 10.50.100.25 -q
```

**Returns:**
- IP status (IN USE, AVAILABLE, UNKNOWN)
- Allocation type (FIXED, DHCP, HOST_RECORD, AVAILABLE)
- Fixed address details (MAC, hostname, comment)
- DHCP lease information (binding state, lease times)
- Host record details
- DNS records (A and PTR with last queried time)
- Parent network and container information

### DNS Zone Queries

```bash
# Query DNS zone
./infoblox-query.py -z corp.local

# Query with quiet mode
./infoblox-query.py -z example.com -q
```

**Returns:**
- Zone name and type (forward/reverse)
- DNS view
- Name server group configuration
- SOA record details (serial, refresh, retry, expire, TTL)
- Subzones list
- Record statistics by type (A, AAAA, CNAME, MX, TXT, SRV, PTR)
- Extensible attributes

## Command-Line Options

```
Usage: infoblox-query.py [-h] (-n NETWORK | -i IP_ADDRESS | -z ZONE) [-q]

Options:
  -h, --help            Show help message and exit
  -n NETWORK, --network NETWORK
                        Query network (e.g., 192.168.1.0/24)
  -i IP_ADDRESS, --ip IP_ADDRESS
                        Query IP address (e.g., 192.168.1.50)
  -z ZONE, --zone ZONE  Query DNS zone (e.g., corp.local)
  -q, --quiet           Quiet mode - use saved config without prompting
```

**Note:** `-n`, `-i`, and `-z` are mutually exclusive (choose one per query).

## Configuration File

### Location
```
~/.infoblox-query.conf
```

### Format (JSON)
```json
{
  "host": "192.168.1.224",
  "username": "admin",
  "password": "your-password",
  "wapi_version": "v2.13.1"
}
```

### Permissions
```bash
-rw-------  1 user  group  123  Oct 14 10:30 .infoblox-query.conf
```

File is automatically created with 600 permissions (owner read/write only).

### Manual Configuration

You can manually edit the config file:

```bash
# Edit config
vim ~/.infoblox-query.conf

# Ensure proper permissions
chmod 600 ~/.infoblox-query.conf
```

## Multi-API Orchestration

The tool automatically combines multiple WAPI calls to provide comprehensive results:

### Network Query (3-4 API Calls)
1. `GET /wapi/v2.13.1/network` - Get network object
2. `GET /wapi/v2.13.1/networkcontainer` - Get parent container (if exists)
3. Calculate IP statistics from network object
4. Extract DHCP/DNS info from network options

### IP Address Query (6 API Calls)
1. `GET /wapi/v2.13.1/ipv4address` - Check IP status
2. `GET /wapi/v2.13.1/fixedaddress` - Check for fixed address
3. `GET /wapi/v2.13.1/lease` - Check for DHCP lease
4. `GET /wapi/v2.13.1/record:a` - Get DNS A record with last_queried
5. `GET /wapi/v2.13.1/record:ptr` - Get DNS PTR record
6. `GET /wapi/v2.13.1/network` - Get parent network info

### DNS Zone Query (4-6 API Calls)
1. `GET /wapi/v2.13.1/zone_auth` - Get zone object
2. `GET /wapi/v2.13.1/nsgroup` - Get name server group details
3. `GET /wapi/v2.13.1/zone_auth` - List all zones (to find subzones)
4. `GET /wapi/v2.13.1/record:a` - Count A records
5. `GET /wapi/v2.13.1/record:cname` - Count CNAME records
6. (Additional calls for MX, TXT, SRV, PTR record counts)

## Use Cases

### Network Operations

```bash
# Check network utilization before provisioning new hosts
./infoblox-query.py -n 192.168.1.0/24 -q

# Find available IP ranges
./infoblox-query.py -n 10.0.0.0/8 -q
```

### Troubleshooting

```bash
# Investigate connectivity issue
./infoblox-query.py -i 192.168.1.50

# Verify DNS records match
./infoblox-query.py -i 10.50.100.25

# Check zone delegation
./infoblox-query.py -z corp.local
```

### Automation & Scripting

```bash
#!/bin/bash
# Monitor network utilization

NETWORKS=("192.168.1.0/24" "192.168.2.0/24" "192.168.3.0/24")

for net in "${NETWORKS[@]}"; do
  echo "Checking $net..."
  ./infoblox-query.py -n "$net" -q | grep "Utilization:"
done
```

### CI/CD Integration

```yaml
# Example GitLab CI job
validate-ip-allocation:
  script:
    - ./infoblox-query.py -i $NEW_IP_ADDRESS -q
    - if grep -q "AVAILABLE" output.txt; then exit 0; else exit 1; fi
```

## Comparison: Standalone vs AI-Powered

| Feature | infoblox-query.py | claude-chat-mcp.py |
|---------|-------------------|-------------------|
| **Speed** | Instant | 2-5 seconds (AI processing) |
| **Dependencies** | None (self-contained) | Claude API, MCP, config.py |
| **Configuration** | `~/.infoblox-query.conf` | `.env` file |
| **Credentials** | Separate config | Shared with other tools |
| **Query Format** | CLI flags (-n, -i, -z) | Natural language |
| **Results** | Structured, deterministic | AI-formatted, conversational |
| **Automation** | Perfect (quiet mode) | Possible but slower |
| **Learning Curve** | Low (standard CLI) | Medium (natural language) |
| **Advanced Queries** | Limited to 3 types | 140+ tools available |
| **Scripting** | Excellent | Good |

## When to Use Each Tool

### Use `infoblox-query.py` when:
✅ You need instant results
✅ Scripting or automation
✅ CI/CD pipelines
✅ You know exactly what you want (network/IP/zone)
✅ No AI overhead desired
✅ Deterministic output required

### Use `claude-chat-mcp.py` when:
✅ Complex multi-step queries
✅ Natural language preferred
✅ Need to combine multiple operations
✅ Exploring InfoBlox data
✅ Using advanced WAPI features (140+ tools)
✅ Want AI assistance in interpretation

## Error Handling

### Network Not Found
```
═══════════════════════════════════════════════════════════════
                    NETWORK INFORMATION
═══════════════════════════════════════════════════════════════

Network not found: 192.168.99.0/24
```

### IP Not Allocated
```
═══════════════════════════════════════════════════════════════
                    IP ADDRESS INFORMATION
═══════════════════════════════════════════════════════════════

IP Address:             192.168.1.150
Status:                 ⚬ AVAILABLE (Not Allocated)

Network Information:
  • Network:            192.168.1.0/24
  • Network Container:  192.168.0.0/16 (Corporate HQ)
  ...
```

### Zone Not Found
```
═══════════════════════════════════════════════════════════════
                    DNS ZONE INFORMATION
═══════════════════════════════════════════════════════════════

Zone not found: invalid.zone
```

### API Connection Error
```
Error: API Error: HTTPSConnectionPool(host='192.168.1.224', port=443):
Max retries exceeded with url: /wapi/v2.13.1/network?network=192.168.1.0/24
```

## Security Considerations

✅ **Password Masking** - Password input is masked (uses `getpass`)
✅ **Secure Storage** - Config file has 600 permissions (owner only)
✅ **No Hardcoded Credentials** - All credentials from user input
✅ **SSL Disabled** - Uses `-k` for self-signed certs (InfoBlox default)
⚠️ **Plaintext Storage** - Password stored in plaintext in config file
⚠️ **Local Use Only** - Not designed for multi-user systems

**Recommendation:** Use on personal workstations only. For production automation, consider using API keys or service accounts.

## Troubleshooting

### Config File Issues

```bash
# Check if config exists
ls -la ~/.infoblox-query.conf

# View config (careful - contains password)
cat ~/.infoblox-query.conf

# Reset config (delete and re-run)
rm ~/.infoblox-query.conf
./infoblox-query.py -n 192.168.1.0/24
```

### Quiet Mode Fails

```bash
# Error: "Quiet mode requires saved configuration"
# Solution: Run once without -q to create config
./infoblox-query.py -n 192.168.1.0/24
# Then use quiet mode
./infoblox-query.py -n 192.168.1.0/24 -q
```

### API Errors

```bash
# Check connectivity
curl -k -u admin:password https://192.168.1.224/wapi/v2.13.1/?_schema

# Verify credentials
# Re-run without quiet mode to re-enter credentials
./infoblox-query.py -n 192.168.1.0/24
```

## Installation

### Prerequisites

- Python 3.8+
- `requests` library

### Install

```bash
# Clone repository
git clone https://github.com/tshoush/20251012InfoBloxMCPandClaudeInteg.git
cd 20251012InfoBloxMCPandClaudeInteg

# Install dependencies (only needs requests)
pip install requests

# Make executable
chmod +x infoblox-query.py

# Run
./infoblox-query.py -h
```

### Standalone Installation

You can copy just this script to any system:

```bash
# Copy to system PATH
sudo cp infoblox-query.py /usr/local/bin/

# Make executable
sudo chmod +x /usr/local/bin/infoblox-query.py

# Run from anywhere
infoblox-query.py -n 192.168.1.0/24
```

## Advanced Usage

### Automation Script Example

```bash
#!/bin/bash
# network-utilization-report.sh

NETWORKS=(
  "192.168.1.0/24"
  "192.168.2.0/24"
  "192.168.3.0/24"
  "10.0.0.0/8"
)

echo "Network Utilization Report - $(date)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for net in "${NETWORKS[@]}"; do
  echo ""
  echo "Network: $net"
  ./infoblox-query.py -n "$net" -q 2>/dev/null | grep -E "(Utilization|Total Usable|IPs Used|IPs Free)"
done
```

### Cron Job Example

```cron
# Check specific network every hour
0 * * * * /usr/local/bin/infoblox-query.py -n 192.168.1.0/24 -q >> /var/log/network-check.log 2>&1

# Daily zone audit
0 2 * * * /usr/local/bin/infoblox-query.py -z corp.local -q > /var/log/zone-audit-$(date +\%Y\%m\%d).log
```

### Python Integration

```python
import subprocess
import json

def query_infoblox_network(network):
    """Query InfoBlox network using standalone tool"""
    result = subprocess.run(
        ['./infoblox-query.py', '-n', network, '-q'],
        capture_output=True,
        text=True
    )
    return result.stdout

# Use it
output = query_infoblox_network('192.168.1.0/24')
print(output)
```

## Version History

- **v1.0** (October 14, 2025) - Initial release
  - Network, IP, and zone queries
  - Interactive configuration
  - Quiet mode
  - Multi-API orchestration
  - WAPI v2.13.1 support

## Related Documentation

- [README.md](README.md) - Main project documentation
- [USE-CASES.md](USE-CASES.md) - Operations use cases
- [ARCHITECTURE-FLOW.md](ARCHITECTURE-FLOW.md) - System architecture
- [DDI-ASSISTANT-GUIDE.md](DDI-ASSISTANT-GUIDE.md) - AI-powered chat interfaces

## Support

For issues or questions:
- GitHub Issues: [Issue Tracker](https://github.com/tshoush/20251012InfoBloxMCPandClaudeInteg/issues)
- Documentation: See project README.md

---

**Last Updated:** October 14, 2025
**Version:** 1.0
**WAPI Version:** v2.13.1
**InfoBlox Version:** 9.3+

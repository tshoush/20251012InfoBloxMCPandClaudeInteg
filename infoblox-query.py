#!/usr/bin/env python3
"""
InfoBlox Query Tool - Self-contained WAPI query script
Retrieves comprehensive information about networks, IP addresses, or DNS zones

Usage:
  ./infoblox-query.py -n 192.168.1.0/24          # Query network
  ./infoblox-query.py -i 192.168.1.50            # Query IP address
  ./infoblox-query.py -z corp.local              # Query DNS zone
  ./infoblox-query.py -n 192.168.1.0/24 -q       # Quiet mode (use saved config)
"""

import argparse
import json
import sys
import os
import getpass
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import ipaddress
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration file location
CONFIG_FILE = Path.home() / '.infoblox-query.conf'

# WAPI version
WAPI_VERSION = "v2.13.1"


class Colors:
    """ANSI color codes for terminal output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    CYAN = '\033[36m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[91m'
    WHITE = '\033[97m'


def print_header(text: str, char: str = '═'):
    """Print formatted section header"""
    width = 70
    print(f"\n{Colors.CYAN}{char * width}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.WHITE}{text.center(width)}{Colors.RESET}")
    print(f"{Colors.CYAN}{char * width}{Colors.RESET}\n")


def load_config() -> Dict[str, str]:
    """Load configuration from file"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"{Colors.YELLOW}Warning: Could not load config file: {e}{Colors.RESET}")
    return {}


def save_config(config: Dict[str, str]) -> bool:
    """Save configuration to file with secure permissions"""
    try:
        # Write config
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

        # Set secure permissions (owner read/write only)
        os.chmod(CONFIG_FILE, 0o600)

        print(f"{Colors.GREEN}✓ Configuration saved to {CONFIG_FILE}{Colors.RESET}")
        return True
    except Exception as e:
        print(f"{Colors.RED}✗ Could not save config: {e}{Colors.RESET}")
        return False


def prompt_for_config(quiet: bool = False) -> Dict[str, str]:
    """Prompt user for configuration values"""
    existing_config = load_config()

    if quiet:
        if not existing_config or not all(k in existing_config for k in ['host', 'username', 'password']):
            print(f"{Colors.RED}Error: Quiet mode requires saved configuration{Colors.RESET}")
            print(f"Run without -q flag first to configure credentials")
            sys.exit(1)
        return existing_config

    print(f"\n{Colors.BOLD}InfoBlox Configuration{Colors.RESET}")
    print(f"{Colors.CYAN}{'─' * 70}{Colors.RESET}\n")

    if existing_config:
        print(f"{Colors.GREEN}Found existing configuration. Press Enter to use defaults.{Colors.RESET}\n")

    config = {}

    # Grid host/IP
    default_host = existing_config.get('host', '')
    prompt = f"InfoBlox Grid IP/Hostname"
    if default_host:
        value = input(f"{prompt} [{default_host}]: ").strip()
        config['host'] = value if value else default_host
    else:
        config['host'] = input(f"{prompt}: ").strip()

    # Username
    default_user = existing_config.get('username', 'admin')
    prompt = f"Username"
    if default_user:
        value = input(f"{prompt} [{default_user}]: ").strip()
        config['username'] = value if value else default_user
    else:
        config['username'] = input(f"{prompt}: ").strip()

    # Password
    print(f"Password: ", end='', flush=True)
    config['password'] = getpass.getpass('')

    # WAPI version (optional, default to 2.13.1)
    default_wapi = existing_config.get('wapi_version', WAPI_VERSION)
    prompt = f"WAPI Version"
    value = input(f"{prompt} [{default_wapi}]: ").strip()
    config['wapi_version'] = value if value else default_wapi

    # Save configuration
    print()
    save_choice = input(f"Save configuration? [Y/n]: ").strip().lower()
    if save_choice != 'n':
        save_config(config)

    return config


class InfoBloxClient:
    """Self-contained InfoBlox WAPI client"""

    def __init__(self, host: str, username: str, password: str, wapi_version: str = WAPI_VERSION):
        self.host = host
        self.username = username
        self.password = password
        self.wapi_version = wapi_version
        self.base_url = f"https://{host}/wapi/{wapi_version}"

        # Create session
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.verify = False  # Disable SSL verification for self-signed certs
        self.session.headers.update({'Content-Type': 'application/json'})

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """Make GET request to WAPI"""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"{Colors.RED}API Error: {e}{Colors.RESET}")
            return None

    def get_network_info(self, network: str) -> Dict[str, Any]:
        """Get comprehensive network information"""
        result = {
            'network': network,
            'found': False,
            'network_obj': None,
            'container': None,
            'ip_stats': {},
            'dhcp_info': {},
            'dns_info': {},
            'gateway': None,
            'extattrs': {},
            'comment': None,
            'last_modified': None
        }

        # Step 1: Get network object
        params = {
            '_return_fields': 'network,comment,extattrs,network_container,options,members,dhcp_utilization,utilization,_ref,zone_associations,network_view'
        }
        networks = self._get(f"network?network={network}", params)

        if not networks or len(networks) == 0:
            return result

        net_obj = networks[0]
        result['found'] = True
        result['network_obj'] = net_obj
        result['comment'] = net_obj.get('comment', '')
        result['extattrs'] = net_obj.get('extattrs', {})

        # Step 2: Get network container if exists
        container_ref = net_obj.get('network_container')
        if container_ref:
            container_params = {'_return_fields': 'network,comment'}
            container = self._get(container_ref.replace(f'/wapi/{self.wapi_version}/', ''), container_params)
            if container:
                result['container'] = container

        # Step 3: Calculate IP statistics
        try:
            net = ipaddress.IPv4Network(network, strict=False)
            total_ips = net.num_addresses - 2  # Exclude network and broadcast

            # Get utilization from InfoBlox
            utilization = net_obj.get('utilization', 0)
            dhcp_utilization = net_obj.get('dhcp_utilization', {})

            result['ip_stats'] = {
                'total_usable': total_ips,
                'utilization_percent': utilization,
                'dhcp_utilization': dhcp_utilization,
                'network_address': str(net.network_address),
                'broadcast_address': str(net.broadcast_address),
                'netmask': str(net.netmask),
                'prefix_length': net.prefixlen
            }
        except Exception as e:
            print(f"{Colors.YELLOW}Warning: Could not calculate IP stats: {e}{Colors.RESET}")

        # Step 4: Extract DHCP info from options
        options = net_obj.get('options', [])
        result['dhcp_info'] = self._extract_dhcp_options(options)

        # Step 5: Extract DNS zones
        zone_assoc = net_obj.get('zone_associations', [])
        result['dns_info'] = zone_assoc

        # Step 6: Extract gateway
        for option in options:
            if option.get('name') == 'routers':
                result['gateway'] = option.get('value')
                break

        return result

    def get_ip_info(self, ip_address: str) -> Dict[str, Any]:
        """Get comprehensive IP address information"""
        result = {
            'ip': ip_address,
            'status': 'UNKNOWN',
            'allocation_type': None,
            'ipv4address': None,
            'fixed_address': None,
            'dhcp_lease': None,
            'dns_a_record': None,
            'dns_ptr_record': None,
            'host_record': None,
            'network': None,
            'container': None
        }

        # Step 1: Get IP address status
        params = {'_return_fields': 'ip_address,status,types,objects,network,usage,names'}
        ipv4_obj = self._get(f"ipv4address?ip_address={ip_address}", params)
        if ipv4_obj and len(ipv4_obj) > 0:
            result['ipv4address'] = ipv4_obj[0]
            result['status'] = ipv4_obj[0].get('status', 'UNKNOWN')

        # Step 2: Check for fixed address
        params = {'_return_fields': 'ipv4addr,mac,name,comment,extattrs,network,_ref,ddns_protected,match_client'}
        fixed = self._get(f"fixedaddress?ipv4addr={ip_address}", params)
        if fixed and len(fixed) > 0:
            result['fixed_address'] = fixed[0]
            result['allocation_type'] = 'FIXED'

        # Step 3: Check for DHCP lease
        params = {'_return_fields': 'address,binding_state,client_hostname,ends,hardware,starts,tstp,tsfp,cltt,uid'}
        lease = self._get(f"lease?address={ip_address}", params)
        if lease and len(lease) > 0:
            result['dhcp_lease'] = lease[0]
            if not result['allocation_type']:
                result['allocation_type'] = 'DHCP'

        # Step 4: Check for DNS A record
        params = {'_return_fields': 'name,ipv4addr,zone,view,ttl,creation_time,last_queried,_ref'}
        a_record = self._get(f"record:a?ipv4addr={ip_address}", params)
        if a_record and len(a_record) > 0:
            result['dns_a_record'] = a_record[0]

        # Step 5: Check for DNS PTR record
        params = {'_return_fields': 'ptrdname,ipv4addr,zone,view,ttl,_ref'}
        ptr_record = self._get(f"record:ptr?ipv4addr={ip_address}", params)
        if ptr_record and len(ptr_record) > 0:
            result['dns_ptr_record'] = ptr_record[0]

        # Step 6: Check for host record
        params = {'_return_fields': 'name,ipv4addrs,comment,extattrs,zone,_ref'}
        host = self._get(f"record:host?ipv4addr={ip_address}", params)
        if host and len(host) > 0:
            result['host_record'] = host[0]
            if not result['allocation_type']:
                result['allocation_type'] = 'HOST_RECORD'

        # Step 7: Get parent network
        if result['ipv4address']:
            network_ref = result['ipv4address'].get('network')
            if network_ref:
                params = {'_return_fields': 'network,comment,network_container,extattrs'}
                network = self._get(network_ref.replace(f'/wapi/{self.wapi_version}/', ''), params)
                if network:
                    result['network'] = network

                    # Get container
                    container_ref = network.get('network_container')
                    if container_ref:
                        container = self._get(container_ref.replace(f'/wapi/{self.wapi_version}/', ''), {'_return_fields': 'network,comment'})
                        if container:
                            result['container'] = container

        # Determine final status
        if not result['allocation_type'] and result['status'] != 'USED':
            result['allocation_type'] = 'AVAILABLE'

        return result

    def get_zone_info(self, zone_name: str) -> Dict[str, Any]:
        """Get comprehensive DNS zone information"""
        result = {
            'zone': zone_name,
            'found': False,
            'zone_obj': None,
            'ns_group': None,
            'subzones': [],
            'record_stats': {},
            'soa_info': {},
            'parent_zone': None
        }

        # Step 1: Get zone object
        params = {
            '_return_fields': 'fqdn,view,ns_group,zone_format,comment,extattrs,soa_default_ttl,soa_expire,soa_negative_ttl,soa_refresh,soa_retry,soa_serial_number,parent,_ref'
        }
        zones = self._get(f"zone_auth?fqdn={zone_name}", params)

        if not zones or len(zones) == 0:
            return result

        zone_obj = zones[0]
        result['found'] = True
        result['zone_obj'] = zone_obj

        # Extract SOA information
        result['soa_info'] = {
            'serial': zone_obj.get('soa_serial_number'),
            'refresh': zone_obj.get('soa_refresh'),
            'retry': zone_obj.get('soa_retry'),
            'expire': zone_obj.get('soa_expire'),
            'ttl': zone_obj.get('soa_default_ttl'),
            'negative_ttl': zone_obj.get('soa_negative_ttl')
        }

        # Step 2: Get NS group details
        ns_group_name = zone_obj.get('ns_group')
        if ns_group_name:
            params = {'_return_fields': 'name,grid_primary,grid_secondaries,external_primaries,external_secondaries'}
            ns_groups = self._get(f"nsgroup?name={ns_group_name}", params)
            if ns_groups and len(ns_groups) > 0:
                result['ns_group'] = ns_groups[0]

        # Step 3: Get subzones
        params = {'_return_fields': 'fqdn,ns_group,zone_format,comment'}
        # Search for zones that have this zone as parent
        all_zones = self._get(f"zone_auth", params)
        if all_zones:
            for z in all_zones:
                z_fqdn = z.get('fqdn', '')
                if z_fqdn != zone_name and z_fqdn.endswith(f'.{zone_name}'):
                    result['subzones'].append(z)

        # Step 4: Get record statistics
        record_types = ['record:a', 'record:aaaa', 'record:cname', 'record:mx', 'record:txt', 'record:srv', 'record:ptr']
        for rtype in record_types:
            records = self._get(f"{rtype}?zone={zone_name}&_max_results=1")
            if records is not None:
                # Get count by making another call with _return_fields to be lighter
                all_records = self._get(f"{rtype}?zone={zone_name}")
                count = len(all_records) if all_records else 0
                result['record_stats'][rtype.split(':')[1].upper()] = count

        return result

    def _extract_dhcp_options(self, options: List[Dict]) -> Dict[str, Any]:
        """Extract DHCP configuration from options"""
        dhcp_info = {
            'enabled': False,
            'range_start': None,
            'range_end': None,
            'lease_time': None,
            'routers': [],
            'dns_servers': [],
            'domain_name': None
        }

        if not options:
            return dhcp_info

        dhcp_info['enabled'] = True

        for option in options:
            name = option.get('name', '')
            value = option.get('value', '')

            if name == 'routers':
                dhcp_info['routers'] = value.split(',') if value else []
            elif name == 'domain-name-servers':
                dhcp_info['dns_servers'] = value.split(',') if value else []
            elif name == 'domain-name':
                dhcp_info['domain_name'] = value
            elif name == 'lease-time':
                dhcp_info['lease_time'] = value

        return dhcp_info


def format_network_output(data: Dict[str, Any]) -> str:
    """Format network information for display"""
    if not data['found']:
        return f"{Colors.RED}Network not found: {data['network']}{Colors.RESET}"

    output = []
    net_obj = data['network_obj']

    output.append(f"\n{Colors.BOLD}Network:{Colors.RESET}                {data['network']}")

    # Container
    if data['container']:
        container_net = data['container'].get('network', 'Unknown')
        container_comment = data['container'].get('comment', '')
        output.append(f"{Colors.BOLD}Network Container:{Colors.RESET}      {container_net} ({container_comment})" if container_comment else f"{Colors.BOLD}Network Container:{Colors.RESET}      {container_net}")

    # Comment
    if data['comment']:
        output.append(f"{Colors.BOLD}Comment:{Colors.RESET}                {data['comment']}")

    # Network View
    if net_obj.get('network_view'):
        output.append(f"{Colors.BOLD}Network View:{Colors.RESET}           {net_obj['network_view']}")

    # Extensible Attributes
    if data['extattrs']:
        output.append(f"\n{Colors.BOLD}Extensible Attributes:{Colors.RESET}")
        for key, value_obj in sorted(data['extattrs'].items()):
            value = value_obj.get('value', '') if isinstance(value_obj, dict) else value_obj
            output.append(f"  • {key:20s} {value}")

    # IP Statistics
    if data['ip_stats']:
        stats = data['ip_stats']
        output.append(f"\n{Colors.BOLD}IP Address Statistics:{Colors.RESET}")
        output.append(f"  • Total Usable IPs:   {stats.get('total_usable', 'N/A')}")
        output.append(f"  • Utilization:        {stats.get('utilization_percent', 0)}%")
        output.append(f"  • Network Address:    {stats.get('network_address', 'N/A')}")
        output.append(f"  • Broadcast Address:  {stats.get('broadcast_address', 'N/A')}")
        output.append(f"  • Netmask:            {stats.get('netmask', 'N/A')}")
        output.append(f"  • Prefix Length:      /{stats.get('prefix_length', 'N/A')}")

    # Gateway
    if data['gateway']:
        output.append(f"\n{Colors.BOLD}Gateway Configuration:{Colors.RESET}")
        output.append(f"  • Default Gateway:    {data['gateway']}")

    # DHCP Information
    dhcp = data['dhcp_info']
    if dhcp.get('enabled'):
        output.append(f"\n{Colors.BOLD}DHCP Configuration:{Colors.RESET}")
        output.append(f"  • DHCP Enabled:       Yes")
        if dhcp.get('routers'):
            output.append(f"  • Routers:            {', '.join(dhcp['routers'])}")
        if dhcp.get('dns_servers'):
            output.append(f"  • DNS Servers:        {', '.join(dhcp['dns_servers'])}")
        if dhcp.get('domain_name'):
            output.append(f"  • Domain Name:        {dhcp['domain_name']}")
        if dhcp.get('lease_time'):
            output.append(f"  • Lease Time:         {dhcp['lease_time']} seconds")

    # DNS Zones
    if data['dns_info']:
        output.append(f"\n{Colors.BOLD}DNS Zone Associations:{Colors.RESET}")
        for zone_assoc in data['dns_info']:
            output.append(f"  • {zone_assoc}")

    output.append("")
    return '\n'.join(output)


def format_ip_output(data: Dict[str, Any]) -> str:
    """Format IP address information for display"""
    output = []

    output.append(f"\n{Colors.BOLD}IP Address:{Colors.RESET}             {data['ip']}")

    # Status
    status_display = {
        'USED': f"{Colors.GREEN}✓ IN USE{Colors.RESET}",
        'UNUSED': f"{Colors.YELLOW}⚬ AVAILABLE{Colors.RESET}",
        'UNKNOWN': f"{Colors.RED}? UNKNOWN{Colors.RESET}"
    }
    output.append(f"{Colors.BOLD}Status:{Colors.RESET}                 {status_display.get(data['status'], data['status'])}")

    # Allocation Type
    if data['allocation_type']:
        output.append(f"{Colors.BOLD}Allocation Type:{Colors.RESET}        {data['allocation_type']}")

    # Fixed Address Details
    if data['fixed_address']:
        fixed = data['fixed_address']
        output.append(f"\n{Colors.BOLD}Fixed Address Details:{Colors.RESET}")
        if fixed.get('mac'):
            output.append(f"  • MAC Address:        {fixed['mac']}")
        if fixed.get('name'):
            output.append(f"  • Host Name:          {fixed['name']}")
        if fixed.get('comment'):
            output.append(f"  • Comment:            {fixed['comment']}")
        if fixed.get('extattrs'):
            output.append(f"  • Extensible Attrs:   {len(fixed['extattrs'])} attributes")
            for key, value_obj in sorted(fixed['extattrs'].items()):
                value = value_obj.get('value', '') if isinstance(value_obj, dict) else value_obj
                output.append(f"    - {key}: {value}")

    # DHCP Lease Details
    if data['dhcp_lease']:
        lease = data['dhcp_lease']
        output.append(f"\n{Colors.BOLD}DHCP Lease Details:{Colors.RESET}")
        if lease.get('binding_state'):
            output.append(f"  • Binding State:      {lease['binding_state']}")
        if lease.get('client_hostname'):
            output.append(f"  • Client Hostname:    {lease['client_hostname']}")
        if lease.get('hardware'):
            output.append(f"  • MAC Address:        {lease['hardware']}")
        if lease.get('starts'):
            output.append(f"  • Lease Start:        {lease['starts']}")
        if lease.get('ends'):
            output.append(f"  • Lease End:          {lease['ends']}")

    # Host Record Details
    if data['host_record']:
        host = data['host_record']
        output.append(f"\n{Colors.BOLD}Host Record Details:{Colors.RESET}")
        if host.get('name'):
            output.append(f"  • Hostname:           {host['name']}")
        if host.get('comment'):
            output.append(f"  • Comment:            {host['comment']}")
        if host.get('zone'):
            output.append(f"  • Zone:               {host['zone']}")

    # DNS Records
    if data['dns_a_record'] or data['dns_ptr_record']:
        output.append(f"\n{Colors.BOLD}DNS Records:{Colors.RESET}")

        if data['dns_a_record']:
            a_rec = data['dns_a_record']
            output.append(f"  • A Record:           {a_rec.get('name', 'N/A')} → {a_rec.get('ipv4addr', 'N/A')}")
            if a_rec.get('zone'):
                output.append(f"    Zone:               {a_rec['zone']}")
            if a_rec.get('ttl'):
                output.append(f"    TTL:                {a_rec['ttl']}")
            if a_rec.get('last_queried'):
                output.append(f"    Last Queried:       {a_rec['last_queried']}")

        if data['dns_ptr_record']:
            ptr_rec = data['dns_ptr_record']
            output.append(f"  • PTR Record:         {ptr_rec.get('ptrdname', 'N/A')}")
            if ptr_rec.get('zone'):
                output.append(f"    Zone:               {ptr_rec['zone']}")

    # Network Information
    if data['network']:
        network = data['network']
        output.append(f"\n{Colors.BOLD}Network Information:{Colors.RESET}")
        output.append(f"  • Network:            {network.get('network', 'N/A')}")
        if network.get('comment'):
            output.append(f"  • Comment:            {network['comment']}")

        if data['container']:
            container = data['container']
            container_net = container.get('network', 'Unknown')
            container_comment = container.get('comment', '')
            output.append(f"  • Network Container:  {container_net} ({container_comment})" if container_comment else f"  • Network Container:  {container_net}")

    output.append("")
    return '\n'.join(output)


def format_zone_output(data: Dict[str, Any]) -> str:
    """Format DNS zone information for display"""
    if not data['found']:
        return f"{Colors.RED}Zone not found: {data['zone']}{Colors.RESET}"

    output = []
    zone_obj = data['zone_obj']

    output.append(f"\n{Colors.BOLD}Zone Name:{Colors.RESET}              {data['zone']}")

    # Zone Type
    zone_format = zone_obj.get('zone_format', 'FORWARD')
    zone_type = 'Authoritative (Forward)' if zone_format == 'FORWARD' else f'Authoritative ({zone_format})'
    output.append(f"{Colors.BOLD}Zone Type:{Colors.RESET}              {zone_type}")

    # View
    if zone_obj.get('view'):
        output.append(f"{Colors.BOLD}View:{Colors.RESET}                   {zone_obj['view']}")

    # Comment
    if zone_obj.get('comment'):
        output.append(f"{Colors.BOLD}Comment:{Colors.RESET}                {zone_obj['comment']}")

    # NS Group Information
    if data['ns_group']:
        ns_group = data['ns_group']
        output.append(f"\n{Colors.BOLD}Name Server Group:{Colors.RESET}")
        output.append(f"  • NS Group:           {ns_group.get('name', 'N/A')}")

        if ns_group.get('grid_primary'):
            output.append(f"  • Grid Primary:       {ns_group['grid_primary'][0].get('name', 'N/A')}")

        if ns_group.get('grid_secondaries'):
            output.append(f"  • Grid Secondaries:")
            for secondary in ns_group['grid_secondaries']:
                output.append(f"    - {secondary.get('name', 'N/A')}")

        if ns_group.get('external_primaries'):
            output.append(f"  • External Primaries:")
            for ext_pri in ns_group['external_primaries']:
                output.append(f"    - {ext_pri}")

    # SOA Configuration
    if data['soa_info']:
        soa = data['soa_info']
        output.append(f"\n{Colors.BOLD}SOA Configuration:{Colors.RESET}")
        if soa.get('serial'):
            output.append(f"  • Serial:             {soa['serial']}")
        if soa.get('refresh'):
            output.append(f"  • Refresh:            {soa['refresh']} seconds")
        if soa.get('retry'):
            output.append(f"  • Retry:              {soa['retry']} seconds")
        if soa.get('expire'):
            output.append(f"  • Expire:             {soa['expire']} seconds")
        if soa.get('ttl'):
            output.append(f"  • Default TTL:        {soa['ttl']} seconds")
        if soa.get('negative_ttl'):
            output.append(f"  • Negative TTL:       {soa['negative_ttl']} seconds")

    # Subzones
    if data['subzones']:
        output.append(f"\n{Colors.BOLD}Sub Zones:{Colors.RESET} ({len(data['subzones'])} zones)")
        for idx, subzone in enumerate(data['subzones'], 1):
            output.append(f"  {idx}. {subzone.get('fqdn', 'N/A')}")
            if subzone.get('ns_group'):
                output.append(f"     • NS Group:        {subzone['ns_group']}")
            if subzone.get('comment'):
                output.append(f"     • Comment:         {subzone['comment']}")

    # Record Statistics
    if data['record_stats']:
        output.append(f"\n{Colors.BOLD}Record Statistics:{Colors.RESET}")
        total = sum(data['record_stats'].values())
        output.append(f"  • Total Records:      {total:,}")
        for rtype, count in sorted(data['record_stats'].items()):
            if count > 0:
                output.append(f"  • {rtype} Records:         {count:,}")

    # Extensible Attributes
    if zone_obj.get('extattrs'):
        output.append(f"\n{Colors.BOLD}Extensible Attributes:{Colors.RESET}")
        for key, value_obj in sorted(zone_obj['extattrs'].items()):
            value = value_obj.get('value', '') if isinstance(value_obj, dict) else value_obj
            output.append(f"  • {key:20s} {value}")

    output.append("")
    return '\n'.join(output)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='InfoBlox Query Tool - Retrieve comprehensive object information',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -n 192.168.1.0/24          Query network details
  %(prog)s -i 192.168.1.50            Query IP address details
  %(prog)s -z corp.local              Query DNS zone details
  %(prog)s -n 192.168.1.0/24 -q       Quiet mode (use saved config)
        """
    )

    # Object type (mutually exclusive)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-n', '--network', metavar='NETWORK',
                      help='Query network (e.g., 192.168.1.0/24)')
    group.add_argument('-i', '--ip', metavar='IP_ADDRESS',
                      help='Query IP address (e.g., 192.168.1.50)')
    group.add_argument('-z', '--zone', metavar='ZONE',
                      help='Query DNS zone (e.g., corp.local)')

    # Quiet mode
    parser.add_argument('-q', '--quiet', action='store_true',
                       help='Quiet mode - use saved configuration without prompting')

    args = parser.parse_args()

    # Get configuration
    config = prompt_for_config(quiet=args.quiet)

    if not config.get('host') or not config.get('username') or not config.get('password'):
        print(f"{Colors.RED}Error: Missing required configuration{Colors.RESET}")
        sys.exit(1)

    # Create client
    client = InfoBloxClient(
        host=config['host'],
        username=config['username'],
        password=config['password'],
        wapi_version=config.get('wapi_version', WAPI_VERSION)
    )

    # Execute query
    if args.network:
        print_header("NETWORK INFORMATION")
        data = client.get_network_info(args.network)
        print(format_network_output(data))

    elif args.ip:
        print_header("IP ADDRESS INFORMATION")
        data = client.get_ip_info(args.ip)
        print(format_ip_output(data))

    elif args.zone:
        print_header("DNS ZONE INFORMATION")
        data = client.get_zone_info(args.zone)
        print(format_zone_output(data))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Interrupted by user{Colors.RESET}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.RESET}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

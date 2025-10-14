#!/usr/bin/env python3
"""
IP Address Information Module
Comprehensive IP address lookup for operations teams
"""

import ipaddress
from typing import Dict, Optional, Any, List
import requests
from config import get_settings
from validators import InputValidator

class IPInfoClient:
    """Client for comprehensive IP address information retrieval"""

    def __init__(self):
        self.settings = get_settings()
        self.session = requests.Session()
        self.session.auth = (self.settings.infoblox_user, self.settings.infoblox_password)
        self.session.verify = self.settings.get_ssl_verify()
        self.base_url = self.settings.get_infoblox_base_url()

    def find_ip_detailed(self, ip_address: str) -> Dict[str, Any]:
        """
        Get comprehensive IP address information for operations teams

        Args:
            ip_address: IP address (e.g., "192.168.1.50")

        Returns:
            Dictionary with comprehensive IP information
        """
        # Validate IP format
        try:
            ip_obj = ipaddress.ip_address(ip_address)
        except ValueError as e:
            return {
                "error": f"Invalid IP address format: {e}",
                "ip_address": ip_address
            }

        # Step 1: Check ipv4address object (shows usage status)
        ip_status = self._get_ip_status(str(ip_obj))

        # Step 2: Check for fixed address
        fixed_address = self._get_fixed_address(str(ip_obj))

        # Step 3: Check for DHCP lease
        dhcp_lease = self._get_dhcp_lease(str(ip_obj))

        # Step 4: Check for host record
        host_record = self._get_host_record(str(ip_obj))

        # Step 5: Get DNS records (A and PTR)
        dns_records = self._get_dns_records(str(ip_obj))

        # Step 6: Get network information
        network_info = self._get_network_info(str(ip_obj))

        # Determine allocation type and status
        allocation_type, status = self._determine_allocation_type(
            fixed_address, dhcp_lease, host_record, ip_status
        )

        # Compile comprehensive result
        result = {
            "ip_address": str(ip_obj),
            "status": status,
            "allocation_type": allocation_type,
            "fixed_address": fixed_address,
            "dhcp_lease": dhcp_lease,
            "host_record": host_record,
            "dns_records": dns_records,
            "network_info": network_info,
            "ip_status": ip_status
        }

        return result

    def _get_ip_status(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get IP address status from ipv4address object"""
        try:
            url = f"{self.base_url}/ipv4address"
            params = {
                "ip_address": ip_address,
                "_return_fields+": "ip_address,status,types,objects,network,usage"
            }

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            results = response.json()
            if results:
                return results[0]
            return None

        except Exception as e:
            print(f"Error fetching IP status: {e}")
            return None

    def _get_fixed_address(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get fixed address object if exists"""
        try:
            url = f"{self.base_url}/fixedaddress"
            params = {
                "ipv4addr": ip_address,
                "_return_fields+": "ipv4addr,mac,name,comment,extattrs,network,_ref"
            }

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            results = response.json()
            if results:
                return results[0]
            return None

        except Exception as e:
            print(f"Error fetching fixed address: {e}")
            return None

    def _get_dhcp_lease(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get DHCP lease if exists"""
        try:
            url = f"{self.base_url}/lease"
            params = {
                "address": ip_address,
                "_return_fields+": "address,binding_state,client_hostname,ends,hardware,network"
            }

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            results = response.json()
            if results:
                return results[0]
            return None

        except Exception as e:
            print(f"Error fetching DHCP lease: {e}")
            return None

    def _get_host_record(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get host record if exists"""
        try:
            url = f"{self.base_url}/record:host"
            params = {
                "ipv4addr": ip_address,
                "_return_fields+": "name,ipv4addrs,comment,extattrs"
            }

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            results = response.json()
            if results:
                return results[0]
            return None

        except Exception as e:
            print(f"Error fetching host record: {e}")
            return None

    def _get_dns_records(self, ip_address: str) -> Dict[str, Any]:
        """Get DNS A and PTR records"""
        dns_info = {
            "a_records": [],
            "ptr_records": []
        }

        # Get A records
        try:
            url = f"{self.base_url}/record:a"
            params = {
                "ipv4addr": ip_address,
                "_return_fields+": "name,ipv4addr,zone,view,last_queried,ttl"
            }

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            dns_info["a_records"] = response.json()

        except Exception as e:
            print(f"Error fetching A records: {e}")

        # Get PTR records
        try:
            url = f"{self.base_url}/record:ptr"
            params = {
                "ipv4addr": ip_address,
                "_return_fields+": "ptrdname,ipv4addr,zone,view"
            }

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            dns_info["ptr_records"] = response.json()

        except Exception as e:
            print(f"Error fetching PTR records: {e}")

        return dns_info

    def _get_network_info(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get network information for the IP"""
        try:
            # Use network_view search function
            url = f"{self.base_url}/ipv4address"
            params = {
                "ip_address": ip_address,
                "_return_fields+": "network,network_view"
            }

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            results = response.json()
            if results and "network" in results[0]:
                network = results[0]["network"]

                # Get full network object
                net_url = f"{self.base_url}/network"
                net_params = {
                    "network": network,
                    "_return_fields+": "network,comment,network_container,extattrs,options"
                }

                net_response = self.session.get(net_url, params=net_params, timeout=30)
                net_response.raise_for_status()

                net_results = net_response.json()
                if net_results:
                    net_obj = net_results[0]

                    # Get network container if present
                    container_info = None
                    if "network_container" in net_obj:
                        container_info = self._get_network_container(net_obj["network_container"])

                    # Extract gateway
                    gateway = self._extract_gateway(net_obj)

                    return {
                        "network": network,
                        "comment": net_obj.get("comment", ""),
                        "container": container_info,
                        "gateway": gateway,
                        "dhcp_enabled": bool(net_obj.get("members", []))
                    }

            return None

        except Exception as e:
            print(f"Error fetching network info: {e}")
            return None

    def _get_network_container(self, container_ref: str) -> Optional[Dict[str, str]]:
        """Get network container information"""
        try:
            url = f"{self.base_url}/{container_ref}"
            params = {"_return_fields+": "network,comment"}

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            container = response.json()
            return {
                "network": container.get("network", ""),
                "comment": container.get("comment", "")
            }

        except Exception:
            return None

    def _extract_gateway(self, network_obj: Dict) -> Optional[str]:
        """Extract default gateway from options"""
        if "options" in network_obj:
            for option in network_obj["options"]:
                if option.get("name") == "routers" or option.get("num") == 3:
                    return option.get("value", "")

        # Default to .1 if not found
        network = network_obj.get("network", "")
        if network:
            try:
                net = ipaddress.ip_network(network)
                return str(list(net.hosts())[0]) if net.num_addresses > 2 else None
            except:
                pass

        return None

    def _determine_allocation_type(
        self,
        fixed_address: Optional[Dict],
        dhcp_lease: Optional[Dict],
        host_record: Optional[Dict],
        ip_status: Optional[Dict]
    ) -> tuple:
        """Determine allocation type and status"""

        if fixed_address:
            return ("Fixed Address", "IN USE")
        elif dhcp_lease:
            binding_state = dhcp_lease.get("binding_state", "")
            if binding_state == "ACTIVE":
                return ("DHCP Lease (Active)", "IN USE")
            else:
                return (f"DHCP Lease ({binding_state})", "IN USE")
        elif host_record:
            return ("Host Record", "IN USE")
        elif ip_status and ip_status.get("usage"):
            # IP is tracked but not in standard objects
            types = ip_status.get("types", [])
            if types:
                return (", ".join(types), "IN USE")
            return ("Unknown Allocation", "IN USE")
        else:
            return ("Not Allocated", "AVAILABLE")

    def format_output(self, result: Dict[str, Any]) -> str:
        """Format the result as human-readable output"""
        if "error" in result:
            return f"❌ {result['error']}"

        output = []
        output.append("═" * 67)
        output.append("                    IP ADDRESS INFORMATION")
        output.append("═" * 67)
        output.append("")

        # Basic info
        output.append(f"IP Address:             {result['ip_address']}")

        # Status
        status_symbol = "✓" if result['status'] == "IN USE" else "⚬"
        output.append(f"Status:                 {status_symbol} {result['status']}")
        output.append("")

        # Allocation details (if in use)
        if result['status'] == "IN USE":
            output.append(f"Allocation Type:        {result['allocation_type']}")

            # MAC address
            mac = None
            if result['fixed_address']:
                mac = result['fixed_address'].get('mac', '')
            elif result['dhcp_lease']:
                mac = result['dhcp_lease'].get('hardware', '')

            if mac:
                output.append(f"MAC Address:            {mac}")

            # Host name
            hostname = None
            if result['fixed_address']:
                hostname = result['fixed_address'].get('name', '')
            elif result['dhcp_lease']:
                hostname = result['dhcp_lease'].get('client_hostname', '')
            elif result['host_record']:
                hostname = result['host_record'].get('name', '')

            if hostname:
                output.append(f"Host Name:              {hostname}")

            # Comment
            comment = None
            if result['fixed_address']:
                comment = result['fixed_address'].get('comment', '')
            elif result['host_record']:
                comment = result['host_record'].get('comment', '')

            if comment:
                output.append(f"Comment:                {comment}")

            output.append("")

        # Network information
        if result['network_info']:
            output.append("Network Information:")
            net_info = result['network_info']
            output.append(f"  • Network:            {net_info['network']}")

            if net_info['container']:
                container = net_info['container']
                container_desc = container['network']
                if container.get('comment'):
                    container_desc += f" ({container['comment']})"
                output.append(f"  • Network Container:  {container_desc}")

            if net_info['gateway']:
                output.append(f"  • Gateway:            {net_info['gateway']}")

            output.append("")

        # DNS Records
        dns = result['dns_records']
        if dns['a_records'] or dns['ptr_records']:
            output.append("DNS Records:")

            for a_rec in dns['a_records']:
                output.append(f"  • A Record:           {a_rec['name']} → {a_rec['ipv4addr']}")
                if a_rec.get('last_queried'):
                    output.append(f"    Last Queried:       {a_rec['last_queried']}")

            for ptr_rec in dns['ptr_records']:
                ptr_name = ptr_rec.get('ptrdname', '')
                ptr_zone = ptr_rec.get('zone', '')
                output.append(f"  • PTR Record:         {ptr_zone} → {ptr_name}")

            output.append("")
        else:
            output.append("DNS Records:            None")
            output.append("")

        # DHCP information
        if result['network_info']:
            output.append("DHCP Information:")
            dhcp_type = "DHCP Lease" if result['dhcp_lease'] else "Fixed/Static"
            output.append(f"  • Type:               {dhcp_type}")

            if result['network_info']['dhcp_enabled']:
                output.append(f"  • DHCP Enabled:       Yes (network has DHCP)")
            else:
                output.append(f"  • DHCP Enabled:       No")

            output.append("")

        # Extensible attributes
        extattrs = {}
        if result['fixed_address'] and 'extattrs' in result['fixed_address']:
            extattrs = self._format_extensible_attributes(result['fixed_address']['extattrs'])
        elif result['host_record'] and 'extattrs' in result['host_record']:
            extattrs = self._format_extensible_attributes(result['host_record']['extattrs'])

        if extattrs:
            output.append("Extensible Attributes:")
            for key, value in extattrs.items():
                output.append(f"  • {key:20} {value}")
            output.append("")

        output.append("═" * 67)

        return "\n".join(output)

    def _format_extensible_attributes(self, extattrs: Dict) -> Dict[str, str]:
        """Format extensible attributes in alphabetical order"""
        if not extattrs:
            return {}

        formatted = {}
        for key in sorted(extattrs.keys()):
            value = extattrs[key]
            # Extract value from EA structure
            if isinstance(value, dict) and "value" in value:
                formatted[key] = str(value["value"])
            else:
                formatted[key] = str(value)

        return formatted


# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ip_info.py <ip_address>")
        print("Example: python ip_info.py 192.168.1.50")
        sys.exit(1)

    client = IPInfoClient()
    result = client.find_ip_detailed(sys.argv[1])
    print(client.format_output(result))

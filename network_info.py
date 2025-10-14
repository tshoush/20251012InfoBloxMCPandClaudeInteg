#!/usr/bin/env python3
"""
Network Information Module
Comprehensive network lookup for operations teams
"""

import ipaddress
from typing import Dict, Optional, Any, List
import requests
from config import get_settings
from validators import InputValidator

class NetworkInfoClient:
    """Client for comprehensive network information retrieval"""

    def __init__(self):
        self.settings = get_settings()
        self.session = requests.Session()
        self.session.auth = (self.settings.infoblox_user, self.settings.infoblox_password)
        self.session.verify = self.settings.get_ssl_verify()
        self.base_url = self.settings.get_infoblox_base_url()

    def find_network_detailed(self, network: str) -> Dict[str, Any]:
        """
        Get comprehensive network information for operations teams

        Args:
            network: Network in CIDR notation (e.g., "192.168.1.0/24")

        Returns:
            Dictionary with comprehensive network information
        """
        # Validate network format
        try:
            net = ipaddress.ip_network(network, strict=False)
        except ValueError as e:
            return {
                "error": f"Invalid network format: {e}",
                "network": network
            }

        # Step 1: Get network object with all fields
        network_obj = self._get_network_object(str(net))
        if not network_obj:
            return {
                "error": f"Network not found: {network}",
                "network": network
            }

        # Step 2: Get network container if present
        container_info = None
        if "network_container" in network_obj:
            container_info = self._get_network_container(network_obj["network_container"])

        # Step 3: Calculate IP statistics
        ip_stats = self._calculate_ip_statistics(net, network_obj)

        # Step 4: Get DHCP information
        dhcp_info = self._extract_dhcp_info(network_obj)

        # Step 5: Get DNS information
        dns_info = self._extract_dns_info(network_obj)

        # Step 6: Extract gateway
        gateway = self._extract_gateway(network_obj, str(net))

        # Step 7: Format extensible attributes
        extattrs = self._format_extensible_attributes(network_obj.get("extattrs", {}))

        # Compile comprehensive result
        result = {
            "network": str(net),
            "network_container": container_info,
            "comment": network_obj.get("comment", ""),
            "extensible_attributes": extattrs,
            "ip_statistics": ip_stats,
            "gateway": gateway,
            "dhcp": dhcp_info,
            "dns": dns_info,
            "last_modified": network_obj.get("_ref", "").split(":")[-1] if "_ref" in network_obj else None,
            "reference": network_obj.get("_ref", ""),
            "raw_data": network_obj  # For debugging
        }

        return result

    def _get_network_object(self, network: str) -> Optional[Dict[str, Any]]:
        """Get network object from InfoBlox"""
        try:
            url = f"{self.base_url}/network"
            params = {
                "network": network,
                "_return_fields+": "network,comment,extattrs,network_container,options,members,dhcp_utilization,usage"
            }

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            results = response.json()
            if results:
                return results[0]
            return None

        except Exception as e:
            print(f"Error fetching network: {e}")
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

    def _calculate_ip_statistics(self, net: ipaddress.IPv4Network, network_obj: Dict) -> Dict[str, Any]:
        """Calculate IP address statistics"""
        # Total usable IPs (excluding network and broadcast)
        total_usable = net.num_addresses - 2 if net.num_addresses > 2 else 0

        # Try to get utilization from InfoBlox
        ips_used = 0
        if "dhcp_utilization" in network_obj:
            # dhcp_utilization is number of leases
            ips_used = network_obj["dhcp_utilization"]
        elif "usage" in network_obj:
            # usage might be a list of used IPs
            ips_used = len(network_obj["usage"]) if isinstance(network_obj["usage"], list) else 0

        ips_free = total_usable - ips_used
        utilization_percent = (ips_used / total_usable * 100) if total_usable > 0 else 0

        return {
            "total_usable": total_usable,
            "ips_used": ips_used,
            "ips_free": ips_free,
            "utilization_percent": round(utilization_percent, 1),
            "network_address": str(net.network_address),
            "broadcast_address": str(net.broadcast_address)
        }

    def _extract_dhcp_info(self, network_obj: Dict) -> Dict[str, Any]:
        """Extract DHCP configuration"""
        dhcp_info = {
            "enabled": False,
            "ranges": []
        }

        # Check if DHCP members are configured
        if "members" in network_obj and network_obj["members"]:
            dhcp_info["enabled"] = True

        # Look for DHCP ranges in options or separate API call
        # This would require additional API call to get ranges
        # For now, indicate if DHCP is enabled

        return dhcp_info

    def _extract_dns_info(self, network_obj: Dict) -> Dict[str, Any]:
        """Extract DNS configuration"""
        dns_info = {
            "zone": None,
            "reverse_zone": None
        }

        # DNS zone info would typically come from separate API calls
        # or from extensible attributes

        return dns_info

    def _extract_gateway(self, network_obj: Dict, network: str) -> Optional[str]:
        """Extract default gateway from options"""
        # Check DHCP options for gateway
        if "options" in network_obj:
            for option in network_obj["options"]:
                if option.get("name") == "routers" or option.get("num") == 3:
                    return option.get("value", "")

        # Default to .1 if not found
        net = ipaddress.ip_network(network)
        return str(list(net.hosts())[0]) if net.num_addresses > 2 else None

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

    def format_output(self, result: Dict[str, Any]) -> str:
        """Format the result as human-readable output"""
        if "error" in result:
            return f"❌ {result['error']}"

        output = []
        output.append("═" * 67)
        output.append("                    NETWORK INFORMATION")
        output.append("═" * 67)
        output.append("")

        # Basic info
        output.append(f"Network:                {result['network']}")

        # Network container
        if result['network_container']:
            container = result['network_container']
            container_desc = f"{container['network']}"
            if container.get('comment'):
                container_desc += f" ({container['comment']})"
            output.append(f"Network Container:      {container_desc}")
        else:
            output.append(f"Network Container:      None (Top-level network)")

        # Comment
        output.append(f"Comment:                {result['comment'] or 'None'}")
        output.append("")

        # Extensible attributes
        if result['extensible_attributes']:
            output.append("Extensible Attributes:")
            for key, value in result['extensible_attributes'].items():
                output.append(f"  • {key:20} {value}")
        else:
            output.append("Extensible Attributes:  None")
        output.append("")

        # IP statistics
        stats = result['ip_statistics']
        output.append("IP Address Statistics:")
        output.append(f"  • Total Usable IPs:   {stats['total_usable']}")
        output.append(f"  • IPs Used:           {stats['ips_used']} ({stats['utilization_percent']}%)")
        output.append(f"  • IPs Free:           {stats['ips_free']} ({100-stats['utilization_percent']:.1f}%)")
        output.append(f"  • Network Address:    {stats['network_address']}")
        output.append(f"  • Broadcast Address:  {stats['broadcast_address']}")
        output.append("")

        # Gateway
        if result['gateway']:
            output.append("Gateway Configuration:")
            output.append(f"  • Default Gateway:    {result['gateway']}")
            output.append("")

        # DHCP
        dhcp = result['dhcp']
        output.append("DHCP Configuration:")
        output.append(f"  • DHCP Enabled:       {'Yes' if dhcp['enabled'] else 'No'}")
        if dhcp['ranges']:
            for dhcp_range in dhcp['ranges']:
                output.append(f"  • DHCP Range:         {dhcp_range}")
        output.append("")

        # Reference
        output.append(f"Reference:              {result['reference']}")

        output.append("═" * 67)

        return "\n".join(output)


# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python network_info.py <network>")
        print("Example: python network_info.py 192.168.1.0/24")
        sys.exit(1)

    client = NetworkInfoClient()
    result = client.find_network_detailed(sys.argv[1])
    print(client.format_output(result))

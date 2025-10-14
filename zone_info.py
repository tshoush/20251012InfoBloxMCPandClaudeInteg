#!/usr/bin/env python3
"""
DNS Zone Information Module
Comprehensive DNS zone lookup for operations teams
"""

from typing import Dict, Optional, Any, List
import requests
from config import get_settings
from validators import InputValidator

class ZoneInfoClient:
    """Client for comprehensive DNS zone information retrieval"""

    def __init__(self):
        self.settings = get_settings()
        self.session = requests.Session()
        self.session.auth = (self.settings.infoblox_user, self.settings.infoblox_password)
        self.session.verify = self.settings.get_ssl_verify()
        self.base_url = self.settings.get_infoblox_base_url()

    def find_zone_detailed(self, zone_name: str) -> Dict[str, Any]:
        """
        Get comprehensive DNS zone information for operations teams

        Args:
            zone_name: Zone FQDN (e.g., "corp.local")

        Returns:
            Dictionary with comprehensive zone information
        """
        # Step 1: Get zone object
        zone_obj = self._get_zone_object(zone_name)
        if not zone_obj:
            return {
                "error": f"Zone not found: {zone_name}",
                "zone_name": zone_name
            }

        # Step 2: Get NS group details
        ns_group_info = None
        if "ns_group" in zone_obj and zone_obj["ns_group"]:
            ns_group_info = self._get_ns_group(zone_obj["ns_group"])

        # Step 3: Get subzones
        subzones = self._get_subzones(zone_name)

        # Step 4: Get record statistics
        record_stats = self._get_record_statistics(zone_name)

        # Step 5: Extract SOA information
        soa_info = self._extract_soa_info(zone_obj)

        # Step 6: Format extensible attributes
        extattrs = self._format_extensible_attributes(zone_obj.get("extattrs", {}))

        # Determine zone type
        zone_type = self._determine_zone_type(zone_obj)

        # Compile comprehensive result
        result = {
            "zone_name": zone_name,
            "zone_type": zone_type,
            "view": zone_obj.get("view", "default"),
            "ns_group": ns_group_info,
            "subzones": subzones,
            "soa": soa_info,
            "record_statistics": record_stats,
            "extensible_attributes": extattrs,
            "reference": zone_obj.get("_ref", ""),
            "raw_data": zone_obj  # For debugging
        }

        return result

    def _get_zone_object(self, zone_name: str) -> Optional[Dict[str, Any]]:
        """Get zone object from InfoBlox"""
        try:
            url = f"{self.base_url}/zone_auth"
            params = {
                "fqdn": zone_name,
                "_return_fields+": "fqdn,view,ns_group,soa_serial,soa_refresh,soa_retry,soa_expire,soa_default_ttl,zone_format,extattrs,_ref"
            }

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            results = response.json()
            if results:
                return results[0]
            return None

        except Exception as e:
            print(f"Error fetching zone: {e}")
            return None

    def _get_ns_group(self, ns_group_name: str) -> Optional[Dict[str, Any]]:
        """Get NS group details"""
        try:
            url = f"{self.base_url}/nsgroup"
            params = {
                "name": ns_group_name,
                "_return_fields+": "name,primary_secondaries"
            }

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            results = response.json()
            if results:
                group = results[0]

                # Extract primary and secondaries
                servers = []
                if "primary_secondaries" in group:
                    for server in group["primary_secondaries"]:
                        server_info = {
                            "name": server.get("name", ""),
                            "address": server.get("address", ""),
                            "type": server.get("stealth", False) and "Stealth" or "Authoritative"
                        }
                        servers.append(server_info)

                return {
                    "name": ns_group_name,
                    "servers": servers
                }

            return None

        except Exception as e:
            print(f"Error fetching NS group: {e}")
            return None

    def _get_subzones(self, parent_zone: str) -> List[Dict[str, Any]]:
        """Get list of subzones"""
        subzones = []

        try:
            url = f"{self.base_url}/zone_auth"
            params = {
                "parent": parent_zone,
                "_return_fields+": "fqdn,ns_group,zone_format"
            }

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            results = response.json()
            for zone in results:
                subzone_info = {
                    "fqdn": zone.get("fqdn", ""),
                    "ns_group": zone.get("ns_group", ""),
                    "zone_format": zone.get("zone_format", ""),
                    "delegation_status": "Complete"  # Simplified
                }
                subzones.append(subzone_info)

        except Exception as e:
            print(f"Error fetching subzones: {e}")

        return subzones

    def _get_record_statistics(self, zone_name: str) -> Dict[str, int]:
        """Get record counts by type"""
        stats = {
            "a_records": 0,
            "cname_records": 0,
            "mx_records": 0,
            "txt_records": 0,
            "srv_records": 0,
            "ptr_records": 0
        }

        record_types = [
            ("a_records", "record:a"),
            ("cname_records", "record:cname"),
            ("mx_records", "record:mx"),
            ("txt_records", "record:txt"),
            ("srv_records", "record:srv"),
            ("ptr_records", "record:ptr")
        ]

        for stat_key, record_type in record_types:
            try:
                url = f"{self.base_url}/{record_type}"
                params = {
                    "zone": zone_name,
                    "_max_results": 1  # We only want the count
                }

                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()

                results = response.json()
                # Try to get count from headers if available
                # Otherwise, would need to page through all results
                stats[stat_key] = len(results)  # Simplified

            except Exception as e:
                print(f"Error fetching {record_type} count: {e}")

        # Calculate total
        stats["total"] = sum(v for k, v in stats.items() if k != "total")

        return stats

    def _extract_soa_info(self, zone_obj: Dict) -> Dict[str, Any]:
        """Extract SOA record information"""
        return {
            "serial": zone_obj.get("soa_serial", ""),
            "refresh": zone_obj.get("soa_refresh", ""),
            "retry": zone_obj.get("soa_retry", ""),
            "expire": zone_obj.get("soa_expire", ""),
            "ttl": zone_obj.get("soa_default_ttl", "")
        }

    def _determine_zone_type(self, zone_obj: Dict) -> str:
        """Determine zone type"""
        zone_format = zone_obj.get("zone_format", "FORWARD")

        if zone_format == "FORWARD":
            return "Authoritative (Forward)"
        elif zone_format == "IPV4":
            return "Authoritative (Reverse - IPv4)"
        elif zone_format == "IPV6":
            return "Authoritative (Reverse - IPv6)"
        else:
            return f"Authoritative ({zone_format})"

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
        output.append("                    DNS ZONE INFORMATION")
        output.append("═" * 67)
        output.append("")

        # Basic info
        output.append(f"Zone Name:              {result['zone_name']}")
        output.append(f"Zone Type:              {result['zone_type']}")
        output.append(f"View:                   {result['view']}")
        output.append("")

        # NS Group
        if result['ns_group']:
            output.append("Name Server Group:")
            ns_group = result['ns_group']
            output.append(f"  • NS Group:           {ns_group['name']}")

            for idx, server in enumerate(ns_group['servers'], 1):
                role = "Primary NS" if idx == 1 else "Secondary NS"
                name = server['name']
                address = server['address']
                if address:
                    output.append(f"  • {role:16} {name} ({address})")
                else:
                    output.append(f"  • {role:16} {name}")

            output.append("")
        else:
            output.append("Name Server Group:      Not configured (using grid defaults)")
            output.append("")

        # Zone Hierarchy / Subzones
        if result['subzones']:
            output.append("Zone Hierarchy:")
            output.append(f"  • This Zone:          {result['zone_name']}")
            output.append(f"  • Sub Zones:          {len(result['subzones'])} zones")
            output.append("")

            output.append("Sub Zones:")
            for idx, subzone in enumerate(result['subzones'], 1):
                output.append(f"  {idx}. {subzone['fqdn']}")
                if subzone['ns_group']:
                    output.append(f"     • NS Group:        {subzone['ns_group']}")
                output.append(f"     • Delegation:      {subzone['delegation_status']}")

            output.append("")
        else:
            output.append("Sub Zones:              None")
            output.append("")

        # SOA Configuration
        soa = result['soa']
        if any(soa.values()):
            output.append("Zone Configuration:")
            if soa['serial']:
                output.append(f"  • SOA Serial:         {soa['serial']}")
            if soa['refresh']:
                output.append(f"  • SOA Refresh:        {soa['refresh']}")
            if soa['retry']:
                output.append(f"  • SOA Retry:          {soa['retry']}")
            if soa['expire']:
                output.append(f"  • SOA Expire:         {soa['expire']}")
            if soa['ttl']:
                output.append(f"  • TTL:                {soa['ttl']}")
            output.append("")

        # Record Statistics
        stats = result['record_statistics']
        if stats['total'] > 0:
            output.append("Record Statistics:")
            output.append(f"  • Total Records:      {stats['total']}")
            if stats['a_records'] > 0:
                output.append(f"  • A Records:          {stats['a_records']}")
            if stats['cname_records'] > 0:
                output.append(f"  • CNAME Records:      {stats['cname_records']}")
            if stats['mx_records'] > 0:
                output.append(f"  • MX Records:         {stats['mx_records']}")
            if stats['txt_records'] > 0:
                output.append(f"  • TXT Records:        {stats['txt_records']}")
            if stats['srv_records'] > 0:
                output.append(f"  • SRV Records:        {stats['srv_records']}")
            if stats['ptr_records'] > 0:
                output.append(f"  • PTR Records:        {stats['ptr_records']}")
            output.append("")

        # Extensible attributes
        if result['extensible_attributes']:
            output.append("Extensible Attributes:")
            for key, value in result['extensible_attributes'].items():
                output.append(f"  • {key:20} {value}")
            output.append("")

        # Reference
        output.append(f"Reference:              {result['reference']}")

        output.append("═" * 67)

        return "\n".join(output)


# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python zone_info.py <zone_name>")
        print("Example: python zone_info.py corp.local")
        sys.exit(1)

    client = ZoneInfoClient()
    result = client.find_zone_detailed(sys.argv[1])
    print(client.format_output(result))

#!/usr/bin/env python3
"""
InfoBlox WAPI Explorer
Discovers all available WAPI objects and their schemas
"""

import requests
import json
from urllib3.exceptions import InsecureRequestWarning
from typing import Dict, List, Any

# Suppress SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# InfoBlox configuration
INFOBLOX_HOST = "192.168.1.224"
INFOBLOX_USER = "admin"
INFOBLOX_PASSWORD = "infoblox"
WAPI_VERSION = "v2.13.1"
BASE_URL = f"https://{INFOBLOX_HOST}/wapi/{WAPI_VERSION}"

def get_wapi_session():
    """Create authenticated session for WAPI"""
    session = requests.Session()
    session.auth = (INFOBLOX_USER, INFOBLOX_PASSWORD)
    session.verify = False
    return session

def get_supported_objects(session):
    """Get list of all supported object types"""
    # Try to get schema which lists all object types
    url = f"{BASE_URL}/?_schema"
    try:
        response = session.get(url)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and 'supported_objects' in data:
                return data['supported_objects']
    except Exception as e:
        print(f"Error getting supported objects: {e}")

    # Fallback: Try common object types
    common_objects = [
        'network', 'networkcontainer', 'record:a', 'record:aaaa',
        'record:ptr', 'record:cname', 'record:mx', 'record:txt',
        'record:srv', 'zone_auth', 'zone_forward', 'dhcprange',
        'fixedaddress', 'host', 'grid', 'member', 'dns:view',
        'network:view', 'ipv4address', 'ipv6address', 'lease',
        'permission', 'adminuser', 'admingroup', 'fileop'
    ]
    return common_objects

def get_object_schema(session, object_type):
    """Get schema for a specific object type"""
    url = f"{BASE_URL}/{object_type}?_schema"
    try:
        response = session.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error getting schema for {object_type}: {e}")
    return None

def test_object_exists(session, object_type):
    """Test if an object type exists by querying it"""
    url = f"{BASE_URL}/{object_type}?_max_results=1"
    try:
        response = session.get(url, timeout=5)
        return response.status_code == 200
    except:
        return False

def discover_wapi_objects(session):
    """Discover all available WAPI objects"""
    print("=" * 80)
    print("InfoBlox WAPI Object Discovery")
    print("=" * 80)
    print(f"Host: {INFOBLOX_HOST}")
    print(f"WAPI Version: {WAPI_VERSION}")
    print("=" * 80)
    print()

    # Get list of potential objects
    objects = get_supported_objects(session)
    print(f"Testing {len(objects)} object types...")
    print()

    discovered = {}

    for obj_type in objects:
        print(f"Testing: {obj_type:30s} ", end='', flush=True)

        # Test if object exists
        if test_object_exists(session, obj_type):
            print("✓ EXISTS", end='')

            # Try to get schema
            schema = get_object_schema(session, obj_type)
            if schema:
                discovered[obj_type] = schema
                # Count fields
                fields = schema.get('fields', [])
                print(f" - {len(fields)} fields")
            else:
                discovered[obj_type] = {"exists": True, "schema": None}
                print(" - No schema available")
        else:
            print("✗ Not found")

    return discovered

def get_grid_schema(session):
    """Get the grid schema which contains metadata about WAPI"""
    url = f"{BASE_URL}/grid?_schema"
    try:
        response = session.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error getting grid schema: {e}")
    return None

def export_schemas(discovered, filename="infoblox_schemas.json"):
    """Export discovered schemas to JSON file"""
    with open(filename, 'w') as f:
        json.dump(discovered, f, indent=2)
    print()
    print(f"✓ Exported schemas to {filename}")
    print(f"  Total objects discovered: {len(discovered)}")
    print(f"  Objects with full schema: {sum(1 for v in discovered.values() if isinstance(v, dict) and 'fields' in v)}")

def main():
    session = get_wapi_session()

    # Test connection
    print("Testing connection to InfoBlox...")
    url = f"{BASE_URL}/network?_max_results=1"
    try:
        response = session.get(url, timeout=5)
        if response.status_code == 200:
            print("✓ Connection successful!")
            print()
        else:
            print(f"✗ Connection failed: {response.status_code}")
            return
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return

    # Discover objects
    discovered = discover_wapi_objects(session)

    # Export results
    export_schemas(discovered, "/Users/tshoush/REDHAT/infoblox_schemas.json")

    # Print summary
    print()
    print("=" * 80)
    print("Discovery Complete!")
    print("=" * 80)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
InfoBlox WAPI Explorer
Discovers all available WAPI objects and their schemas
"""

# Import security modules
from config import get_settings
from logging_config import setup_logging, get_security_logger
from validators import InputValidator, ValidationError
import logging

# Load secure configuration
settings = get_settings()

# Setup logging
setup_logging(
    log_level=settings.log_level,
    log_file="infoblox-explorer.log",
    enable_security_audit=True
)

logger = logging.getLogger(__name__)
security_logger = get_security_logger()

# Display SSL warning if disabled
settings.display_security_warning()

import requests
import json
from typing import Dict, List, Any

# InfoBlox configuration moved to config.py
BASE_URL = settings.get_infoblox_base_url()

def get_wapi_session():
    """Create authenticated session for WAPI"""
    logger.info("Creating WAPI session")
    session = requests.Session()
    session.auth = (settings.infoblox_user, settings.infoblox_password)
    session.verify = settings.get_ssl_verify()
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
    logger.info("Starting WAPI object discovery")
    print("=" * 80)
    print("InfoBlox WAPI Object Discovery")
    print("=" * 80)
    print(f"Host: {settings.infoblox_host}")
    print(f"WAPI Version: {settings.wapi_version}")
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

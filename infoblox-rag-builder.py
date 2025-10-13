#!/usr/bin/env python3
"""
InfoBlox RAG Knowledge Base Builder
Creates a vector database from InfoBlox WAPI schemas and documentation
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
    log_file="infoblox-rag-builder.log",
    enable_security_audit=True
)

logger = logging.getLogger(__name__)
security_logger = get_security_logger()

# Display SSL warning if disabled
settings.display_security_warning()

import json
import os
import sys
from typing import List, Dict, Any
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("ChromaDB not available. Install with: pip install chromadb")

try:
    import requests
    from bs4 import BeautifulSoup
    WEB_SCRAPING_AVAILABLE = True
except ImportError:
    WEB_SCRAPING_AVAILABLE = False

# Configuration moved to config.py

# RAG Configuration
RAG_DB_PATH = os.path.expanduser("~/.infoblox-rag")
SCHEMAS_FILE = os.path.expanduser("~/infoblox_schemas.json")
COLLECTION_NAME = "infoblox_knowledge"


class InfoBloxRAGBuilder:
    """Builds RAG knowledge base from InfoBlox WAPI schemas and documentation"""

    def __init__(self):
        if not CHROMADB_AVAILABLE:
            logger.error("ChromaDB is required but not available")
            raise ImportError("ChromaDB is required. Install with: pip install chromadb")

        logger.info("Initializing InfoBloxRAGBuilder")

        # Initialize ChromaDB
        os.makedirs(RAG_DB_PATH, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=RAG_DB_PATH,
            settings=Settings(anonymized_telemetry=False)
        )

        # Create or get collection
        try:
            self.collection = self.client.get_collection(name=COLLECTION_NAME)
            logger.info(f"Loaded existing collection: {COLLECTION_NAME}")
            print(f"✓ Loaded existing collection: {COLLECTION_NAME}")
        except:
            self.collection = self.client.create_collection(
                name=COLLECTION_NAME,
                metadata={"description": "InfoBlox WAPI knowledge base"}
            )
            logger.info(f"Created new collection: {COLLECTION_NAME}")
            print(f"✓ Created new collection: {COLLECTION_NAME}")

        self.documents = []
        self.metadatas = []
        self.ids = []

    def load_schemas(self, schemas_file: str):
        """Load InfoBlox WAPI schemas"""
        print(f"\nLoading schemas from {schemas_file}...")

        if not os.path.exists(schemas_file):
            print(f"✗ Schemas file not found: {schemas_file}")
            return

        with open(schemas_file, 'r') as f:
            schemas = json.load(f)

        print(f"✓ Loaded {len(schemas)} object types")

        # Process each schema
        for object_type, schema in schemas.items():
            self._process_schema(object_type, schema)

        print(f"✓ Processed {len(self.documents)} documents from schemas")

    def _process_schema(self, object_type: str, schema: Dict):
        """Process a single schema into RAG documents"""

        # 1. Object overview document
        overview_doc = f"""
        InfoBlox Object Type: {object_type}

        Description: {object_type} is a WAPI object type that represents {self._infer_description(object_type)}.

        Available operations:
        - GET: List and retrieve {object_type} objects
        - POST: Create new {object_type} objects
        - PUT: Update existing {object_type} objects
        - DELETE: Delete {object_type} objects

        API Endpoint: https://<infoblox-host>/wapi/{settings.wapi_version}/{object_type}
        """

        self.documents.append(overview_doc)
        self.metadatas.append({
            "type": "object_overview",
            "object_type": object_type,
            "category": self._categorize_object(object_type)
        })
        self.ids.append(f"obj_{object_type}_overview")

        # 2. Fields documentation
        fields = schema.get('fields', [])
        if fields:
            for field in fields[:20]:  # Limit to avoid too many docs
                if isinstance(field, dict):
                    field_doc = self._create_field_document(object_type, field)
                    if field_doc:
                        self.documents.append(field_doc)
                        self.metadatas.append({
                            "type": "field",
                            "object_type": object_type,
                            "field_name": field.get('name', 'unknown'),
                            "searchable": field.get('searchable_by', False)
                        })
                        self.ids.append(f"obj_{object_type}_field_{field.get('name', 'unknown')}")

        # 3. Common use cases
        use_cases = self._generate_use_cases(object_type)
        if use_cases:
            self.documents.append(use_cases)
            self.metadatas.append({
                "type": "use_cases",
                "object_type": object_type,
                "category": self._categorize_object(object_type)
            })
            self.ids.append(f"obj_{object_type}_usecases")

    def _create_field_document(self, object_type: str, field: Dict) -> str:
        """Create documentation for a field"""
        name = field.get('name', 'unknown')
        field_type = field.get('type', ['unknown'])
        if isinstance(field_type, list):
            field_type = field_type[0] if field_type else 'unknown'

        searchable = "searchable" if field.get('searchable_by', False) else "not searchable"
        required = "required" if field.get('required', False) else "optional"

        doc = f"""
        Field: {name} (in {object_type})

        Type: {field_type}
        Status: {required}, {searchable}

        Description: The {name} field in {object_type} objects is used to {self._infer_field_purpose(name, object_type)}.

        Usage in queries:
        - Can be used in search filters if searchable
        - Can be returned in results with _return_fields={name}
        - Can be modified in PUT requests if not read-only

        Example:
        GET /wapi/{settings.wapi_version}/{object_type}?{name}=<value>&_return_fields={name}
        """

        return doc

    def _generate_use_cases(self, object_type: str) -> str:
        """Generate common use cases for an object type"""
        category = self._categorize_object(object_type)

        use_cases_map = {
            "network": f"""
            Common use cases for {object_type}:

            1. List all networks:
               GET /wapi/{settings.wapi_version}/{object_type}?_return_fields=network,comment

            2. Search for specific network:
               GET /wapi/{settings.wapi_version}/{object_type}?network=10.0.0.0/24

            3. Create new network:
               POST /wapi/{settings.wapi_version}/{object_type}
               {{"network": "10.50.0.0/24", "comment": "New network"}}

            4. Check network utilization:
               GET /wapi/{settings.wapi_version}/{object_type}?_return_fields=network,utilization

            5. Find networks with DHCP enabled:
               GET /wapi/{settings.wapi_version}/{object_type}?_return_fields=network,members
            """,

            "dns": f"""
            Common use cases for {object_type}:

            1. List DNS records:
               GET /wapi/{settings.wapi_version}/{object_type}?_return_fields=name,ipv4addr

            2. Search by hostname:
               GET /wapi/{settings.wapi_version}/{object_type}?name~=server

            3. Create DNS record:
               POST /wapi/{settings.wapi_version}/{object_type}
               {{"name": "server1.example.com", "ipv4addr": "10.0.0.50"}}

            4. Find all records in zone:
               GET /wapi/{settings.wapi_version}/{object_type}?zone=example.com
            """,

            "dhcp": f"""
            Common use cases for {object_type}:

            1. List DHCP objects:
               GET /wapi/{settings.wapi_version}/{object_type}?_return_fields=address,hardware

            2. Find by MAC address:
               GET /wapi/{settings.wapi_version}/{object_type}?hardware=00:11:22:33:44:55

            3. Create DHCP reservation:
               POST /wapi/{settings.wapi_version}/{object_type}
               {{"ipv4addr": "10.0.0.100", "mac": "00:11:22:33:44:55"}}
            """,

            "infrastructure": f"""
            Common use cases for {object_type}:

            1. View configuration:
               GET /wapi/{settings.wapi_version}/{object_type}

            2. Update settings:
               PUT /wapi/{settings.wapi_version}/{object_type}/<ref>
               {{"setting": "value"}}
            """,

            "other": f"""
            Common operations for {object_type}:

            1. List objects:
               GET /wapi/{settings.wapi_version}/{object_type}

            2. Get specific object:
               GET /wapi/{settings.wapi_version}/{object_type}/<ref>

            3. Create object:
               POST /wapi/{settings.wapi_version}/{object_type}
               {{"required_field": "value"}}
            """
        }

        return use_cases_map.get(category, use_cases_map["other"])

    def _infer_description(self, object_type: str) -> str:
        """Infer description from object type name"""
        descriptions = {
            "network": "IPv4 or IPv6 network objects",
            "networkcontainer": "network container objects for organizing IP space",
            "record:a": "DNS A records mapping hostnames to IPv4 addresses",
            "record:aaaa": "DNS AAAA records mapping hostnames to IPv6 addresses",
            "record:ptr": "DNS PTR records for reverse DNS lookups",
            "record:cname": "DNS CNAME records for aliasing",
            "record:mx": "DNS MX records for mail servers",
            "zone_auth": "authoritative DNS zones",
            "range": "DHCP ranges for dynamic IP allocation",
            "fixedaddress": "DHCP reservations with fixed IP addresses",
            "lease": "active DHCP leases",
            "grid": "the InfoBlox grid configuration",
            "member": "InfoBlox grid members",
            "view": "DNS views for split DNS",
        }

        return descriptions.get(object_type, f"{object_type} objects in the InfoBlox system")

    def _infer_field_purpose(self, field_name: str, object_type: str) -> str:
        """Infer field purpose from name"""
        purposes = {
            "network": "specify the IP network in CIDR format",
            "ipv4addr": "specify the IPv4 address",
            "ipv6addr": "specify the IPv6 address",
            "name": "specify the object name or hostname",
            "comment": "add descriptive comments or notes",
            "hardware": "specify the MAC address",
            "mac": "specify the MAC address",
            "_ref": "uniquely identify the object",
            "zone": "specify the DNS zone",
            "view": "specify the DNS view",
        }

        return purposes.get(field_name, f"configure the {field_name} property")

    def _categorize_object(self, object_type: str) -> str:
        """Categorize object type"""
        if any(x in object_type for x in ["network", "ipv4", "ipv6", "container"]):
            return "network"
        elif any(x in object_type for x in ["record:", "zone_", "dns", "view"]):
            return "dns"
        elif any(x in object_type for x in ["range", "lease", "fixedaddress", "dhcp"]):
            return "dhcp"
        elif any(x in object_type for x in ["grid", "member", "admin", "permission"]):
            return "infrastructure"
        else:
            return "other"

    def scrape_wapi_docs(self):
        """Scrape InfoBlox WAPI documentation if available"""
        if not WEB_SCRAPING_AVAILABLE:
            logger.warning("Web scraping not available (missing requests/beautifulsoup4)")
            print("\n✗ Web scraping not available (missing requests/beautifulsoup4)")
            return

        logger.info("Attempting to scrape WAPI documentation")
        print("\nAttempting to scrape WAPI documentation...")

        # Try to access wapidoc
        doc_url = f"https://{settings.infoblox_host}/wapidoc/"

        try:
            response = requests.get(
                doc_url,
                auth=(settings.infoblox_user, settings.infoblox_password),
                verify=settings.get_ssl_verify(),
                timeout=10
            )

            if response.status_code == 200:
                logger.info(f"Found WAPI documentation at {doc_url}")
                print(f"✓ Found WAPI documentation at {doc_url}")
                # Parse and extract documentation
                # This is a placeholder - actual implementation depends on InfoBlox version
                print("  (Documentation scraping not yet implemented)")
            else:
                logger.warning(f"Cannot access documentation: HTTP {response.status_code}")
                print(f"✗ Cannot access documentation: HTTP {response.status_code}")

        except Exception as e:
            logger.error(f"Cannot access documentation: {e}", exc_info=True)
            print(f"✗ Cannot access documentation: {e}")

    def discover_extensible_attributes(self):
        """Discover extensible attributes (EAs) from InfoBlox"""
        print("\nDiscovering extensible attributes...")
        logger.info("Discovering extensible attributes from InfoBlox")

        try:
            import requests

            url = f"https://{settings.infoblox_host}/wapi/{settings.wapi_version}/extensibleattributedef"
            logger.debug(f"Fetching EAs from: {url}")
            response = requests.get(
                url,
                auth=(settings.infoblox_user, settings.infoblox_password),
                verify=settings.get_ssl_verify(),
                params={"_return_fields": "name,comment,type,list_values"},
                timeout=30
            )

            if response.status_code == 200:
                eas = response.json()
                logger.info(f"Discovered {len(eas)} extensible attributes")
                print(f"✓ Discovered {len(eas)} extensible attributes")

                # Add EA documentation
                for ea in eas:
                    ea_name = ea.get('name', 'unknown')
                    ea_type = ea.get('type', 'STRING')
                    ea_comment = ea.get('comment', '')
                    list_values = ea.get('list_values', [])

                    ea_doc = f"""
                    Extensible Attribute: {ea_name}

                    Type: {ea_type}
                    Description: {ea_comment if ea_comment else f'Custom extensible attribute {ea_name}'}

                    How to query by this EA:
                    - Use *{ea_name} in search filters
                    - Example: *{ea_name}=value
                    - Use _return_fields+ to include EAs in results

                    Query example:
                    GET /wapi/{settings.wapi_version}/network?*{ea_name}=<value>&_return_fields+=extattrs

                    Example natural language queries:
                    - "List all networks where {ea_name} is <value>"
                    - "Show networks with {ea_name} equal to <value>"
                    - "Find networks where {ea_name} is <value>"

                    MCP Tool to use: infoblox_search_network
                    Parameters: {{"filters": {{"*{ea_name}": "<value>"}}, "return_fields": "network,extattrs"}}
                    """

                    if list_values:
                        ea_doc += f"\n\nValid values: {', '.join(list_values)}"

                    self.documents.append(ea_doc)
                    self.metadatas.append({
                        "type": "extensible_attribute",
                        "ea_name": ea_name,
                        "ea_type": ea_type,
                        "category": "extensible_attributes"
                    })
                    self.ids.append(f"ea_{ea_name}")

                return len(eas)
            else:
                logger.warning(f"Could not discover EAs: HTTP {response.status_code}")
                print(f"✗ Could not discover EAs: HTTP {response.status_code}")
                return 0

        except Exception as e:
            logger.error(f"Error discovering EAs: {e}", exc_info=True)
            print(f"✗ Error discovering EAs: {e}")
            return 0

    def add_common_knowledge(self):
        """Add common InfoBlox knowledge and best practices"""
        print("\nAdding common InfoBlox knowledge...")

        common_docs = [
            {
                "content": """
                InfoBlox WAPI Query Parameters:

                - _max_results: Limit number of results (default: 1000)
                - _return_fields: Specify which fields to return (comma-separated)
                - _return_fields+: Add fields to default return set
                - _paging: Enable pagination (1 for enable)
                - _return_as_object: Return results as object (1 for enable)
                - _proxy_search: Search across grid members

                Example:
                GET /wapi/v2.13.1/network?_max_results=100&_return_fields=network,comment
                """,
                "metadata": {"type": "api_parameters", "category": "query"},
                "id": "wapi_query_params"
            },
            {
                "content": """
                InfoBlox Extensible Attributes (EA) Query Patterns:

                Extensible attributes are custom fields added to InfoBlox objects.
                They are prefixed with * in queries.

                Query by EA:
                GET /wapi/v2.13.1/<object>?*<EA_NAME>=<value>

                Example: Find networks where MARSHA='HDQTR2':
                GET /wapi/v2.13.1/network?*MARSHA=HDQTR2&_return_fields+=extattrs

                Return EAs in results:
                - Use _return_fields+=extattrs to include all EAs
                - Use _return_fields+=extattrs to add to default fields
                - EAs will be in the 'extattrs' field of the response

                Common EA query patterns:
                1. Exact match: *EA_NAME=value
                2. Regex match: *EA_NAME~=pattern
                3. Not equal: *EA_NAME!=value
                4. Multiple EAs: *EA1=val1&*EA2=val2

                MCP Tool Selection for EA Queries:
                - For networks: use infoblox_search_network tool
                - For DNS records: use infoblox_search_record_a (or appropriate record type)
                - For ranges: use infoblox_search_range tool
                - Always include filters parameter with EA filter
                - Always include extattrs in return_fields

                Natural language examples:
                - "networks where MARSHA='HDQTR2'" → infoblox_search_network with filters={"*MARSHA": "HDQTR2"}
                - "find all A records with Site='NYC'" → infoblox_search_record_a with filters={"*Site": "NYC"}
                - "show ranges where Location='Building A'" → infoblox_search_range with filters={"*Location": "Building A"}
                """,
                "metadata": {"type": "ea_query_patterns", "category": "query"},
                "id": "ea_query_patterns"
            },
            {
                "content": """
                MCP Tool Selection Intelligence:

                When user asks for data retrieval, select the appropriate tool:

                1. NETWORK QUERIES:
                   - "list networks" → infoblox_list_network
                   - "find network 10.0.0.0/24" → infoblox_search_network with filters
                   - "networks where <EA>=<value>" → infoblox_search_network with filters={"*<EA>": "<value>"}
                   - "create network" → infoblox_create_network

                2. DNS RECORD QUERIES:
                   - "list A records" → infoblox_list_record_a
                   - "find host server1.example.com" → infoblox_search_record_host
                   - "A records where <EA>=<value>" → infoblox_search_record_a with filters
                   - "create DNS record" → infoblox_create_record_a or infoblox_create_record_host

                3. DHCP QUERIES:
                   - "list DHCP ranges" → infoblox_list_range
                   - "find fixed address" → infoblox_search_fixedaddress
                   - "ranges where <EA>=<value>" → infoblox_search_range with filters
                   - "create fixed address" → infoblox_create_fixedaddress

                4. GENERIC QUERIES:
                   - For any object type: use infoblox_search_<object_type>
                   - Always check if object type exists first

                PARAMETER CONSTRUCTION:
                - Always use filters parameter for search conditions
                - Use *<EA_NAME> format for extensible attributes
                - Include extattrs in return_fields when querying by EA
                - Use max_results to limit large queries

                Example tool calls:
                User: "list all networks where MARSHA='HDQTR2'"
                Tool: infoblox_search_network
                Parameters: {
                    "filters": {"*MARSHA": "HDQTR2"},
                    "return_fields": "network,comment,extattrs",
                    "max_results": 100
                }
                """,
                "metadata": {"type": "tool_selection", "category": "mcp"},
                "id": "tool_selection_guide"
            },
            {
                "content": """
                Multi-Tool Chain Examples:

                Some queries require multiple tool calls in sequence:

                EXAMPLE 1: Find and update network
                User: "Find network 10.0.0.0/24 and update its comment"

                Step 1: Search for network
                Tool: infoblox_search_network
                Parameters: {"filters": {"network": "10.0.0.0/24"}, "return_fields": "_ref,network"}
                Result: Get _ref like "network/ZG5zLm5ldHdvcmskMTAuMC4wLjAvMjQvMA:10.0.0.0/24/default"

                Step 2: Update network
                Tool: infoblox_update_network
                Parameters: {"ref": "<_ref from step 1>", "data": {"comment": "New comment"}}

                EXAMPLE 2: Check network, then create DNS record
                User: "Find network for IP 10.0.0.50 and create A record"

                Step 1: Find network containing IP
                Tool: infoblox_search_network
                Parameters: {"filters": {"network~": "10.0.0"}, "return_fields": "network"}

                Step 2: Create A record
                Tool: infoblox_create_record_a
                Parameters: {"data": {"name": "server1.example.com", "ipv4addr": "10.0.0.50"}}

                EXAMPLE 3: Complex EA query with multiple filters
                User: "Find networks where MARSHA='HDQTR2' AND Site='NYC'"

                Single tool with multiple filters:
                Tool: infoblox_search_network
                Parameters: {
                    "filters": {"*MARSHA": "HDQTR2", "*Site": "NYC"},
                    "return_fields": "network,comment,extattrs"
                }

                EXAMPLE 4: Get object details and related objects
                User: "Show me network 10.0.0.0/24 and all its DNS records"

                Step 1: Get network details
                Tool: infoblox_search_network
                Parameters: {"filters": {"network": "10.0.0.0/24"}, "return_fields": "network,comment,extattrs"}

                Step 2: Search for A records in that network
                Tool: infoblox_search_record_a
                Parameters: {"filters": {"ipv4addr~": "10.0.0"}, "return_fields": "name,ipv4addr"}
                """,
                "metadata": {"type": "multi_tool_chains", "category": "mcp"},
                "id": "multi_tool_examples"
            },
            {
                "content": """
                InfoBlox Search Modifiers:

                - Exact match: field=value
                - Regex match: field~=pattern
                - Less than: field<value
                - Greater than: field>value
                - Not equal: field!=value
                - Contains: field:=substring

                Example:
                GET /wapi/v2.13.1/record:a?name~=^server
                (finds records starting with 'server')
                """,
                "metadata": {"type": "search_modifiers", "category": "query"},
                "id": "wapi_search_modifiers"
            },
            {
                "content": """
                InfoBlox Object References (_ref):

                Every object has a unique _ref field that identifies it.
                Use _ref for GET, PUT, DELETE operations on specific objects.

                Format: <object_type>/<base64_encoded_id>:<key_fields>

                Example:
                network/ZG5zLm5ldHdvcmskMTAuMC4wLjAvMjQvMA:10.0.0.0/24/default

                To get an object by ref:
                GET /wapi/v2.13.1/<ref>

                To update:
                PUT /wapi/v2.13.1/<ref>
                {"comment": "Updated"}

                To delete:
                DELETE /wapi/v2.13.1/<ref>
                """,
                "metadata": {"type": "object_references", "category": "concepts"},
                "id": "wapi_object_refs"
            },
            {
                "content": """
                InfoBlox Network Management Best Practices:

                1. Always use _max_results to limit large queries
                2. Use _return_fields to get only needed data
                3. Use search modifiers for efficient filtering
                4. Check network utilization before creating new objects
                5. Use comments to document networks and changes
                6. Verify references before deleting objects
                7. Use network containers for hierarchical organization

                Network Utilization Check:
                GET /wapi/v2.13.1/network?_return_fields=network,utilization

                Create network in container:
                POST /wapi/v2.13.1/network
                {"network": "10.0.0.0/24", "network_container": "10.0.0.0/16"}
                """,
                "metadata": {"type": "best_practices", "category": "network"},
                "id": "network_best_practices"
            },
            {
                "content": """
                InfoBlox DNS Management Best Practices:

                1. Always check if record exists before creating
                2. Use views for split DNS configurations
                3. Set appropriate TTL values
                4. Use CNAME for aliasing, not multiple A records
                5. Keep PTR records in sync with A records
                6. Use record templates for consistency

                Check for existing record:
                GET /wapi/v2.13.1/record:a?name=server1.example.com

                Create A and PTR together:
                POST /wapi/v2.13.1/record:host
                {
                    "name": "server1.example.com",
                    "ipv4addrs": [{"ipv4addr": "10.0.0.50"}]
                }
                """,
                "metadata": {"type": "best_practices", "category": "dns"},
                "id": "dns_best_practices"
            },
            {
                "content": """
                InfoBlox DHCP Management Best Practices:

                1. Don't overlap DHCP ranges with fixed addresses
                2. Reserve IPs for servers and network devices
                3. Use meaningful names in fixed address comments
                4. Monitor lease utilization
                5. Set appropriate lease times
                6. Use DHCP failover for high availability

                Check range utilization:
                GET /wapi/v2.13.1/range?_return_fields=start_addr,end_addr,utilization

                Create fixed address with reservation:
                POST /wapi/v2.13.1/fixedaddress
                {
                    "ipv4addr": "10.0.0.100",
                    "mac": "00:11:22:33:44:55",
                    "name": "server1",
                    "comment": "Production web server"
                }
                """,
                "metadata": {"type": "best_practices", "category": "dhcp"},
                "id": "dhcp_best_practices"
            },
            {
                "content": """
                Common InfoBlox Error Messages and Solutions:

                1. "AdmConProtoError: Unknown object type"
                   - Object type doesn't exist or is misspelled
                   - Check available objects with schema query

                2. "Permission denied"
                   - User lacks necessary permissions
                   - Check adminuser permissions

                3. "Object not found"
                   - Reference is invalid or object was deleted
                   - Query again to get current references

                4. "Concurrent update conflict"
                   - Object was modified by another user
                   - Retry the operation

                5. "Network overlaps with existing network"
                   - IP space already allocated
                   - Check existing networks first
                """,
                "metadata": {"type": "troubleshooting", "category": "errors"},
                "id": "common_errors"
            }
        ]

        for doc in common_docs:
            self.documents.append(doc["content"])
            self.metadatas.append(doc["metadata"])
            self.ids.append(doc["id"])

        print(f"✓ Added {len(common_docs)} common knowledge documents")

    def load_ea_examples(self):
        """Load EA query examples from markdown file"""
        print("\nLoading EA query examples...")

        ea_examples_file = os.path.expanduser("~/ea-query-examples.md")
        if os.path.exists(ea_examples_file):
            with open(ea_examples_file, 'r') as f:
                content = f.read()

            # Split into sections for better retrieval
            sections = content.split('## ')
            for section in sections[1:]:  # Skip the title
                lines = section.split('\n', 1)
                if len(lines) == 2:
                    section_title = lines[0].strip()
                    section_content = lines[1].strip()

                    self.documents.append(f"## {section_title}\n\n{section_content}")
                    self.metadatas.append({
                        "type": "ea_examples",
                        "section": section_title,
                        "category": "extensible_attributes"
                    })
                    self.ids.append(f"ea_example_{section_title.replace(' ', '_').lower()}")

            print(f"✓ Loaded {len(sections)-1} EA example sections")
            return len(sections) - 1
        else:
            print(f"✗ EA examples file not found: {ea_examples_file}")
            return 0

    def build_rag_database(self):
        """Build the RAG database"""
        logger.info("Starting RAG database build")
        print("\n" + "=" * 80)
        print("Building InfoBlox RAG Knowledge Base")
        print("=" * 80)

        # Load schemas
        self.load_schemas(SCHEMAS_FILE)

        # Discover extensible attributes
        ea_count = self.discover_extensible_attributes()

        # Load EA query examples
        self.load_ea_examples()

        # Add common knowledge
        self.add_common_knowledge()

        # Scrape documentation if available
        self.scrape_wapi_docs()

        # Add to ChromaDB
        print(f"\nAdding {len(self.documents)} documents to vector database...")

        if len(self.documents) > 0:
            # Add in batches to avoid memory issues
            batch_size = 100
            for i in range(0, len(self.documents), batch_size):
                end_idx = min(i + batch_size, len(self.documents))
                self.collection.add(
                    documents=self.documents[i:end_idx],
                    metadatas=self.metadatas[i:end_idx],
                    ids=self.ids[i:end_idx]
                )
                print(f"  Added batch {i//batch_size + 1} ({end_idx}/{len(self.documents)})")

            logger.info(f"RAG database built successfully - {len(self.documents)} documents")
            print(f"✓ RAG database built successfully")
            print(f"  Total documents: {len(self.documents)}")
            print(f"  Database location: {RAG_DB_PATH}")
        else:
            logger.warning("No documents to add to RAG database")
            print("✗ No documents to add")

    def test_search(self, query: str, n_results: int = 5):
        """Test the RAG database with a query"""
        print(f"\nTest Query: '{query}'")
        print("-" * 80)

        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

        if results['documents'] and len(results['documents'][0]) > 0:
            print(f"Found {len(results['documents'][0])} relevant documents:\n")

            for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                print(f"{i+1}. Type: {metadata.get('type', 'unknown')}")
                print(f"   Object: {metadata.get('object_type', 'N/A')}")
                print(f"   Preview: {doc[:150]}...")
                print()
        else:
            print("No results found")


def main():
    logger.info("InfoBlox RAG Knowledge Base Builder started")
    print("InfoBlox RAG Knowledge Base Builder")
    print("=" * 80)

    if not CHROMADB_AVAILABLE:
        logger.error("ChromaDB not installed")
        print("\n✗ ChromaDB not installed")
        print("  Install with: pip install chromadb")
        return 1

    try:
        builder = InfoBloxRAGBuilder()
        builder.build_rag_database()

        # Test the database
        print("\n" + "=" * 80)
        print("Testing RAG Database")
        print("=" * 80)

        test_queries = [
            "How do I create a new network?",
            "Show me how to search for DNS records",
            "What are DHCP best practices?",
            "How do I use object references?",
            "List all networks where MARSHA='HDQTR2'",
            "How do I query by extensible attributes?"
        ]

        for query in test_queries:
            builder.test_search(query, n_results=3)
            print()

        print("=" * 80)
        print("RAG Database Ready!")
        print("=" * 80)
        print(f"\nDatabase location: {RAG_DB_PATH}")
        print(f"Total documents: {len(builder.documents)}")
        print("\nThe RAG database can now be used with the DDI Assistant")
        print("for enhanced InfoBlox understanding and better responses.")

        logger.info("RAG database builder completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Error building RAG database: {e}", exc_info=True)
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

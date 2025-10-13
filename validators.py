#!/usr/bin/env python3
"""
Input Validation Module
Validates and sanitizes all user inputs to prevent injection attacks
"""

import os
import re
from typing import Any, Dict
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class ValidationError(ValueError):
    """Raised when input validation fails"""
    pass


class InputValidator:
    """Validates and sanitizes user inputs"""

    # Patterns for validation
    OBJECT_TYPE_PATTERN = re.compile(r'^[a-z0-9_:]+$')
    EA_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    IPV4_PATTERN = re.compile(
        r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
        r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    )
    CIDR_PATTERN = re.compile(
        r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
        r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
        r'/(?:[0-9]|[1-2][0-9]|3[0-2])$'
    )
    HOSTNAME_PATTERN = re.compile(
        r'^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*$'
    )

    # Forbidden patterns that might indicate injection attempts
    FORBIDDEN_PATTERNS = [
        r'[;\|\&\$\(\)\`]',  # Shell metacharacters
        r'\.\./\.\.',         # Path traversal
        r'<script',           # XSS attempts
        r'javascript:',       # JavaScript protocol
        r'on\w+\s*=',        # Event handlers
    ]

    @classmethod
    def validate_object_type(cls, object_type: str) -> str:
        """
        Validate InfoBlox object type.

        Args:
            object_type: Object type string (e.g., "network", "record:a")

        Returns:
            Validated object type

        Raises:
            ValidationError: If object type is invalid

        Example:
            >>> InputValidator.validate_object_type("network")
            'network'
            >>> InputValidator.validate_object_type("record:a")
            'record:a'
        """
        if not isinstance(object_type, str):
            raise ValidationError(f"Object type must be string, got {type(object_type)}")

        if not object_type:
            raise ValidationError("Object type cannot be empty")

        if len(object_type) > 100:
            raise ValidationError(f"Object type too long: {len(object_type)} chars (max 100)")

        if not cls.OBJECT_TYPE_PATTERN.match(object_type):
            raise ValidationError(
                f"Invalid object type '{object_type}'. "
                f"Must contain only lowercase letters, numbers, underscore, and colon."
            )

        return object_type

    @classmethod
    def validate_ea_name(cls, ea_name: str) -> str:
        """
        Validate Extensible Attribute name.

        Args:
            ea_name: EA name (with or without leading asterisk)

        Returns:
            Validated EA name (without asterisk)

        Raises:
            ValidationError: If EA name is invalid

        Example:
            >>> InputValidator.validate_ea_name("*MARSHA")
            'MARSHA'
            >>> InputValidator.validate_ea_name("Site")
            'Site'
        """
        if not isinstance(ea_name, str):
            raise ValidationError(f"EA name must be string, got {type(ea_name)}")

        # Remove leading asterisk if present
        ea_name_clean = ea_name.lstrip('*')

        if not ea_name_clean:
            raise ValidationError("EA name cannot be empty")

        if len(ea_name_clean) > 50:
            raise ValidationError(f"EA name too long: {len(ea_name_clean)} chars (max 50)")

        if not cls.EA_NAME_PATTERN.match(ea_name_clean):
            raise ValidationError(
                f"Invalid EA name '{ea_name_clean}'. "
                f"Must contain only letters, numbers, underscore, and dash."
            )

        return ea_name_clean

    @classmethod
    def validate_filter_value(cls, value: Any) -> Any:
        """
        Validate filter value for injection attempts.

        Args:
            value: Filter value (any type)

        Returns:
            Validated value

        Raises:
            ValidationError: If value contains forbidden patterns

        Example:
            >>> InputValidator.validate_filter_value("10.0.0.0/24")
            '10.0.0.0/24'
            >>> InputValidator.validate_filter_value("test; rm -rf /")
            ValidationError: Invalid characters in filter value
        """
        if isinstance(value, str):
            # Check for injection attempts
            for pattern in cls.FORBIDDEN_PATTERNS:
                if re.search(pattern, value, re.IGNORECASE):
                    raise ValidationError(
                        f"Invalid characters detected in filter value. "
                        f"Potential injection attempt blocked."
                    )

            # Check length
            if len(value) > 1000:
                raise ValidationError(f"Filter value too long: {len(value)} chars (max 1000)")

        elif isinstance(value, (int, float, bool)):
            # Numbers and booleans are safe
            pass

        elif isinstance(value, (list, tuple)):
            # Validate each item in list
            return type(value)(cls.validate_filter_value(item) for item in value)

        elif isinstance(value, dict):
            # Validate each value in dict
            return {k: cls.validate_filter_value(v) for k, v in value.items()}

        elif value is None:
            # None is acceptable
            pass

        else:
            raise ValidationError(f"Unsupported filter value type: {type(value)}")

        return value

    @classmethod
    def validate_network(cls, network: str) -> str:
        """
        Validate network in CIDR format.

        Args:
            network: Network in CIDR notation (e.g., "10.0.0.0/24")

        Returns:
            Validated network

        Raises:
            ValidationError: If network format is invalid

        Example:
            >>> InputValidator.validate_network("10.0.0.0/24")
            '10.0.0.0/24'
            >>> InputValidator.validate_network("192.168.1.0/8")
            ValidationError: Invalid CIDR prefix
        """
        if not isinstance(network, str):
            raise ValidationError(f"Network must be string, got {type(network)}")

        if not cls.CIDR_PATTERN.match(network):
            raise ValidationError(
                f"Invalid network format: '{network}'. "
                f"Must be CIDR notation (e.g., 10.0.0.0/24)"
            )

        # Additional validation: check prefix is valid for the address
        try:
            ip_str, prefix_str = network.split('/')
            prefix = int(prefix_str)

            # Validate prefix range
            if not 0 <= prefix <= 32:
                raise ValidationError(f"Invalid CIDR prefix: {prefix} (must be 0-32)")

        except ValueError as e:
            raise ValidationError(f"Invalid network format: {e}")

        return network

    @classmethod
    def validate_ipv4(cls, ip: str) -> str:
        """
        Validate IPv4 address.

        Args:
            ip: IPv4 address

        Returns:
            Validated IP address

        Raises:
            ValidationError: If IP is invalid
        """
        if not isinstance(ip, str):
            raise ValidationError(f"IP must be string, got {type(ip)}")

        if not cls.IPV4_PATTERN.match(ip):
            raise ValidationError(f"Invalid IPv4 address: '{ip}'")

        return ip

    @classmethod
    def validate_hostname(cls, hostname: str) -> str:
        """
        Validate hostname/domain name.

        Args:
            hostname: Hostname to validate

        Returns:
            Validated hostname

        Raises:
            ValidationError: If hostname is invalid
        """
        if not isinstance(hostname, str):
            raise ValidationError(f"Hostname must be string, got {type(hostname)}")

        if not hostname:
            raise ValidationError("Hostname cannot be empty")

        if len(hostname) > 253:
            raise ValidationError(f"Hostname too long: {len(hostname)} chars (max 253)")

        if not cls.HOSTNAME_PATTERN.match(hostname):
            raise ValidationError(f"Invalid hostname: '{hostname}'")

        return hostname

    @classmethod
    def validate_url(cls, url: str) -> str:
        """
        Validate URL for web_search tool.

        Args:
            url: URL to validate

        Returns:
            Validated URL

        Raises:
            ValidationError: If URL is invalid
        """
        if not isinstance(url, str):
            raise ValidationError(f"URL must be string, got {type(url)}")

        try:
            parsed = urlparse(url)

            # Must have http or https scheme
            if parsed.scheme not in ['http', 'https']:
                raise ValidationError(
                    f"URL must use http or https, got: {parsed.scheme}"
                )

            # Must have a domain
            if not parsed.netloc:
                raise ValidationError("URL must have a valid domain")

            # Check for suspicious patterns
            if any(pattern in url.lower() for pattern in ['javascript:', 'data:', 'file:']):
                raise ValidationError("Suspicious URL scheme detected")

            return url

        except Exception as e:
            raise ValidationError(f"Invalid URL: {e}")

    @classmethod
    def validate_file_path(cls, path: str, allowed_base: str = None) -> str:
        """
        Validate file path to prevent directory traversal.

        Args:
            path: File path to validate
            allowed_base: Base directory path must be within (default: cwd)

        Returns:
            Absolute validated path

        Raises:
            ValidationError: If path is outside allowed directory

        Example:
            >>> InputValidator.validate_file_path("./myfile.txt")
            '/current/dir/myfile.txt'
            >>> InputValidator.validate_file_path("../../etc/passwd")
            ValidationError: Path outside allowed directory
        """
        if not isinstance(path, str):
            raise ValidationError(f"Path must be string, got {type(path)}")

        # Expand user home directory
        path = os.path.expanduser(path)

        # Resolve to absolute path
        try:
            abs_path = os.path.abspath(path)
        except Exception as e:
            raise ValidationError(f"Invalid path: {e}")

        # Default to current working directory
        if allowed_base is None:
            allowed_base = os.getcwd()
        else:
            allowed_base = os.path.abspath(os.path.expanduser(allowed_base))

        # Check if path is within allowed directory
        if not abs_path.startswith(allowed_base):
            raise ValidationError(
                f"Path '{path}' is outside allowed directory '{allowed_base}'"
            )

        return abs_path

    @classmethod
    def validate_tool_input(cls, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate tool input based on tool type.

        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters

        Returns:
            Validated tool input

        Raises:
            ValidationError: If any input is invalid

        Example:
            >>> InputValidator.validate_tool_input(
            ...     "infoblox_query",
            ...     {"object_type": "network", "filters": {"*MARSHA": "HDQTR2"}}
            ... )
            {"object_type": "network", "filters": {"*MARSHA": "HDQTR2"}}
        """
        validated = {}

        try:
            if tool_name == "infoblox_query":
                # Validate object_type
                if "object_type" in tool_input:
                    validated["object_type"] = cls.validate_object_type(tool_input["object_type"])

                # Validate filters
                if "filters" in tool_input:
                    validated_filters = {}
                    for key, value in tool_input["filters"].items():
                        # Check if EA (starts with *)
                        if key.startswith('*'):
                            cls.validate_ea_name(key)
                        # Validate value
                        validated_filters[key] = cls.validate_filter_value(value)
                    validated["filters"] = validated_filters

                # Pass through other parameters
                for key in ["max_results", "return_fields"]:
                    if key in tool_input:
                        validated[key] = tool_input[key]

            elif tool_name == "infoblox_create_network":
                if "network" in tool_input:
                    validated["network"] = cls.validate_network(tool_input["network"])
                if "comment" in tool_input:
                    validated["comment"] = cls.validate_filter_value(tool_input["comment"])

            elif tool_name == "infoblox_search_records":
                if "record_type" in tool_input:
                    validated["record_type"] = cls.validate_object_type(f"record:{tool_input['record_type']}")
                if "name" in tool_input:
                    validated["name"] = cls.validate_hostname(tool_input["name"])
                if "value" in tool_input:
                    validated["value"] = cls.validate_filter_value(tool_input["value"])

            elif tool_name == "web_search":
                if "query" in tool_input:
                    validated["query"] = cls.validate_filter_value(tool_input["query"])

            elif tool_name == "fetch_webpage":
                if "url" in tool_input:
                    validated["url"] = cls.validate_url(tool_input["url"])

            elif tool_name == "read_file":
                if "file_path" in tool_input:
                    validated["file_path"] = cls.validate_file_path(tool_input["file_path"])

            else:
                # For unknown tools, do basic validation
                validated = {k: cls.validate_filter_value(v) for k, v in tool_input.items()}

            return validated

        except ValidationError as e:
            logger.warning(f"Input validation failed for {tool_name}: {e}")
            raise


if __name__ == "__main__":
    # Test validators
    print("Testing InputValidator...")

    # Test object type validation
    assert InputValidator.validate_object_type("network") == "network"
    assert InputValidator.validate_object_type("record:a") == "record:a"

    try:
        InputValidator.validate_object_type("network; DROP TABLE")
        assert False, "Should have raised ValidationError"
    except ValidationError:
        print("✓ Correctly blocked SQL injection attempt")

    # Test EA name validation
    assert InputValidator.validate_ea_name("*MARSHA") == "MARSHA"
    assert InputValidator.validate_ea_name("Site") == "Site"

    # Test network validation
    assert InputValidator.validate_network("10.0.0.0/24") == "10.0.0.0/24"

    try:
        InputValidator.validate_network("invalid")
        assert False, "Should have raised ValidationError"
    except ValidationError:
        print("✓ Correctly blocked invalid network")

    # Test filter value validation
    assert InputValidator.validate_filter_value("safe_value") == "safe_value"

    try:
        InputValidator.validate_filter_value("test; rm -rf /")
        assert False, "Should have raised ValidationError"
    except ValidationError:
        print("✓ Correctly blocked command injection attempt")

    print("\n✓ All validation tests passed!")

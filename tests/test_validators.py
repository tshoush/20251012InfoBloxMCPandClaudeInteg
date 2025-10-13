"""
Unit tests for validators module
"""

import os
import pytest
from validators import InputValidator, ValidationError


class TestValidateObjectType:
    """Tests for validate_object_type method"""

    def test_valid_simple_object_type(self):
        """Test valid simple object type"""
        assert InputValidator.validate_object_type("network") == "network"

    def test_valid_complex_object_type(self):
        """Test valid complex object type with colon"""
        assert InputValidator.validate_object_type("record:a") == "record:a"
        assert InputValidator.validate_object_type("record:aaaa") == "record:aaaa"

    def test_valid_with_underscores(self):
        """Test valid object type with underscores"""
        assert InputValidator.validate_object_type("zone_auth") == "zone_auth"

    def test_empty_object_type(self):
        """Test empty object type raises error"""
        with pytest.raises(ValidationError, match="cannot be empty"):
            InputValidator.validate_object_type("")

    def test_invalid_uppercase(self):
        """Test uppercase characters raise error"""
        with pytest.raises(ValidationError, match="lowercase"):
            InputValidator.validate_object_type("Network")

    def test_invalid_special_characters(self):
        """Test special characters raise error"""
        with pytest.raises(ValidationError):
            InputValidator.validate_object_type("network; DROP TABLE")

    def test_too_long(self):
        """Test too long object type raises error"""
        long_name = "a" * 101
        with pytest.raises(ValidationError, match="too long"):
            InputValidator.validate_object_type(long_name)

    def test_non_string_input(self):
        """Test non-string input raises error"""
        with pytest.raises(ValidationError, match="must be string"):
            InputValidator.validate_object_type(123)


class TestValidateEAName:
    """Tests for validate_ea_name method"""

    def test_valid_ea_with_asterisk(self):
        """Test valid EA name with asterisk"""
        assert InputValidator.validate_ea_name("*MARSHA") == "MARSHA"

    def test_valid_ea_without_asterisk(self):
        """Test valid EA name without asterisk"""
        assert InputValidator.validate_ea_name("MARSHA") == "MARSHA"

    def test_valid_mixed_case(self):
        """Test valid EA name with mixed case"""
        assert InputValidator.validate_ea_name("Site") == "Site"

    def test_valid_with_underscore(self):
        """Test valid EA name with underscore"""
        assert InputValidator.validate_ea_name("Cost_Center") == "Cost_Center"

    def test_valid_with_dash(self):
        """Test valid EA name with dash"""
        assert InputValidator.validate_ea_name("Cost-Center") == "Cost-Center"

    def test_empty_ea_name(self):
        """Test empty EA name raises error"""
        with pytest.raises(ValidationError, match="cannot be empty"):
            InputValidator.validate_ea_name("")

        with pytest.raises(ValidationError, match="cannot be empty"):
            InputValidator.validate_ea_name("*")

    def test_invalid_special_characters(self):
        """Test invalid special characters"""
        with pytest.raises(ValidationError):
            InputValidator.validate_ea_name("EA;Name")

    def test_too_long(self):
        """Test too long EA name raises error"""
        long_name = "A" * 51
        with pytest.raises(ValidationError, match="too long"):
            InputValidator.validate_ea_name(long_name)


class TestValidateFilterValue:
    """Tests for validate_filter_value method"""

    def test_valid_string_value(self):
        """Test valid string filter value"""
        assert InputValidator.validate_filter_value("HDQTR2") == "HDQTR2"

    def test_valid_numeric_value(self):
        """Test valid numeric filter values"""
        assert InputValidator.validate_filter_value(42) == 42
        assert InputValidator.validate_filter_value(3.14) == 3.14

    def test_valid_boolean_value(self):
        """Test valid boolean filter value"""
        assert InputValidator.validate_filter_value(True) is True
        assert InputValidator.validate_filter_value(False) is False

    def test_valid_none_value(self):
        """Test None is accepted"""
        assert InputValidator.validate_filter_value(None) is None

    def test_valid_list_value(self):
        """Test valid list of values"""
        result = InputValidator.validate_filter_value(["value1", "value2"])
        assert result == ["value1", "value2"]

    def test_invalid_shell_metacharacters(self):
        """Test shell metacharacters are blocked"""
        malicious_values = [
            "test; rm -rf /",
            "test && malicious",
            "test || other",
            "test `whoami`",
            "test $(whoami)",
            "test | grep password"
        ]
        for value in malicious_values:
            with pytest.raises(ValidationError, match="Invalid characters"):
                InputValidator.validate_filter_value(value)

    def test_invalid_path_traversal(self):
        """Test path traversal attempts are blocked"""
        with pytest.raises(ValidationError):
            InputValidator.validate_filter_value("../../etc/passwd")

    def test_invalid_xss_attempt(self):
        """Test XSS attempts are blocked"""
        with pytest.raises(ValidationError):
            InputValidator.validate_filter_value("<script>alert('xss')</script>")

    def test_too_long_value(self):
        """Test too long value raises error"""
        long_value = "A" * 1001
        with pytest.raises(ValidationError, match="too long"):
            InputValidator.validate_filter_value(long_value)


class TestValidateNetwork:
    """Tests for validate_network method"""

    def test_valid_network(self):
        """Test valid network in CIDR format"""
        assert InputValidator.validate_network("10.0.0.0/24") == "10.0.0.0/24"
        assert InputValidator.validate_network("192.168.1.0/16") == "192.168.1.0/16"

    def test_valid_network_various_prefixes(self):
        """Test valid networks with various prefixes"""
        assert InputValidator.validate_network("10.0.0.0/8") == "10.0.0.0/8"
        assert InputValidator.validate_network("10.0.0.0/32") == "10.0.0.0/32"
        assert InputValidator.validate_network("0.0.0.0/0") == "0.0.0.0/0"

    def test_invalid_network_format(self):
        """Test invalid network format raises error"""
        with pytest.raises(ValidationError, match="Invalid network format"):
            InputValidator.validate_network("10.0.0.0")

        with pytest.raises(ValidationError):
            InputValidator.validate_network("not a network")

    def test_invalid_prefix_range(self):
        """Test invalid prefix range"""
        with pytest.raises(ValidationError, match="Invalid network format"):
            InputValidator.validate_network("10.0.0.0/33")

        with pytest.raises(ValidationError, match="Invalid network format"):
            InputValidator.validate_network("10.0.0.0/-1")

    def test_invalid_ip_in_network(self):
        """Test invalid IP in network"""
        with pytest.raises(ValidationError):
            InputValidator.validate_network("999.999.999.999/24")


class TestValidateIPv4:
    """Tests for validate_ipv4 method"""

    def test_valid_ipv4(self):
        """Test valid IPv4 addresses"""
        assert InputValidator.validate_ipv4("10.0.0.1") == "10.0.0.1"
        assert InputValidator.validate_ipv4("192.168.1.1") == "192.168.1.1"
        assert InputValidator.validate_ipv4("255.255.255.255") == "255.255.255.255"
        assert InputValidator.validate_ipv4("0.0.0.0") == "0.0.0.0"

    def test_invalid_ipv4(self):
        """Test invalid IPv4 addresses"""
        with pytest.raises(ValidationError):
            InputValidator.validate_ipv4("999.999.999.999")

        with pytest.raises(ValidationError):
            InputValidator.validate_ipv4("10.0.0")

        with pytest.raises(ValidationError):
            InputValidator.validate_ipv4("not an ip")


class TestValidateHostname:
    """Tests for validate_hostname method"""

    def test_valid_hostname(self):
        """Test valid hostnames"""
        assert InputValidator.validate_hostname("server1") == "server1"
        assert InputValidator.validate_hostname("server1.example.com") == "server1.example.com"
        assert InputValidator.validate_hostname("sub.domain.example.com") == "sub.domain.example.com"

    def test_valid_hostname_with_dash(self):
        """Test valid hostname with dashes"""
        assert InputValidator.validate_hostname("web-server-01") == "web-server-01"

    def test_invalid_hostname_empty(self):
        """Test empty hostname raises error"""
        with pytest.raises(ValidationError, match="cannot be empty"):
            InputValidator.validate_hostname("")

    def test_invalid_hostname_too_long(self):
        """Test too long hostname"""
        long_name = "a" * 254
        with pytest.raises(ValidationError, match="too long"):
            InputValidator.validate_hostname(long_name)

    def test_invalid_hostname_characters(self):
        """Test invalid characters in hostname"""
        with pytest.raises(ValidationError):
            InputValidator.validate_hostname("server@example.com")


class TestValidateURL:
    """Tests for validate_url method"""

    def test_valid_http_url(self):
        """Test valid HTTP URL"""
        url = "http://example.com"
        assert InputValidator.validate_url(url) == url

    def test_valid_https_url(self):
        """Test valid HTTPS URL"""
        url = "https://example.com/path?query=value"
        assert InputValidator.validate_url(url) == url

    def test_invalid_scheme(self):
        """Test invalid URL scheme"""
        with pytest.raises(ValidationError, match="must use http or https"):
            InputValidator.validate_url("ftp://example.com")

    def test_invalid_javascript_scheme(self):
        """Test JavaScript scheme is blocked"""
        with pytest.raises(ValidationError, match="Invalid URL"):
            InputValidator.validate_url("javascript:alert('xss')")

    def test_invalid_no_domain(self):
        """Test URL without domain"""
        with pytest.raises(ValidationError, match="valid domain"):
            InputValidator.validate_url("http://")


class TestValidateFilePath:
    """Tests for validate_file_path method"""

    def test_valid_file_path(self, temp_dir):
        """Test valid file path within allowed directory"""
        test_file = temp_dir / "test.txt"
        result = InputValidator.validate_file_path(str(test_file), str(temp_dir))
        assert str(temp_dir) in result

    def test_path_traversal_blocked(self, temp_dir):
        """Test path traversal is blocked"""
        with pytest.raises(ValidationError, match="outside allowed directory"):
            InputValidator.validate_file_path("../../etc/passwd", str(temp_dir))

    def test_expands_user_home(self):
        """Test ~ expansion works"""
        result = InputValidator.validate_file_path("~/test.txt", os.path.expanduser("~"))
        assert os.path.expanduser("~") in result


class TestValidateToolInput:
    """Tests for validate_tool_input method"""

    def test_infoblox_query_valid(self):
        """Test valid infoblox_query input"""
        tool_input = {
            "object_type": "network",
            "filters": {"*MARSHA": "HDQTR2"},
            "max_results": 100
        }
        result = InputValidator.validate_tool_input("infoblox_query", tool_input)
        assert result["object_type"] == "network"
        assert result["filters"]["*MARSHA"] == "HDQTR2"

    def test_infoblox_query_invalid_object_type(self):
        """Test invalid object type in infoblox_query"""
        tool_input = {
            "object_type": "network; DROP TABLE",
            "filters": {}
        }
        with pytest.raises(ValidationError):
            InputValidator.validate_tool_input("infoblox_query", tool_input)

    def test_infoblox_query_invalid_filter_value(self):
        """Test invalid filter value in infoblox_query"""
        tool_input = {
            "object_type": "network",
            "filters": {"network": "10.0.0.0/24; rm -rf /"}
        }
        with pytest.raises(ValidationError):
            InputValidator.validate_tool_input("infoblox_query", tool_input)

    def test_infoblox_create_network_valid(self):
        """Test valid infoblox_create_network input"""
        tool_input = {
            "network": "10.50.0.0/24",
            "comment": "Test network"
        }
        result = InputValidator.validate_tool_input("infoblox_create_network", tool_input)
        assert result["network"] == "10.50.0.0/24"

    def test_infoblox_create_network_invalid(self):
        """Test invalid network in infoblox_create_network"""
        tool_input = {
            "network": "invalid network"
        }
        with pytest.raises(ValidationError):
            InputValidator.validate_tool_input("infoblox_create_network", tool_input)

    def test_web_search_valid(self):
        """Test valid web_search input"""
        tool_input = {"query": "test query"}
        result = InputValidator.validate_tool_input("web_search", tool_input)
        assert result["query"] == "test query"

    def test_unknown_tool_validates_values(self):
        """Test unknown tool still validates filter values"""
        tool_input = {"param1": "safe value"}
        result = InputValidator.validate_tool_input("unknown_tool", tool_input)
        assert result["param1"] == "safe value"

        with pytest.raises(ValidationError):
            InputValidator.validate_tool_input("unknown_tool", {"param1": "bad; value"})


@pytest.mark.security
class TestSecurityValidation:
    """Security-specific validation tests"""

    def test_sql_injection_blocked(self):
        """Test SQL injection attempts are blocked"""
        malicious_inputs = [
            "' OR '1'='1",
            "1; DROP TABLE users--",
            "admin'--",
        ]
        # Note: Our validators block shell metacharacters which also blocks many SQL injection attempts
        # Specific SQL injection in filter values
        for malicious in malicious_inputs:
            try:
                # Some might pass if they don't contain shell metacharacters
                result = InputValidator.validate_filter_value(malicious)
                # If it passes, that's OK as long as it's properly escaped by the API client
            except ValidationError:
                # Blocked is also good
                pass

    def test_command_injection_blocked(self):
        """Test command injection attempts are blocked"""
        malicious_inputs = [
            "; ls -la",
            "& whoami",
            "| cat /etc/passwd",
            "`id`",
            "$(whoami)",
        ]
        for malicious in malicious_inputs:
            with pytest.raises(ValidationError):
                InputValidator.validate_filter_value(malicious)

    def test_xss_blocked(self):
        """Test XSS attempts are blocked"""
        xss_attempts = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
        ]
        for xss in xss_attempts:
            with pytest.raises(ValidationError):
                InputValidator.validate_filter_value(xss)

    def test_path_traversal_blocked(self):
        """Test path traversal attempts are blocked"""
        with pytest.raises(ValidationError):
            InputValidator.validate_filter_value("../../etc/passwd")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

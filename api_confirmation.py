#!/usr/bin/env python
"""
API Call Confirmation System
Provides user preview and confirmation for InfoBlox API calls before execution
"""

import json
import re
from typing import Dict, Any, Optional, Tuple
from config import get_settings

# ANSI colors
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    CYAN = '\033[36m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    BRIGHT_YELLOW = '\033[93m'


class APICallConfirmation:
    """Handles API call preview, confirmation, and editing"""

    def __init__(self):
        self._settings = None
        self._base_url = None

    @property
    def settings(self):
        """Lazy load settings only when needed"""
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    @property
    def base_url(self):
        """Lazy load base URL only when needed"""
        if self._base_url is None:
            self._base_url = self.settings.get_infoblox_base_url()
        return self._base_url

    def map_tool_to_api_call(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Map tool call to API details (method, path, params)"""

        # Parse tool name to determine endpoint and method
        api_info = {
            "tool_name": tool_name,
            "method": "GET",  # default
            "path": "",
            "params": {},
            "data": None,
            "description": ""
        }

        # Map each tool to its API details
        if tool_name == "infoblox_list_networks":
            api_info["method"] = "GET"
            api_info["path"] = "network"
            api_info["params"] = {
                "_max_results": tool_input.get("max_results", 100)
            }
            if tool_input.get("return_fields"):
                api_info["params"]["_return_fields"] = tool_input["return_fields"]
            api_info["description"] = "List networks from InfoBlox"

        elif tool_name == "infoblox_get_network":
            api_info["method"] = "GET"
            api_info["path"] = tool_input.get("ref", "<NETWORK_REF>")
            api_info["params"] = {}
            if tool_input.get("return_fields"):
                api_info["params"]["_return_fields"] = tool_input["return_fields"]
            api_info["description"] = "Get specific network details"

        elif tool_name == "infoblox_create_network":
            api_info["method"] = "POST"
            api_info["path"] = "network"
            api_info["data"] = {
                "network": tool_input.get("network", "<NETWORK_CIDR>")
            }
            if tool_input.get("comment"):
                api_info["data"]["comment"] = tool_input["comment"]
            # Add any extra kwargs
            for key, value in tool_input.items():
                if key not in ["network", "comment"]:
                    api_info["data"][key] = value
            api_info["description"] = "Create new network"

        elif tool_name == "infoblox_search_records":
            record_type = tool_input.get("record_type", "a")
            api_info["method"] = "GET"
            api_info["path"] = f"record:{record_type}"
            api_info["params"] = {
                "_max_results": tool_input.get("max_results", 100)
            }
            if tool_input.get("name"):
                api_info["params"]["name"] = tool_input["name"]
            if tool_input.get("value"):
                api_info["params"]["ipv4addr"] = tool_input["value"]
            api_info["description"] = f"Search {record_type.upper()} DNS records"

        elif tool_name == "infoblox_list_dhcp_leases":
            api_info["method"] = "GET"
            api_info["path"] = "lease"
            api_info["params"] = {
                "_max_results": tool_input.get("max_results", 100)
            }
            if tool_input.get("network"):
                api_info["params"]["network"] = tool_input["network"]
            if tool_input.get("mac"):
                api_info["params"]["hardware"] = tool_input["mac"]
            api_info["description"] = "List DHCP leases"

        elif tool_name == "infoblox_query":
            api_info["method"] = "GET"
            api_info["path"] = tool_input.get("object_type", "<OBJECT_TYPE>")
            api_info["params"] = {
                "_max_results": tool_input.get("max_results", 100)
            }
            if tool_input.get("filters"):
                api_info["params"].update(tool_input["filters"])
            api_info["description"] = "Generic InfoBlox query"

        else:
            # Unknown tool - return generic info
            api_info["description"] = f"Execute {tool_name}"
            api_info["path"] = "<unknown>"

        return api_info

    def generate_curl_command(self, api_info: Dict[str, Any], username: Optional[str] = None) -> str:
        """Generate curl command equivalent with password masked"""

        user = username or self.settings.infoblox_user
        method = api_info["method"]
        path = api_info["path"]
        params = api_info.get("params", {})
        data = api_info.get("data")

        # Build URL
        url = f"{self.base_url}/{path.lstrip('/')}"

        # Add query parameters
        if params:
            param_str = "&".join([f"{k}={v}" for k, v in params.items()])
            url = f"{url}?{param_str}"

        # Build curl command
        curl_parts = [
            f"curl -X {method}",
            f"-u {user}:$INFOBLOX_PASSWORD",  # Use env var placeholder
        ]

        # Add data for POST/PUT
        if data:
            json_data = json.dumps(data, indent=2)
            curl_parts.append(f"-H 'Content-Type: application/json'")
            curl_parts.append(f"-d '{json_data}'")

        # Add URL (with quotes)
        curl_parts.append(f"'{url}'")

        return " \\\n  ".join(curl_parts)

    def display_api_preview(self, api_info: Dict[str, Any], username: Optional[str] = None) -> None:
        """Display formatted API call preview"""

        width = 70
        user = username or self.settings.infoblox_user

        print()
        print(f"{Colors.BRIGHT_CYAN}{'┌' + '─' * (width-2) + '┐'}{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}│{Colors.BOLD} 🔍 API Call Preview{' ' * (width-21)}│{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}{'├' + '─' * (width-2) + '┤'}{Colors.RESET}")

        # Description
        desc = api_info["description"]
        print(f"{Colors.BRIGHT_CYAN}│{Colors.RESET} {Colors.BRIGHT_WHITE}{desc}{' ' * (width-len(desc)-3)}│{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}│{' ' * (width-2)}│{Colors.RESET}")

        # Method
        method = api_info["method"]
        print(f"{Colors.BRIGHT_CYAN}│{Colors.RESET} {Colors.YELLOW}Method:{Colors.RESET}     {Colors.BRIGHT_WHITE}{method}{' ' * (width-len(method)-15)}│{Colors.RESET}")

        # Endpoint
        path = api_info["path"]
        full_path = f"/wapi/{self.settings.wapi_version}/{path}"
        if len(full_path) > width - 18:
            full_path = full_path[:width-21] + "..."
        print(f"{Colors.BRIGHT_CYAN}│{Colors.RESET} {Colors.YELLOW}Endpoint:{Colors.RESET}   {Colors.BRIGHT_WHITE}{full_path}{' ' * (width-len(full_path)-15)}│{Colors.RESET}")

        # Username
        print(f"{Colors.BRIGHT_CYAN}│{Colors.RESET} {Colors.YELLOW}Username:{Colors.RESET}   {Colors.BRIGHT_WHITE}{user}{' ' * (width-len(user)-15)}│{Colors.RESET}")

        # Parameters or Data
        if api_info.get("params"):
            print(f"{Colors.BRIGHT_CYAN}│{Colors.RESET} {Colors.YELLOW}Parameters:{Colors.RESET}{' ' * (width-14)}│{Colors.RESET}")
            for key, value in api_info["params"].items():
                param_line = f"  • {key}: {value}"
                if len(param_line) > width - 4:
                    param_line = param_line[:width-7] + "..."
                print(f"{Colors.BRIGHT_CYAN}│{Colors.RESET}   {Colors.BRIGHT_WHITE}{param_line}{' ' * (width-len(param_line)-5)}│{Colors.RESET}")

        if api_info.get("data"):
            print(f"{Colors.BRIGHT_CYAN}│{Colors.RESET} {Colors.YELLOW}Request Body:{Colors.RESET}{' ' * (width-16)}│{Colors.RESET}")
            data_str = json.dumps(api_info["data"], indent=2)
            for line in data_str.split('\n'):
                if len(line) > width - 6:
                    line = line[:width-9] + "..."
                print(f"{Colors.BRIGHT_CYAN}│{Colors.RESET}   {Colors.BRIGHT_WHITE}{line}{' ' * (width-len(line)-5)}│{Colors.RESET}")

        print(f"{Colors.BRIGHT_CYAN}│{' ' * (width-2)}│{Colors.RESET}")

        # Curl command
        print(f"{Colors.BRIGHT_CYAN}│{Colors.RESET} {Colors.YELLOW}Curl Equivalent:{Colors.RESET}{' ' * (width-19)}│{Colors.RESET}")
        curl_cmd = self.generate_curl_command(api_info, user)
        for line in curl_cmd.split('\n'):
            # Trim long lines
            display_line = line.strip()
            if len(display_line) > width - 6:
                display_line = display_line[:width-9] + "..."
            print(f"{Colors.BRIGHT_CYAN}│{Colors.RESET}   {Colors.DIM}{display_line}{' ' * (width-len(display_line)-5)}│{Colors.RESET}")

        print(f"{Colors.BRIGHT_CYAN}{'└' + '─' * (width-2) + '┘'}{Colors.RESET}")
        print()

    def get_user_confirmation(self) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Get user confirmation for API call
        Returns: (action, modified_data)
          action: 'yes', 'no', 'edit'
          modified_data: edited values if action=='yes' after edit
        """

        while True:
            try:
                response = input(f"{Colors.BRIGHT_YELLOW}Execute? (yes/no/edit) [{Colors.BRIGHT_WHITE}yes{Colors.BRIGHT_YELLOW}]: {Colors.RESET}").strip().lower()

                if not response or response in ['y', 'yes']:
                    return ('yes', None)
                elif response in ['n', 'no']:
                    return ('no', None)
                elif response in ['e', 'edit']:
                    return ('edit', None)
                else:
                    print(f"{Colors.YELLOW}Please enter 'yes', 'no', or 'edit'{Colors.RESET}")

            except (EOFError, KeyboardInterrupt):
                print()
                return ('no', None)

    def edit_parameters(self, api_info: Dict[str, Any]) -> Dict[str, Any]:
        """Allow user to edit API call parameters"""

        print()
        print(f"{Colors.BRIGHT_CYAN}{'─' * 70}{Colors.RESET}")
        print(f"{Colors.BRIGHT_WHITE}Edit Mode{Colors.RESET} - Press Enter to keep current value")
        print(f"{Colors.BRIGHT_CYAN}{'─' * 70}{Colors.RESET}")
        print()

        # Edit username
        current_user = self.settings.infoblox_user
        new_user = input(f"{Colors.YELLOW}Username [{Colors.BRIGHT_WHITE}{current_user}{Colors.YELLOW}]: {Colors.RESET}").strip()
        if new_user:
            api_info["_username"] = new_user

        # Edit parameters
        if api_info.get("params"):
            print()
            print(f"{Colors.YELLOW}Parameters:{Colors.RESET}")
            new_params = {}
            for key, value in api_info["params"].items():
                new_value = input(f"  {key} [{Colors.BRIGHT_WHITE}{value}{Colors.RESET}]: ").strip()
                new_params[key] = new_value if new_value else value
            api_info["params"] = new_params

        # Edit data (for POST/PUT)
        if api_info.get("data"):
            print()
            print(f"{Colors.YELLOW}Request Data:{Colors.RESET}")
            new_data = {}
            for key, value in api_info["data"].items():
                new_value = input(f"  {key} [{Colors.BRIGHT_WHITE}{value}{Colors.RESET}]: ").strip()
                new_data[key] = new_value if new_value else value
            api_info["data"] = new_data

        print()
        print(f"{Colors.GREEN}✓ Parameters updated{Colors.RESET}")

        return api_info

    def confirm_api_call(self, tool_name: str, tool_input: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """
        Main confirmation workflow
        Returns: (should_execute, final_tool_input, username)
        """

        # Map tool to API details
        api_info = self.map_tool_to_api_call(tool_name, tool_input)

        # Display preview
        username = None

        while True:
            self.display_api_preview(api_info, username)

            # Get confirmation
            action, _ = self.get_user_confirmation()

            if action == 'yes':
                # Extract modified values back into tool_input
                if "_username" in api_info:
                    username = api_info["_username"]

                # Update tool_input with any edited values
                if api_info.get("params"):
                    # Map params back to tool_input
                    if "max_results" in tool_input:
                        tool_input["max_results"] = api_info["params"].get("_max_results", 100)
                    # Add other mappings as needed

                if api_info.get("data"):
                    tool_input.update(api_info["data"])

                return (True, tool_input, username)

            elif action == 'no':
                print(f"{Colors.YELLOW}✗ API call cancelled{Colors.RESET}")
                return (False, tool_input, None)

            elif action == 'edit':
                api_info = self.edit_parameters(api_info)
                if "_username" in api_info:
                    username = api_info["_username"]
                # Loop back to show updated preview


# Global instance
api_confirmation = APICallConfirmation()

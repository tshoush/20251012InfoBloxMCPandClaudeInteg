#!/usr/bin/env python3
"""
Centralized Configuration Management
Secure configuration with environment variable validation
"""

import os
import logging
from typing import Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing"""
    pass


class Settings:
    """
    Application configuration loaded from environment variables.

    All sensitive values must be provided via environment variables.
    No default credentials are allowed.
    """

    def __init__(self):
        """Initialize settings from environment variables"""
        self._load_settings()
        self._validate_settings()

    def _load_settings(self):
        """Load all settings from environment variables"""

        # InfoBlox Configuration (REQUIRED)
        self.infoblox_host = os.getenv("INFOBLOX_HOST")
        self.infoblox_user = os.getenv("INFOBLOX_USER")
        self.infoblox_password = os.getenv("INFOBLOX_PASSWORD")
        self.wapi_version = os.getenv("WAPI_VERSION", "v2.13.1")

        # SSL Configuration
        self.infoblox_verify_ssl = os.getenv("INFOBLOX_VERIFY_SSL", "true").lower() == "true"
        self.infoblox_ca_bundle = os.getenv("INFOBLOX_CA_BUNDLE")

        # Anthropic Configuration (REQUIRED)
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

        # RAG Configuration
        self.rag_db_path = os.path.expanduser(
            os.getenv("RAG_DB_PATH", "~/.infoblox-rag")
        )
        self.rag_collection_name = os.getenv("RAG_COLLECTION_NAME", "infoblox_knowledge")

        # Logging Configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.log_file = os.getenv("LOG_FILE", "ddi-assistant.log")
        self.enable_security_audit = os.getenv("ENABLE_SECURITY_AUDIT", "true").lower() == "true"

        # Application Configuration
        self.app_name = "DDI Assistant"
        self.app_version = "1.0.0"

    def _validate_settings(self):
        """Validate required settings are present"""
        errors = []

        # Check InfoBlox credentials
        if not self.infoblox_host:
            errors.append("INFOBLOX_HOST environment variable is required")

        if not self.infoblox_user:
            errors.append("INFOBLOX_USER environment variable is required")

        if not self.infoblox_password:
            errors.append("INFOBLOX_PASSWORD environment variable is required")

        # Check Anthropic API key
        if not self.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY environment variable is required")

        if errors:
            error_msg = (
                "\n" + "="*70 + "\n"
                "CONFIGURATION ERROR: Missing required environment variables\n"
                + "="*70 + "\n\n"
                "The following environment variables must be set:\n\n"
                + "\n".join(f"  ✗ {error}" for error in errors) + "\n\n"
                "Please set these variables and try again:\n\n"
                "  export INFOBLOX_HOST=\"your-infoblox-host\"\n"
                "  export INFOBLOX_USER=\"your-username\"\n"
                "  export INFOBLOX_PASSWORD=\"your-password\"\n"
                "  export ANTHROPIC_API_KEY=\"your-api-key\"\n\n"
                "For more information, see: README.md\n"
                + "="*70 + "\n"
            )
            raise ConfigurationError(error_msg)

    def get_infoblox_base_url(self) -> str:
        """Get InfoBlox WAPI base URL"""
        return f"https://{self.infoblox_host}/wapi/{self.wapi_version}"

    def get_ssl_verify(self) -> Union[bool, str]:
        """
        Get SSL verification setting.

        Returns:
            True: Verify with system CA bundle
            False: Don't verify (INSECURE)
            str: Path to custom CA bundle
        """
        if self.infoblox_ca_bundle:
            return self.infoblox_ca_bundle
        return self.infoblox_verify_ssl

    def display_security_warning(self):
        """Display warning if SSL verification is disabled"""
        if not self.infoblox_verify_ssl and not self.infoblox_ca_bundle:
            warning = (
                "\n" + "="*70 + "\n"
                "⚠️  WARNING: SSL CERTIFICATE VERIFICATION IS DISABLED ⚠️\n"
                + "="*70 + "\n"
                "\nYour InfoBlox connection is vulnerable to man-in-the-middle attacks!\n"
                "\nThis should ONLY be used in isolated lab environments.\n"
                "\nTo enable SSL verification:\n"
                "  1. Set: export INFOBLOX_VERIFY_SSL=true\n"
                "  2. OR provide custom CA: export INFOBLOX_CA_BUNDLE=/path/to/ca.pem\n"
                "\nFor certificate installation instructions, see:\n"
                "  SECURITY-REVIEW-REPORT.md\n"
                + "="*70 + "\n"
            )
            logger.critical(warning)
            print(warning)

    def __repr__(self):
        """String representation (safe, no secrets)"""
        return (
            f"Settings("
            f"infoblox_host={self.infoblox_host}, "
            f"infoblox_user={self.infoblox_user}, "
            f"wapi_version={self.wapi_version}, "
            f"verify_ssl={self.infoblox_verify_ssl})"
        )


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get or create global settings instance.

    Returns:
        Settings instance

    Raises:
        ConfigurationError: If required environment variables are missing
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Convenience function for backward compatibility
def load_settings() -> Settings:
    """Load and return settings"""
    return get_settings()


if __name__ == "__main__":
    # Test configuration
    try:
        settings = get_settings()
        print("✓ Configuration loaded successfully")
        print(f"  InfoBlox: {settings.infoblox_host}")
        print(f"  WAPI Version: {settings.wapi_version}")
        print(f"  SSL Verify: {settings.get_ssl_verify()}")
    except ConfigurationError as e:
        print(str(e))

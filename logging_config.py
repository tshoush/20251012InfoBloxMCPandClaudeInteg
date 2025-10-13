#!/usr/bin/env python3
"""
Structured Logging Configuration
Provides application-wide logging with security audit trail
"""

import logging
import logging.handlers
import sys
import re
from pathlib import Path
from typing import Dict, Any


def setup_logging(
    log_level: str = "INFO",
    log_file: str = "ddi-assistant.log",
    enable_security_audit: bool = True
) -> None:
    """
    Configure application logging with file rotation and security audit trail.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Name of the main log file
        enable_security_audit: Whether to enable separate security audit log

    Example:
        >>> setup_logging(log_level="DEBUG")
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("Application started")
    """
    # Create logs directory
    log_dir = Path.home() / ".ddi-assistant" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_path = log_dir / log_file

    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler (stdout) - User-friendly format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)

    # File handler with rotation - Detailed format
    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Security audit logger (separate file)
    if enable_security_audit:
        security_logger = logging.getLogger('security_audit')
        security_logger.setLevel(logging.INFO)
        security_logger.propagate = False  # Don't propagate to root logger

        security_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'security_audit.log',
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,  # Keep more security logs
            encoding='utf-8'
        )
        security_formatter = logging.Formatter(
            '%(asctime)s - SECURITY - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        security_handler.setFormatter(security_formatter)
        security_logger.addHandler(security_handler)

    # Suppress verbose third-party logging
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('anthropic').setLevel(logging.INFO)
    logging.getLogger('chromadb').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)

    # Log initialization
    logger = logging.getLogger(__name__)
    logger.info("="*60)
    logger.info("Logging initialized")
    logger.info(f"Log level: {log_level}")
    logger.info(f"Log file: {log_path}")
    logger.info(f"Security audit: {'Enabled' if enable_security_audit else 'Disabled'}")
    logger.info("="*60)


def get_security_logger():
    """
    Get the security audit logger.

    Returns:
        Logger instance for security events

    Example:
        >>> security_logger = get_security_logger()
        >>> security_logger.info("User login successful")
    """
    return logging.getLogger('security_audit')


def sanitize_for_logging(data: Any) -> Any:
    """
    Sanitize data for logging by removing sensitive information.

    Args:
        data: Data to sanitize (string, dict, or other)

    Returns:
        Sanitized data safe for logging

    Example:
        >>> sanitize_for_logging({"password": "secret", "user": "admin"})
        {"password": "[REDACTED]", "user": "admin"}
    """
    if isinstance(data, str):
        # Remove passwords, API keys, tokens
        data = re.sub(
            r'(password|passwd|pwd|api_key|token|secret)[\'"]?\s*[:=]\s*[\'"]?[^\s\'"]+',
            r'\1=[REDACTED]',
            data,
            flags=re.IGNORECASE
        )
        # Remove IP addresses (optional - uncomment if needed)
        # data = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]', data)

    elif isinstance(data, dict):
        sanitized = {}
        sensitive_keys = {
            'password', 'passwd', 'pwd', 'api_key', 'token',
            'secret', 'authorization', 'auth'
        }
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = '[REDACTED]'
            else:
                sanitized[key] = sanitize_for_logging(value)
        return sanitized

    elif isinstance(data, (list, tuple)):
        return type(data)(sanitize_for_logging(item) for item in data)

    return data


# Security audit logging helpers

def log_authentication(host: str, user: str, success: bool, error: str = None) -> None:
    """
    Log authentication attempt.

    Args:
        host: InfoBlox host
        user: Username attempting authentication
        success: Whether authentication succeeded
        error: Error message if failed
    """
    security_logger = get_security_logger()
    if success:
        security_logger.info(
            f"Authentication SUCCESS - Host: {host}, User: {user}"
        )
    else:
        security_logger.warning(
            f"Authentication FAILED - Host: {host}, User: {user}, Error: {error}"
        )


def log_tool_execution(tool_name: str, params: Dict[str, Any], success: bool, error: str = None) -> None:
    """
    Log tool execution.

    Args:
        tool_name: Name of the tool executed
        params: Tool parameters (will be sanitized)
        success: Whether execution succeeded
        error: Error message if failed
    """
    security_logger = get_security_logger()
    safe_params = sanitize_for_logging(params)

    if success:
        security_logger.info(
            f"Tool SUCCESS - Name: {tool_name}, Params: {safe_params}"
        )
    else:
        security_logger.warning(
            f"Tool FAILED - Name: {tool_name}, Params: {safe_params}, Error: {error}"
        )


def log_api_error(endpoint: str, status_code: int, error: str) -> None:
    """
    Log API error.

    Args:
        endpoint: API endpoint that failed
        status_code: HTTP status code
        error: Error message
    """
    security_logger = get_security_logger()
    security_logger.warning(
        f"API ERROR - Endpoint: {endpoint}, Status: {status_code}, Error: {error}"
    )


def log_security_event(event_type: str, details: str, severity: str = "WARNING") -> None:
    """
    Log security event.

    Args:
        event_type: Type of security event
        details: Event details
        severity: Log severity (INFO, WARNING, ERROR, CRITICAL)
    """
    security_logger = get_security_logger()
    log_method = getattr(security_logger, severity.lower(), security_logger.warning)
    log_method(f"SECURITY EVENT - Type: {event_type}, Details: {details}")


def log_configuration_change(setting: str, old_value: Any, new_value: Any) -> None:
    """
    Log configuration change.

    Args:
        setting: Setting name
        old_value: Previous value
        new_value: New value
    """
    security_logger = get_security_logger()
    old_safe = sanitize_for_logging(old_value)
    new_safe = sanitize_for_logging(new_value)
    security_logger.info(
        f"CONFIG CHANGE - Setting: {setting}, Old: {old_safe}, New: {new_safe}"
    )


if __name__ == "__main__":
    # Test logging configuration
    setup_logging(log_level="DEBUG", enable_security_audit=True)

    # Test application logging
    logger = logging.getLogger(__name__)
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    # Test security audit logging
    log_authentication("192.168.1.224", "admin", True)
    log_authentication("192.168.1.224", "baduser", False, "Invalid credentials")
    log_tool_execution("infoblox_query", {"object_type": "network", "password": "secret"}, True)
    log_security_event("suspicious_activity", "Multiple failed login attempts")

    print("\nCheck logs at: ~/.ddi-assistant/logs/")
    print("  - ddi-assistant.log (application logs)")
    print("  - security_audit.log (security events)")

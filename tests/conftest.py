"""
Pytest configuration and shared fixtures
"""

import pytest
import os
import tempfile
from pathlib import Path


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing"""
    monkeypatch.setenv("INFOBLOX_HOST", "test.infoblox.local")
    monkeypatch.setenv("INFOBLOX_USER", "testuser")
    monkeypatch.setenv("INFOBLOX_PASSWORD", "testpass")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key-12345")
    monkeypatch.setenv("WAPI_VERSION", "v2.13.1")
    monkeypatch.setenv("INFOBLOX_VERIFY_SSL", "false")


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_infoblox_response():
    """Sample InfoBlox API response"""
    return [
        {
            "_ref": "network/ZG5zLm5ldHdvcms:10.0.0.0/24/default",
            "network": "10.0.0.0/24",
            "comment": "Test network",
            "extattrs": {
                "MARSHA": {"value": "HDQTR2"},
                "Site": {"value": "NYC"}
            }
        }
    ]


@pytest.fixture
def sample_network_schema():
    """Sample network object schema"""
    return {
        "fields": [
            {
                "name": "network",
                "type": ["string"],
                "searchable_by": True,
                "required": True
            },
            {
                "name": "comment",
                "type": ["string"],
                "searchable_by": False,
                "required": False
            }
        ]
    }


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration before each test"""
    import logging
    # Clear all handlers
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    yield
    # Clean up after test
    for handler in root.handlers[:]:
        root.removeHandler(handler)

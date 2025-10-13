"""
Unit tests for config module
"""

import pytest
import os
from config import Settings, ConfigurationError, get_settings


class TestSettingsInitialization:
    """Tests for Settings initialization"""

    def test_settings_with_all_env_vars(self, mock_env_vars):
        """Test settings load correctly with all environment variables"""
        settings = Settings()

        assert settings.infoblox_host == "test.infoblox.local"
        assert settings.infoblox_user == "testuser"
        assert settings.infoblox_password == "testpass"
        assert settings.anthropic_api_key == "sk-test-key-12345"
        assert settings.wapi_version == "v2.13.1"

    def test_settings_without_required_vars(self, monkeypatch):
        """Test settings raise error without required variables"""
        # Clear all environment variables
        for var in ["INFOBLOX_HOST", "INFOBLOX_USER", "INFOBLOX_PASSWORD", "ANTHROPIC_API_KEY"]:
            monkeypatch.delenv(var, raising=False)

        with pytest.raises(ConfigurationError) as exc_info:
            Settings()

        error_msg = str(exc_info.value)
        assert "INFOBLOX_HOST" in error_msg
        assert "INFOBLOX_USER" in error_msg
        assert "INFOBLOX_PASSWORD" in error_msg
        assert "ANTHROPIC_API_KEY" in error_msg

    def test_settings_missing_infoblox_host(self, mock_env_vars, monkeypatch):
        """Test error when INFOBLOX_HOST is missing"""
        monkeypatch.delenv("INFOBLOX_HOST")

        with pytest.raises(ConfigurationError, match="INFOBLOX_HOST"):
            Settings()

    def test_settings_missing_infoblox_user(self, mock_env_vars, monkeypatch):
        """Test error when INFOBLOX_USER is missing"""
        monkeypatch.delenv("INFOBLOX_USER")

        with pytest.raises(ConfigurationError, match="INFOBLOX_USER"):
            Settings()

    def test_settings_missing_infoblox_password(self, mock_env_vars, monkeypatch):
        """Test error when INFOBLOX_PASSWORD is missing"""
        monkeypatch.delenv("INFOBLOX_PASSWORD")

        with pytest.raises(ConfigurationError, match="INFOBLOX_PASSWORD"):
            Settings()

    def test_settings_missing_anthropic_key(self, mock_env_vars, monkeypatch):
        """Test error when ANTHROPIC_API_KEY is missing"""
        monkeypatch.delenv("ANTHROPIC_API_KEY")

        with pytest.raises(ConfigurationError, match="ANTHROPIC_API_KEY"):
            Settings()


class TestSettingsDefaults:
    """Tests for default settings values"""

    def test_default_wapi_version(self, mock_env_vars, monkeypatch):
        """Test default WAPI version"""
        monkeypatch.delenv("WAPI_VERSION", raising=False)
        settings = Settings()

        assert settings.wapi_version == "v2.13.1"

    def test_custom_wapi_version(self, mock_env_vars, monkeypatch):
        """Test custom WAPI version"""
        monkeypatch.setenv("WAPI_VERSION", "v2.12.1")
        settings = Settings()

        assert settings.wapi_version == "v2.12.1"

    def test_default_ssl_verify(self, mock_env_vars, monkeypatch):
        """Test default SSL verification is enabled"""
        monkeypatch.delenv("INFOBLOX_VERIFY_SSL", raising=False)
        settings = Settings()

        assert settings.infoblox_verify_ssl is True

    def test_ssl_verify_false(self, mock_env_vars, monkeypatch):
        """Test SSL verification can be disabled"""
        monkeypatch.setenv("INFOBLOX_VERIFY_SSL", "false")
        settings = Settings()

        assert settings.infoblox_verify_ssl is False

    def test_ssl_verify_true_explicit(self, mock_env_vars, monkeypatch):
        """Test SSL verification explicitly enabled"""
        monkeypatch.setenv("INFOBLOX_VERIFY_SSL", "true")
        settings = Settings()

        assert settings.infoblox_verify_ssl is True

    def test_default_rag_db_path(self, mock_env_vars):
        """Test default RAG database path"""
        settings = Settings()

        assert ".infoblox-rag" in settings.rag_db_path

    def test_custom_rag_db_path(self, mock_env_vars, monkeypatch, temp_dir):
        """Test custom RAG database path"""
        custom_path = str(temp_dir / "custom-rag")
        monkeypatch.setenv("RAG_DB_PATH", custom_path)
        settings = Settings()

        assert custom_path in settings.rag_db_path

    def test_default_log_level(self, mock_env_vars):
        """Test default log level"""
        settings = Settings()

        assert settings.log_level == "INFO"

    def test_custom_log_level(self, mock_env_vars, monkeypatch):
        """Test custom log level"""
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        settings = Settings()

        assert settings.log_level == "DEBUG"


class TestSettingsMethods:
    """Tests for Settings methods"""

    def test_get_infoblox_base_url(self, mock_env_vars):
        """Test get_infoblox_base_url method"""
        settings = Settings()

        url = settings.get_infoblox_base_url()

        assert url == "https://test.infoblox.local/wapi/v2.13.1"

    def test_get_ssl_verify_true(self, mock_env_vars, monkeypatch):
        """Test get_ssl_verify returns True when enabled"""
        monkeypatch.setenv("INFOBLOX_VERIFY_SSL", "true")
        monkeypatch.delenv("INFOBLOX_CA_BUNDLE", raising=False)
        settings = Settings()

        assert settings.get_ssl_verify() is True

    def test_get_ssl_verify_false(self, mock_env_vars, monkeypatch):
        """Test get_ssl_verify returns False when disabled"""
        monkeypatch.setenv("INFOBLOX_VERIFY_SSL", "false")
        monkeypatch.delenv("INFOBLOX_CA_BUNDLE", raising=False)
        settings = Settings()

        assert settings.get_ssl_verify() is False

    def test_get_ssl_verify_with_ca_bundle(self, mock_env_vars, monkeypatch):
        """Test get_ssl_verify returns CA bundle path when set"""
        ca_bundle = "/path/to/ca-bundle.pem"
        monkeypatch.setenv("INFOBLOX_CA_BUNDLE", ca_bundle)
        settings = Settings()

        assert settings.get_ssl_verify() == ca_bundle

    def test_repr(self, mock_env_vars):
        """Test __repr__ method doesn't expose secrets"""
        settings = Settings()

        repr_str = repr(settings)

        # Should include non-sensitive info
        assert "test.infoblox.local" in repr_str
        assert "testuser" in repr_str
        assert "v2.13.1" in repr_str

        # Should NOT include password or API key
        assert "testpass" not in repr_str
        assert "sk-test-key" not in repr_str


class TestGetSettings:
    """Tests for get_settings function"""

    def test_get_settings_returns_singleton(self, mock_env_vars):
        """Test get_settings returns the same instance"""
        # Clear any existing instance
        import config
        config._settings = None

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_get_settings_raises_on_missing_config(self, monkeypatch):
        """Test get_settings raises ConfigurationError"""
        # Clear any existing instance
        import config
        config._settings = None

        # Clear environment variables
        for var in ["INFOBLOX_HOST", "INFOBLOX_USER", "INFOBLOX_PASSWORD", "ANTHROPIC_API_KEY"]:
            monkeypatch.delenv(var, raising=False)

        with pytest.raises(ConfigurationError):
            get_settings()


class TestSSLConfiguration:
    """Tests for SSL configuration"""

    def test_ssl_enabled_by_default(self, mock_env_vars, monkeypatch):
        """Test SSL verification is enabled by default"""
        monkeypatch.delenv("INFOBLOX_VERIFY_SSL", raising=False)
        monkeypatch.delenv("INFOBLOX_CA_BUNDLE", raising=False)

        settings = Settings()

        assert settings.infoblox_verify_ssl is True
        assert settings.infoblox_ca_bundle is None
        assert settings.get_ssl_verify() is True

    def test_ssl_with_custom_ca(self, mock_env_vars, monkeypatch):
        """Test SSL with custom CA bundle"""
        ca_path = "/etc/ssl/certs/infoblox-ca.pem"
        monkeypatch.setenv("INFOBLOX_CA_BUNDLE", ca_path)

        settings = Settings()

        assert settings.get_ssl_verify() == ca_path

    def test_ssl_disabled_shows_warning(self, mock_env_vars, monkeypatch, capsys):
        """Test warning is displayed when SSL is disabled"""
        monkeypatch.setenv("INFOBLOX_VERIFY_SSL", "false")
        monkeypatch.delenv("INFOBLOX_CA_BUNDLE", raising=False)

        settings = Settings()
        settings.display_security_warning()

        captured = capsys.readouterr()

        assert "WARNING" in captured.out
        assert "SSL" in captured.out
        assert "man-in-the-middle" in captured.out

    def test_ssl_enabled_no_warning(self, mock_env_vars, monkeypatch, capsys):
        """Test no warning when SSL is enabled"""
        monkeypatch.setenv("INFOBLOX_VERIFY_SSL", "true")

        settings = Settings()
        settings.display_security_warning()

        captured = capsys.readouterr()

        # Should not display warning
        assert captured.out == ""


@pytest.mark.integration
class TestSettingsWithEnvironment:
    """Integration tests with actual environment"""

    def test_load_from_env_file(self, tmp_path, monkeypatch):
        """Test loading from .env file (if supported)"""
        # Note: This test would require python-dotenv
        # For now, just test manual environment setting
        monkeypatch.setenv("INFOBLOX_HOST", "prod.infoblox.example.com")
        monkeypatch.setenv("INFOBLOX_USER", "admin")
        monkeypatch.setenv("INFOBLOX_PASSWORD", "secure_password")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-real-key")

        settings = Settings()

        assert settings.infoblox_host == "prod.infoblox.example.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

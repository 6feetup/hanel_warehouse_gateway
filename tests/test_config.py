"""Tests for GatewayConfig of hanel_warehouse_gateway."""

from __future__ import annotations

import pytest

from hanel_warehouse_gateway import GatewayConfig


class TestGatewayConfigDefaults:
    def test_minimal_valid_config(self) -> None:
        config = GatewayConfig(endpoint_url="http://192.168.1.1:8080/service")
        assert config.timeout_seconds == 30
        assert config.retry_attempts == 3
        assert config.retry_delay_seconds == 2.0
        assert config.test_mode is False
        assert config.test_prefix == "TEST_"
        assert config.log_level == "INFO"
        assert config.log_soap_payloads is False
        assert config.validation_truncate is False

    def test_namespace_defaults(self) -> None:
        config = GatewayConfig(endpoint_url="http://example.com/")
        assert config.namespace_main == "http://main.jws.com.hanel.de"
        assert config.namespace_xsd == "http://main.jws.com.hanel.de/xsd"

    def test_https_endpoint_valid(self) -> None:
        config = GatewayConfig(endpoint_url="https://secure.example.com/hanel")
        assert config.endpoint_url.startswith("https://")


class TestGatewayConfigValidation:
    def test_empty_endpoint_raises(self) -> None:
        with pytest.raises(ValueError, match="endpoint_url"):
            GatewayConfig(endpoint_url="")

    def test_blank_endpoint_raises(self) -> None:
        with pytest.raises(ValueError, match="endpoint_url"):
            GatewayConfig(endpoint_url="   ")

    def test_invalid_scheme_raises(self) -> None:
        with pytest.raises(ValueError, match="http"):
            GatewayConfig(endpoint_url="ftp://example.com/service")

    def test_zero_timeout_raises(self) -> None:
        with pytest.raises(ValueError, match="timeout_seconds"):
            GatewayConfig(endpoint_url="http://x.com/", timeout_seconds=0)

    def test_negative_timeout_raises(self) -> None:
        with pytest.raises(ValueError, match="timeout_seconds"):
            GatewayConfig(endpoint_url="http://x.com/", timeout_seconds=-1)

    def test_zero_retry_attempts_raises(self) -> None:
        with pytest.raises(ValueError, match="retry_attempts"):
            GatewayConfig(endpoint_url="http://x.com/", retry_attempts=0)

    def test_negative_retry_delay_raises(self) -> None:
        with pytest.raises(ValueError, match="retry_delay_seconds"):
            GatewayConfig(endpoint_url="http://x.com/", retry_delay_seconds=-0.1)

    def test_invalid_log_level_raises(self) -> None:
        with pytest.raises(ValueError, match="log_level"):
            GatewayConfig(endpoint_url="http://x.com/", log_level="VERBOSE")


class TestGatewayConfigFromEnv:
    def test_from_env_with_overrides(self) -> None:
        config = GatewayConfig.from_env(
            overrides={
                "endpoint_url": "http://mock-server/",
                "test_mode": True,
                "timeout_seconds": 10,
            }
        )
        assert config.endpoint_url == "http://mock-server/"
        assert config.test_mode is True
        assert config.timeout_seconds == 10

    def test_from_env_reads_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HANEL_ENDPOINT_URL", "http://env-server/")
        monkeypatch.setenv("HANEL_TEST_MODE", "true")
        monkeypatch.setenv("HANEL_TEST_PREFIX", "CI_")
        config = GatewayConfig.from_env()
        assert config.endpoint_url == "http://env-server/"
        assert config.test_mode is True
        assert config.test_prefix == "CI_"

    def test_overrides_win_over_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HANEL_ENDPOINT_URL", "http://env-server/")
        config = GatewayConfig.from_env(overrides={"endpoint_url": "http://override/"})
        assert config.endpoint_url == "http://override/"

    def test_unknown_keys_ignored(self) -> None:
        config = GatewayConfig.from_env(
            overrides={
                "endpoint_url": "http://x.com/",
                "nonexistent_param": "value",
            }
        )
        assert config.endpoint_url == "http://x.com/"
        assert not hasattr(config, "nonexistent_param")

    def test_test_mode_false_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HANEL_ENDPOINT_URL", "http://x.com/")
        monkeypatch.setenv("HANEL_TEST_MODE", "false")
        config = GatewayConfig.from_env()
        assert config.test_mode is False

    def test_lot_management_default_false(self) -> None:
        config = GatewayConfig(endpoint_url="http://x.com/")
        assert config.lot_management_enabled is False

    def test_lot_management_from_env_true(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HANEL_ENDPOINT_URL", "http://x.com/")
        monkeypatch.setenv("HANEL_LOT_MANAGEMENT_ENABLED", "true")
        config = GatewayConfig.from_env()
        assert config.lot_management_enabled is True

    def test_lot_management_from_env_false(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HANEL_ENDPOINT_URL", "http://x.com/")
        monkeypatch.setenv("HANEL_LOT_MANAGEMENT_ENABLED", "false")
        config = GatewayConfig.from_env()
        assert config.lot_management_enabled is False

    def test_lot_management_from_env_case_insensitive(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HANEL_ENDPOINT_URL", "http://x.com/")
        monkeypatch.setenv("HANEL_LOT_MANAGEMENT_ENABLED", "TRUE")
        config = GatewayConfig.from_env()
        assert config.lot_management_enabled is True

    def test_lot_management_override(self) -> None:
        config = GatewayConfig.from_env(
            overrides={"endpoint_url": "http://x.com/", "lot_management_enabled": True}
        )
        assert config.lot_management_enabled is True

    def test_log_level_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HANEL_ENDPOINT_URL", "http://x.com/")
        monkeypatch.setenv("HANEL_LOG_LEVEL", "debug")
        config = GatewayConfig.from_env()
        assert config.log_level == "DEBUG"

    def test_log_soap_payloads_from_env_true(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HANEL_ENDPOINT_URL", "http://x.com/")
        monkeypatch.setenv("HANEL_LOG_SOAP_PAYLOADS", "true")
        config = GatewayConfig.from_env()
        assert config.log_soap_payloads is True

    def test_log_soap_payloads_from_env_false(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HANEL_ENDPOINT_URL", "http://x.com/")
        monkeypatch.setenv("HANEL_LOG_SOAP_PAYLOADS", "false")
        config = GatewayConfig.from_env()
        assert config.log_soap_payloads is False

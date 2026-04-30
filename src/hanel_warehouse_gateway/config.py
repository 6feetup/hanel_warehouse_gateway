"""Configuration for the hanel_warehouse_gateway module."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, fields

logger = logging.getLogger(__name__)

_VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR"}


@dataclass
class GatewayConfig:
    """Full configuration for the Hanel gateway.

    Use GatewayConfig.from_env() to load from .env or environment variables.
    """

    # Volatile parameter — must come from the environment, not committed code
    endpoint_url: str

    # SOAP namespaces — fixed values defined by the Hanel protocol
    namespace_main: str = "http://main.jws.com.hanel.de"
    namespace_xsd: str = "http://main.jws.com.hanel.de/xsd"

    # Static parameters with defaults
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: float = 2.0
    test_mode: bool = False
    test_prefix: str = "TEST_"
    log_level: str = "INFO"
    log_soap_payloads: bool = False
    validation_truncate: bool = False

    def __post_init__(self) -> None:
        if not self.endpoint_url or not self.endpoint_url.strip():
            raise ValueError("endpoint_url cannot be empty")
        if not self.endpoint_url.startswith(("http://", "https://")):
            raise ValueError(
                f"endpoint_url must start with http:// or https://, "
                f"got: {self.endpoint_url!r}"
            )
        if self.timeout_seconds <= 0:
            raise ValueError(
                f"timeout_seconds must be > 0, got: {self.timeout_seconds}"
            )
        if self.retry_attempts < 1:
            raise ValueError(
                f"retry_attempts must be >= 1, got: {self.retry_attempts}"
            )
        if self.retry_delay_seconds < 0:
            raise ValueError(
                f"retry_delay_seconds must be >= 0, "
                f"got: {self.retry_delay_seconds}"
            )
        if self.log_level not in _VALID_LOG_LEVELS:
            raise ValueError(
                f"log_level must be one of {sorted(_VALID_LOG_LEVELS)}, "
                f"got: {self.log_level!r}"
            )

    @classmethod
    def from_env(cls, overrides: dict[str, object] | None = None) -> GatewayConfig:
        """Build a GatewayConfig by reading environment variables.

        Automatically loads the .env file from the current directory (no-op if
        it does not exist). Environment variables use the HANEL_ prefix. The
        overrides dict, if provided, takes precedence over everything else.

        Args:
            overrides: Parameters that override those read from the environment.
                Useful in tests to inject mock values.
        """
        from dotenv import load_dotenv

        load_dotenv()

        env_values: dict[str, object] = {}

        raw_url = os.getenv("HANEL_ENDPOINT_URL")
        if raw_url is not None:
            env_values["endpoint_url"] = raw_url

        raw_test_mode = os.getenv("HANEL_TEST_MODE")
        if raw_test_mode is not None:
            env_values["test_mode"] = raw_test_mode.strip().lower() == "true"

        raw_test_prefix = os.getenv("HANEL_TEST_PREFIX")
        if raw_test_prefix is not None:
            env_values["test_prefix"] = raw_test_prefix

        if overrides:
            env_values.update(overrides)

        return cls._from_dict(env_values)

    @classmethod
    def _from_dict(cls, d: dict[str, object]) -> GatewayConfig:
        """Build a GatewayConfig from a dictionary, ignoring unknown keys."""
        known_keys = {f.name for f in fields(cls)}
        unknown = set(d.keys()) - known_keys
        if unknown:
            logger.warning(
                "GatewayConfig: unknown keys ignored: %s", sorted(unknown)
            )
        filtered = {k: v for k, v in d.items() if k in known_keys}
        return cls(**filtered)  # type: ignore[arg-type]

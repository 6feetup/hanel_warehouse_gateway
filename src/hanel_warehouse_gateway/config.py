"""Configurazione del modulo hanel_warehouse_gateway."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, fields

logger = logging.getLogger(__name__)

_VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR"}


@dataclass
class GatewayConfig:
    """Configurazione completa del gateway Hanel.

    Usare GatewayConfig.from_env() per caricare da .env o variabili d'ambiente.
    """

    # Parametro volatile — deve provenire dall'ambiente, non da codice committato
    endpoint_url: str

    # Namespace SOAP — valori fissi definiti dal protocollo Hanel
    namespace_main: str = "http://main.jws.com.hanel.de"
    namespace_xsd: str = "http://main.jws.com.hanel.de/xsd"

    # Parametri statici con default
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
            raise ValueError("endpoint_url non può essere vuoto")
        if not self.endpoint_url.startswith(("http://", "https://")):
            raise ValueError(
                f"endpoint_url deve iniziare con http:// o https://, "
                f"ricevuto: {self.endpoint_url!r}"
            )
        if self.timeout_seconds <= 0:
            raise ValueError(
                f"timeout_seconds deve essere > 0, ricevuto: {self.timeout_seconds}"
            )
        if self.retry_attempts < 1:
            raise ValueError(
                f"retry_attempts deve essere >= 1, ricevuto: {self.retry_attempts}"
            )
        if self.retry_delay_seconds < 0:
            raise ValueError(
                f"retry_delay_seconds deve essere >= 0, "
                f"ricevuto: {self.retry_delay_seconds}"
            )
        if self.log_level not in _VALID_LOG_LEVELS:
            raise ValueError(
                f"log_level deve essere uno tra {sorted(_VALID_LOG_LEVELS)}, "
                f"ricevuto: {self.log_level!r}"
            )

    @classmethod
    def from_env(cls, overrides: dict[str, object] | None = None) -> GatewayConfig:
        """Costruisce GatewayConfig leggendo le variabili d'ambiente.

        Carica automaticamente il file .env dalla directory corrente (no-op se
        non esiste). Le variabili d'ambiente hanno prefisso HANEL_. Il dict
        overrides, se fornito, ha precedenza su tutto.

        Args:
            overrides: Parametri che sovrascrivono quelli letti dall'ambiente.
                Utile nei test per iniettare valori mock.
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
        """Costruisce GatewayConfig da un dizionario, ignorando chiavi sconosciute."""
        known_keys = {f.name for f in fields(cls)}
        unknown = set(d.keys()) - known_keys
        if unknown:
            logger.warning(
                "GatewayConfig: chiavi sconosciute ignorate: %s", sorted(unknown)
            )
        filtered = {k: v for k, v in d.items() if k in known_keys}
        return cls(**filtered)  # type: ignore[arg-type]

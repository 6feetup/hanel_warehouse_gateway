"""Layer 1 — SOAP Transport.

Performs HTTP POST with retry on network errors. Does not interpret XML content.
"""

from __future__ import annotations

import logging

from .config import GatewayConfig

logger = logging.getLogger(__name__)


class SoapTransport:
    """HTTP client for SOAP calls to the Hanel t-Server.

    Handles automatic retries on network errors. Does not retry on
    HTTP errors (4xx/5xx) or SOAP faults.
    """

    def __init__(self, config: GatewayConfig) -> None:
        self._config = config

    def post(self, envelope: str, operation: str) -> str:
        """Perform an HTTP POST with the provided SOAP envelope.

        Args:
            envelope: XML string of the SOAP envelope to send.
            operation: SOAP operation name (used in logs and exceptions).

        Returns:
            XML string of the raw HTTP response body.

        Raises:
            HanelGatewayNetworkError: If all retry attempts are exhausted.
            HanelGatewayHttpError: If the response has a non-2xx status code.
        """
        raise NotImplementedError

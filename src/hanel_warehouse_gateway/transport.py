"""Layer 1 — SOAP Transport.

Performs HTTP POST with retry on network errors. Does not interpret XML content.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

import requests

from .config import GatewayConfig
from .exceptions import HanelGatewayHttpError, HanelGatewayNetworkError

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
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": '""',
        }

        if self._config.log_soap_payloads:
            logger.debug("→ %s request:\n%s", operation, envelope)

        last_exc: Exception | None = None
        for attempt in range(1, self._config.retry_attempts + 1):
            try:
                response = requests.post(
                    self._config.endpoint_url,
                    data=envelope.encode("utf-8"),
                    headers=headers,
                    timeout=self._config.timeout_seconds,
                )
                if self._config.log_soap_payloads:
                    logger.debug("← %s response:\n%s", operation, response.text)
                if not response.ok:
                    raise HanelGatewayHttpError(
                        message=(
                            f"HTTP {response.status_code} for operation {operation}"
                        ),
                        operation=operation,
                        detail=response.text[:500],
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        http_status=response.status_code,
                    )
                return response.text
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_exc = exc
                if attempt == self._config.retry_attempts:
                    break
                logger.warning(
                    "Retry %d/%d for operation %s: %s",
                    attempt,
                    self._config.retry_attempts,
                    operation,
                    exc,
                )
                time.sleep(self._config.retry_delay_seconds)

        raise HanelGatewayNetworkError(
            message=(
                f"Network error after {self._config.retry_attempts}"
                f" attempt(s) for operation {operation}"
            ),
            operation=operation,
            detail=str(last_exc),
            timestamp=datetime.now(timezone.utc).isoformat(),
        ) from last_exc

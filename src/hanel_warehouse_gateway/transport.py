"""Layer 1 — SOAP Transport.

Performs HTTP POST with retry on network errors. Does not interpret XML content.
"""

from __future__ import annotations

import datetime
import logging
import time

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
            logger.debug("Request [%s]: %s", operation, envelope)

        response: requests.Response | None = None
        for attempt in range(1, self._config.retry_attempts + 1):
            try:
                response = requests.post(
                    self._config.endpoint_url,
                    data=envelope.encode("utf-8"),
                    headers=headers,
                    timeout=self._config.timeout_seconds,
                )
                break
            except (requests.ConnectionError, requests.Timeout) as exc:
                if attempt == self._config.retry_attempts:
                    raise HanelGatewayNetworkError(
                        message=(
                            f"Network error after {self._config.retry_attempts}"
                            f" attempts for {operation}"
                        ),
                        operation=operation,
                        detail=str(exc),
                        timestamp=datetime.datetime.utcnow().isoformat(),
                    ) from exc
                logger.warning(
                    "Retry %d/%d for operation %s: %s",
                    attempt,
                    self._config.retry_attempts,
                    operation,
                    exc,
                )
                time.sleep(self._config.retry_delay_seconds)

        assert response is not None

        if self._config.log_soap_payloads:
            logger.debug("Response [%s]: %s", operation, response.text)

        if not response.ok:
            raise HanelGatewayHttpError(
                message=f"HTTP {response.status_code} for operation {operation}",
                operation=operation,
                detail=response.text[:500],
                timestamp=datetime.datetime.utcnow().isoformat(),
                http_status=response.status_code,
            )

        return response.text

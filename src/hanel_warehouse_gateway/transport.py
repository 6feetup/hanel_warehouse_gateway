"""Layer 1 — SOAP Transport.

Esegue HTTP POST con retry su errori di rete. Non interpreta il contenuto XML.
"""

from __future__ import annotations

import logging

from .config import GatewayConfig

logger = logging.getLogger(__name__)


class SoapTransport:
    """Client HTTP per le chiamate SOAP al t-Server Hanel.

    Gestisce retry automatici su errori di rete. Non esegue retry su
    errori HTTP (4xx/5xx) o fault SOAP.
    """

    def __init__(self, config: GatewayConfig) -> None:
        self._config = config

    def post(self, envelope: str, operation: str) -> str:
        """Esegue un HTTP POST con l'envelope SOAP fornito.

        Args:
            envelope: Stringa XML dell'envelope SOAP da inviare.
            operation: Nome dell'operazione SOAP (usato in log ed eccezioni).

        Returns:
            Stringa XML della risposta HTTP (body grezzo).

        Raises:
            HanelGatewayNetworkError: Se tutti i tentativi di retry falliscono.
            HanelGatewayHttpError: Se la risposta ha status code non 2xx.
        """
        raise NotImplementedError

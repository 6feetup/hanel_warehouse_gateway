"""Layer 2 — SOAP Operations.

Mappa ogni operazione di business alla corrispondente chiamata SOAP.
Serializza gli input, deserializza le risposte, valida i campi.
Non esegue chiamate HTTP direttamente: delega a SoapTransport.
"""

from __future__ import annotations

import logging

from .config import GatewayConfig
from .models import MovementLine, MovementResult, StockRecord
from .transport import SoapTransport

logger = logging.getLogger(__name__)


class SoapOperations:
    """Implementa le operazioni SOAP del t-Server Hanel."""

    def __init__(self, config: GatewayConfig, transport: SoapTransport) -> None:
        self._config = config
        self._transport = transport

    def register_article(self, article_number: str, article_name: str) -> bool:
        """Registra o aggiorna un articolo nel magazzino (sendAPDReqV01)."""
        raise NotImplementedError

    def send_movement_order(
        self, order_number: str, positions: list[MovementLine]
    ) -> bool:
        """Invia un ordine di movimento al magazzino (sendJobsReqV01)."""
        raise NotImplementedError

    def get_completed_movements(self) -> list[MovementResult]:
        """Recupera gli ordini completati (readAllJobsReqV01, mode=1)."""
        raise NotImplementedError

    def get_all_orders(self) -> list[MovementResult]:
        """Recupera tutti gli ordini in coda (readAllJobsReqV01, mode=0)."""
        raise NotImplementedError

    def get_inventory(self) -> list[StockRecord]:
        """Recupera i livelli di stock di tutti gli articoli (readAllAMDReqV01)."""
        raise NotImplementedError

    def cancel_order(self, order_number: str) -> bool:
        """Cancella un ordine dalla coda (deleteJobReqV01)."""
        raise NotImplementedError

"""Layer 3 — Interfaccia pubblica del modulo hanel_warehouse_gateway.

HanelWarehouseGateway è l'unico punto di contatto per il sistema chiamante.
Nasconde completamente i dettagli SOAP, HTTP e XML.
"""

from __future__ import annotations

import logging

from .config import GatewayConfig
from .models import MovementLine, MovementResult, StockRecord
from .operations import SoapOperations
from .transport import SoapTransport

logger = logging.getLogger(__name__)


class HanelWarehouseGateway:
    """Gateway per il magazzino automatico Hanel via SOAP.

    Il modulo non è thread-safe. In caso di chiamate concorrenti,
    istanziare un client per thread.

    Example:
        config = GatewayConfig.from_env()
        gateway = HanelWarehouseGateway(config)
        gateway.register_article("ART001", "Vite M6 inox")
    """

    def __init__(self, config: GatewayConfig) -> None:
        self._config = config
        self._transport = SoapTransport(config)
        self._operations = SoapOperations(config, self._transport)

    def register_article(self, article_number: str, article_name: str) -> bool:
        """Registra o aggiorna un articolo nell'anagrafica del magazzino.

        Args:
            article_number: Codice articolo univoco (max 40 chars alfanumerici).
            article_name: Descrizione articolo (max 40 chars).

        Returns:
            True se l'operazione è andata a buon fine (returnValue == 0).
        """
        raise NotImplementedError

    def send_movement_order(
        self, order_number: str, positions: list[MovementLine]
    ) -> bool:
        """Invia un ordine di movimento (prelievo o carico) al magazzino.

        Args:
            order_number: Identificativo ordine univoco (max 40 chars).
            positions: Lista di righe di movimento (almeno un elemento).

        Returns:
            True se l'operazione è andata a buon fine (returnValue == 0).
        """
        raise NotImplementedError

    def get_completed_movements(self) -> list[MovementResult]:
        """Recupera gli ordini completati dal magazzino.

        Se actual_quantity < nominal_quantity in una riga, lo stock era
        insufficiente: la gestione è responsabilità del chiamante.
        """
        raise NotImplementedError

    def get_all_orders(self) -> list[MovementResult]:
        """Recupera tutti gli ordini presenti nella coda del magazzino."""
        raise NotImplementedError

    def get_inventory(self) -> list[StockRecord]:
        """Recupera i livelli di stock di tutti gli articoli nel magazzino.

        Unico meccanismo per rilevare movimenti manuali eseguiti alla console.
        """
        raise NotImplementedError

    def cancel_order(self, order_number: str) -> bool:
        """Cancella un ordine dalla coda del magazzino.

        Applicabile solo ad ordini non ancora processati (stato 0).

        Args:
            order_number: Identificativo dell'ordine da cancellare (max 40 chars).

        Returns:
            True se l'operazione è andata a buon fine (returnValue == 0).
        """
        raise NotImplementedError

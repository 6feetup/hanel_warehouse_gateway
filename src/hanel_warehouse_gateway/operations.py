"""Layer 2 — SOAP Operations.

Maps each business operation to the corresponding SOAP call.
Serializes inputs, deserializes responses, validates fields.
Does not make HTTP calls directly: delegates to SoapTransport.
"""

from __future__ import annotations

import logging

from .config import GatewayConfig
from .models import MovementLine, MovementResult, StockRecord
from .transport import SoapTransport

logger = logging.getLogger(__name__)


class SoapOperations:
    """Implements SOAP operations for the Hanel t-Server."""

    def __init__(self, config: GatewayConfig, transport: SoapTransport) -> None:
        self._config = config
        self._transport = transport

    def register_article(self, article_number: str, article_name: str) -> bool:
        """Register or update an article in the warehouse (sendAPDReqV01)."""
        raise NotImplementedError

    def send_movement_order(
        self, order_number: str, positions: list[MovementLine]
    ) -> bool:
        """Send a movement order to the warehouse (sendJobsReqV01)."""
        raise NotImplementedError

    def get_completed_movements(self) -> list[MovementResult]:
        """Retrieve completed orders (readAllJobsReqV01, mode=1)."""
        raise NotImplementedError

    def get_all_orders(self) -> list[MovementResult]:
        """Retrieve all queued orders (readAllJobsReqV01, mode=0)."""
        raise NotImplementedError

    def get_inventory(self) -> list[StockRecord]:
        """Retrieve stock levels for all articles (readAllAMDReqV01)."""
        raise NotImplementedError

    def cancel_order(self, order_number: str) -> bool:
        """Cancel an order from the queue (deleteJobReqV01)."""
        raise NotImplementedError

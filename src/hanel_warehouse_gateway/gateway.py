"""Layer 3 — Public interface of the hanel_warehouse_gateway module.

HanelWarehouseGateway is the single point of contact for the calling system.
Completely hides SOAP, HTTP, and XML details.
"""

from __future__ import annotations

import logging

from .config import GatewayConfig
from .models import MovementLine, MovementResult, StockRecord
from .operations import SoapOperations
from .transport import SoapTransport

logger = logging.getLogger("hanel_warehouse_gateway")


class HanelWarehouseGateway:
    """Gateway for the Hanel automatic warehouse via SOAP.

    The module is not thread-safe. For concurrent calls,
    instantiate one client per thread.

    Example:
        config = GatewayConfig.from_env()
        gateway = HanelWarehouseGateway(config)
        gateway.register_article("1001", "M6 stainless bolt")
    """

    def __init__(self, config: GatewayConfig) -> None:
        self._config = config
        # Apply the configured verbosity to the module logger (ADR-006). The
        # caller still owns handlers; this only sets the effective level so that
        # DEBUG payload logging and ERROR failure logging behave as configured.
        logger.setLevel(getattr(logging, config.log_level, logging.INFO))
        self._transport = SoapTransport(config)
        self._operations = SoapOperations(config, self._transport)

    def register_article(
        self,
        article_number: str,
        article_name: str,
        batch_number: str | None = None,
    ) -> bool:
        """Register or update an article in the warehouse catalogue.

        Args:
            article_number: Unique article code (max 40 chars, alphanumeric only).
            article_name: Article description (max 40 chars).
            batch_number: Lot/batch number (max 40 chars). Only used when
                lot_management_enabled=True in GatewayConfig.

        Returns:
            True if the operation succeeded (returnValue == 0).
        """
        return self._operations.register_article(
            article_number, article_name, batch_number
        )

    def send_movement_order(
        self, order_number: str, positions: list[MovementLine]
    ) -> bool:
        """Send a movement order (pick or load) to the warehouse.

        Args:
            order_number: Unique order identifier (max 40 chars).
            positions: List of movement lines (at least one element).

        Returns:
            True if the operation succeeded (returnValue == 0).
        """
        return self._operations.send_movement_order(order_number, positions)

    def get_completed_movements(self) -> list[MovementResult]:
        """Retrieve completed orders from the warehouse.

        If actual_quantity < nominal_quantity in a line, stock was
        insufficient: handling is the caller's responsibility.
        """
        return self._operations.get_completed_movements()

    def get_all_orders(self) -> list[MovementResult]:
        """Retrieve all orders currently in the warehouse queue."""
        return self._operations.get_all_orders()

    def get_inventory(self) -> list[StockRecord]:
        """Retrieve stock levels for all articles in the warehouse.

        Only mechanism to detect manual movements performed at the warehouse console.
        """
        return self._operations.get_inventory()

    def cancel_order(self, order_number: str) -> bool:
        """Cancel an order from the warehouse queue.

        Applicable only to orders not yet processed (status 0).

        Args:
            order_number: Identifier of the order to cancel (max 40 chars).

        Returns:
            True if the operation succeeded (returnValue == 0).
        """
        return self._operations.cancel_order(order_number)

    def ping(self) -> bool:
        """Check whether the warehouse t-Server is reachable.

        Lightweight connectivity probe that sends a read-only request with a
        single attempt and a capped timeout, so an unreachable server fails
        fast instead of blocking for the full retry sequence. Returns True if
        the server responds with any HTTP reply, False if it cannot be reached
        over the network. Does not raise on an unreachable server.
        """
        return self._operations.ping()

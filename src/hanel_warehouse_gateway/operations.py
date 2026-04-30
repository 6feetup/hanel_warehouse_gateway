"""Layer 2 — SOAP Operations.

Maps each business operation to the corresponding SOAP call.
Serializes inputs, deserializes responses, validates fields.
Does not make HTTP calls directly: delegates to SoapTransport.
"""

from __future__ import annotations

import datetime
import logging

from . import _xml
from .config import GatewayConfig
from .exceptions import HanelGatewayApplicationError, HanelGatewayValidationError
from .models import MovementLine, MovementResult, StockRecord
from .transport import SoapTransport

logger = logging.getLogger(__name__)


def _validate_field_length(
    value: str, field: str, operation: str, config: GatewayConfig
) -> str:
    """Validate that a string field does not exceed 40 chars (ADR-008)."""
    if len(value) <= 40:
        return value
    if config.validation_truncate:
        logger.warning(
            "Field '%s' truncated to 40 chars in operation '%s'", field, operation
        )
        return value[:40]
    raise HanelGatewayValidationError(
        message=f"Field '{field}' exceeds the 40-character limit",
        operation=operation,
        detail=f"Length: {len(value)}, value: {value!r}",
        timestamp=datetime.datetime.utcnow().isoformat(),
        field=field,
        value=value,
    )


class SoapOperations:
    """Implements SOAP operations for the Hanel t-Server."""

    def __init__(self, config: GatewayConfig, transport: SoapTransport) -> None:
        self._config = config
        self._transport = transport

    def register_article(self, article_number: str, article_name: str) -> bool:
        """Register or update an article in the warehouse (sendAPDReqV01)."""
        operation = "sendAPDReqV01"

        article_number = _validate_field_length(
            article_number, "article_number", operation, self._config
        )
        article_name = _validate_field_length(
            article_name, "article_name", operation, self._config
        )

        logger.info(
            "register_article: initiating %s for article_number=%r",
            operation,
            article_number,
        )

        envelope = _xml.build_register_article_envelope(
            article_number,
            article_name,
            self._config.namespace_main,
            self._config.namespace_xsd,
        )

        raw = self._transport.post(envelope, operation)

        return_value = _xml.parse_return_value(
            raw, operation, self._config.namespace_xsd
        )
        if return_value != 0:
            raise HanelGatewayApplicationError(
                message=f"{operation} returned error code {return_value}",
                operation=operation,
                detail=f"returnValue={return_value}",
                timestamp=datetime.datetime.utcnow().isoformat(),
                return_value=return_value,
            )

        logger.info(
            "register_article: %s succeeded for article_number=%r",
            operation,
            article_number,
        )
        return True

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
        op = "deleteJobReqV01"
        if self._config.test_mode:
            order_number = f"{self._config.test_prefix}{order_number}"
        order_number = _validate_field_length(
            order_number, "job_number", op, self._config
        )
        envelope = _xml.build_cancel_order_envelope(
            job_number=order_number,
            namespace_main=self._config.namespace_main,
            namespace_xsd=self._config.namespace_xsd,
        )
        xml_response = self._transport.post(envelope, op)
        return_value = _xml.parse_return_value(
            xml_response, op, self._config.namespace_xsd
        )
        return return_value == 0

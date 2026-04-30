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
from .models import MovementLine, MovementLineResult, MovementResult, StockRecord
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
        operation = "sendJobsReqV01"

        if not positions:
            raise HanelGatewayValidationError(
                message="positions list must not be empty",
                operation=operation,
                detail="at least one MovementLine is required",
                timestamp=datetime.datetime.utcnow().isoformat(),
                field="positions",
                value="[]",
            )

        for i, pos in enumerate(positions):
            if pos.operation not in ("+", "-"):
                raise HanelGatewayValidationError(
                    message=f"invalid operation in position {i}: {pos.operation!r}",
                    operation=operation,
                    detail="operation must be '+' (pick) or '-' (load)",
                    timestamp=datetime.datetime.utcnow().isoformat(),
                    field=f"positions[{i}].operation",
                    value=str(pos.operation),
                )
            if pos.nominal_quantity <= 0:
                raise HanelGatewayValidationError(
                    message=f"nominal_quantity must be > 0 in position {i}",
                    operation=operation,
                    detail=f"got: {pos.nominal_quantity}",
                    timestamp=datetime.datetime.utcnow().isoformat(),
                    field=f"positions[{i}].nominal_quantity",
                    value=str(pos.nominal_quantity),
                )

        if self._config.test_mode:
            order_number = f"{self._config.test_prefix}{order_number}"

        job_number = _validate_field_length(
            order_number, "job_number", operation, self._config
        )

        positions_dicts: list[dict[str, object]] = []
        for i, pos in enumerate(positions):
            field_name = f"positions[{i}].article_number"
            article_number = _validate_field_length(
                pos.article_number, field_name, operation, self._config
            )
            positions_dicts.append({
                "article_number": article_number,
                "operation": pos.operation,
                "nominal_quantity": pos.nominal_quantity,
            })

        logger.info(
            "send_movement_order: initiating %s for job_number=%r with %d position(s)",
            operation,
            job_number,
            len(positions),
        )

        envelope = _xml.build_send_movement_order_envelope(
            job_number,
            positions_dicts,
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
            "send_movement_order: %s succeeded for job_number=%r",
            operation,
            job_number,
        )
        return True

    def get_completed_movements(self) -> list[MovementResult]:
        """Retrieve completed orders (readAllJobsReqV01, mode=1)."""
        operation = "readAllJobsReqV01"
        logger.info("get_completed_movements: initiating %s (mode=1)", operation)
        envelope = _xml.build_read_jobs_envelope(
            mode=1,
            namespace_main=self._config.namespace_main,
            namespace_xsd=self._config.namespace_xsd,
        )
        raw = self._transport.post(envelope, operation)
        raw_jobs = _xml.parse_movement_results(
            raw, operation, self._config.namespace_xsd
        )
        results = [
            MovementResult(
                job_number=str(job["job_number"]),
                job_priority=int(job["job_priority"]),  # type: ignore[call-overload]
                job_status=int(job["job_status"]),  # type: ignore[call-overload]
                job_date=str(job["job_date"]),
                job_time=str(job["job_time"]),
                positions=[
                    MovementLineResult(**pos)
                    for pos in job["positions"]  # type: ignore[attr-defined]
                ],
            )
            for job in raw_jobs
        ]
        logger.info(
            "get_completed_movements: %s returned %d results", operation, len(results)
        )
        return results

    def get_all_orders(self) -> list[MovementResult]:
        """Retrieve all queued orders (readAllJobsReqV01, mode=0)."""
        operation = "readAllJobsReqV01"
        logger.info("get_all_orders: initiating %s (mode=0)", operation)
        envelope = _xml.build_read_jobs_envelope(
            mode=0,
            namespace_main=self._config.namespace_main,
            namespace_xsd=self._config.namespace_xsd,
        )
        raw = self._transport.post(envelope, operation)
        raw_jobs = _xml.parse_movement_results(
            raw, operation, self._config.namespace_xsd
        )
        results = [
            MovementResult(
                job_number=str(job["job_number"]),
                job_priority=int(job["job_priority"]),  # type: ignore[call-overload]
                job_status=int(job["job_status"]),  # type: ignore[call-overload]
                job_date=str(job["job_date"]),
                job_time=str(job["job_time"]),
                positions=[
                    MovementLineResult(**pos)
                    for pos in job["positions"]  # type: ignore[attr-defined]
                ],
            )
            for job in raw_jobs
        ]
        logger.info(
            "get_all_orders: %s returned %d results", operation, len(results)
        )
        return results

    def get_inventory(self) -> list[StockRecord]:
        """Retrieve stock levels for all articles (readAllAMDReqV01)."""
        raise NotImplementedError

    def cancel_order(self, order_number: str) -> bool:
        """Cancel an order from the queue (deleteJobReqV01)."""
        operation = "deleteJobReqV01"
        if self._config.test_mode:
            order_number = f"{self._config.test_prefix}{order_number}"
        order_number = _validate_field_length(
            order_number, "job_number", operation, self._config
        )

        logger.info(
            "cancel_order: initiating %s for job_number=%r",
            operation,
            order_number,
        )

        envelope = _xml.build_cancel_order_envelope(
            job_number=order_number,
            namespace_main=self._config.namespace_main,
            namespace_xsd=self._config.namespace_xsd,
        )
        xml_response = self._transport.post(envelope, operation)
        return_value = _xml.parse_return_value(
            xml_response, operation, self._config.namespace_xsd
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
            "cancel_order: %s succeeded for job_number=%r",
            operation,
            order_number,
        )
        return True

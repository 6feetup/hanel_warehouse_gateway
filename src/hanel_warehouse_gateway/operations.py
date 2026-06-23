"""Layer 2 — SOAP Operations.

Maps each business operation to the corresponding SOAP call.
Serializes inputs, deserializes responses, validates fields.
Does not make HTTP calls directly: delegates to SoapTransport.
"""

from __future__ import annotations

import dataclasses
import datetime
import logging
import re

from . import _xml
from .config import GatewayConfig
from .exceptions import (
    HanelGatewayApplicationError,
    HanelGatewayError,
    HanelGatewayNetworkError,
    HanelGatewayValidationError,
)
from .models import MovementLine, MovementLineResult, MovementResult, StockRecord
from .transport import SoapTransport

logger = logging.getLogger("hanel_warehouse_gateway")

# Human-readable descriptions for known Hanel returnValue codes. The Hanel
# documentation does not publish an exhaustive list of application error codes;
# entries are added here as they get confirmed against the t-Server.
# Open question — complete from Hanel documentation when available.
_RETURN_CODE_DESCRIPTIONS: dict[int, str] = {
    -1: "Generic warehouse error (unspecified)",
}

# Upper bound on the per-attempt timeout used by ping(). A connectivity probe
# must answer quickly, so it caps the configured timeout instead of inheriting
# the (potentially large) value used for real operations.
_PING_TIMEOUT_SECONDS = 5


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


_ARTICLE_NUMBER_RE = re.compile(r"^[0-9]+$")


def _validate_article_number_charset(value: str, field: str, operation: str) -> None:
    """Reject article numbers that contain non-digit characters (ADR-008).

    The article number is a numeric code: the Hanel t-Server rejects article
    codes containing letters, hyphens, spaces, or symbols. This check always
    raises on violation, regardless of validation_truncate: an article number
    cannot be auto-corrected by stripping characters without changing the
    article identity. The empty string is also rejected (``+`` requires at
    least one digit).
    """
    if not _ARTICLE_NUMBER_RE.match(value):
        raise HanelGatewayValidationError(
            message=f"Field '{field}' must contain only digits (0-9)",
            operation=operation,
            detail=f"value: {value!r}",
            timestamp=datetime.datetime.utcnow().isoformat(),
            field=field,
            value=value,
        )


def _raise_application_error(
    operation: str,
    return_value: int,
    lot_hint: bool = False,
    raw: str | None = None,
) -> None:
    msg = f"{operation} returned error code {return_value}"
    description = _RETURN_CODE_DESCRIPTIONS.get(return_value)
    if description:
        msg += f": {description}"
    if lot_hint:
        msg += " (hint: verify lot_management_enabled configuration)"

    detail = f"returnValue={return_value}"
    if raw is not None:
        detail += f" | response={raw[:500]}"

    logger.error(
        "Application error in operation %s: returnValue=%d%s",
        operation,
        return_value,
        f" ({description})" if description else "",
    )
    raise HanelGatewayApplicationError(
        message=msg,
        operation=operation,
        detail=detail,
        timestamp=datetime.datetime.utcnow().isoformat(),
        return_value=return_value,
    )


class SoapOperations:
    """Implements SOAP operations for the Hanel t-Server."""

    def __init__(self, config: GatewayConfig, transport: SoapTransport) -> None:
        self._config = config
        self._transport = transport

    def register_article(
        self,
        article_number: str,
        article_name: str,
        batch_number: str | None = None,
    ) -> bool:
        """Register or update an article in the warehouse.

        Uses sendAPDReqV03 when lot_management_enabled=True, sendAPDReqV01 otherwise.
        """
        lot = self._config.lot_management_enabled
        operation = "sendAPDReqV03" if lot else "sendAPDReqV01"

        # Charset check on the caller-supplied value, before the test_prefix is
        # prepended: the prefix is module-controlled (e.g. "TEST_") and may
        # legitimately contain non-digit characters.
        _validate_article_number_charset(article_number, "article_number", operation)

        if self._config.test_mode:
            article_number = f"{self._config.test_prefix}{article_number}"

        article_number = _validate_field_length(
            article_number, "article_number", operation, self._config
        )
        article_name = _validate_field_length(
            article_name, "article_name", operation, self._config
        )
        if lot and batch_number is not None:
            batch_number = _validate_field_length(
                batch_number, "batch_number", operation, self._config
            )

        if batch_number is not None:
            logger.info(
                "register_article: initiating %s for article_number=%r batch_number=%r",
                operation,
                article_number,
                batch_number,
            )
        else:
            logger.info(
                "register_article: initiating %s for article_number=%r",
                operation,
                article_number,
            )

        if lot:
            envelope = _xml.build_register_article_envelope_v03(
                article_number,
                article_name,
                batch_number,
                self._config.namespace_main,
                self._config.namespace_xsd,
            )
        else:
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
            _raise_application_error(operation, return_value, lot, raw)

        logger.info(
            "register_article: %s succeeded for article_number=%r",
            operation,
            article_number,
        )
        return True

    def send_movement_order(
        self, order_number: str, positions: list[MovementLine]
    ) -> bool:
        """Send a movement order to the warehouse.

        Uses sendJobsV02 when lot_management_enabled=True, sendJobsReqV01 otherwise.
        """
        lot = self._config.lot_management_enabled
        operation = "sendJobsV02" if lot else "sendJobsReqV01"

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
            # The warehouse only accepts integer quantities. Reject bools and any
            # value carrying a fractional part (e.g. 3.5); whole floats like 5.0
            # are tolerated and normalised to int when the envelope is built.
            # Widen to object so the runtime type checks narrow correctly even
            # though the field is annotated int (a caller may pass a float).
            quantity: object = pos.nominal_quantity
            if isinstance(quantity, bool) or (
                isinstance(quantity, float) and not quantity.is_integer()
            ):
                raise HanelGatewayValidationError(
                    message=f"nominal_quantity must be an integer in position {i}",
                    operation=operation,
                    detail=f"got: {pos.nominal_quantity!r}",
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
            # Charset check on the caller-supplied value, before the test_prefix
            # is prepended: mirrors register_article so a test article registered
            # as e.g. "TEST_123" is referenced by the same id in the order line.
            _validate_article_number_charset(pos.article_number, field_name, operation)
            position_article_number = pos.article_number
            if self._config.test_mode:
                position_article_number = (
                    f"{self._config.test_prefix}{position_article_number}"
                )
            article_number = _validate_field_length(
                position_article_number, field_name, operation, self._config
            )
            pos_dict: dict[str, object] = {
                "article_number": article_number,
                "operation": pos.operation,
                "nominal_quantity": int(pos.nominal_quantity),
            }
            if lot:
                pos_dict["batch_number"] = pos.batch_number
            positions_dicts.append(pos_dict)

        logger.info(
            "send_movement_order: initiating %s for job_number=%r with %d position(s)",
            operation,
            job_number,
            len(positions),
        )

        if lot:
            envelope = _xml.build_send_movement_order_envelope_v02(
                job_number,
                positions_dicts,
                self._config.namespace_main,
                self._config.namespace_xsd,
            )
        else:
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
            _raise_application_error(operation, return_value, lot, raw)

        logger.info(
            "send_movement_order: %s succeeded for job_number=%r",
            operation,
            job_number,
        )
        return True

    def get_completed_movements(self) -> list[MovementResult]:
        """Retrieve completed orders.

        Uses readAllJobsV02 when lot_management_enabled=True,
        readAllJobsReqV01 otherwise.
        """
        lot = self._config.lot_management_enabled
        operation = "readAllJobsV02" if lot else "readAllJobsReqV01"
        logger.info("get_completed_movements: initiating %s (mode=1)", operation)
        if lot:
            envelope = _xml.build_read_jobs_envelope_v02(
                mode=1,
                namespace_main=self._config.namespace_main,
                namespace_xsd=self._config.namespace_xsd,
            )
        else:
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
        """Retrieve all queued orders.

        Uses readAllJobsV02 when lot_management_enabled=True,
        readAllJobsReqV01 otherwise.
        """
        lot = self._config.lot_management_enabled
        operation = "readAllJobsV02" if lot else "readAllJobsReqV01"
        logger.info("get_all_orders: initiating %s (mode=0)", operation)
        if lot:
            envelope = _xml.build_read_jobs_envelope_v02(
                mode=0,
                namespace_main=self._config.namespace_main,
                namespace_xsd=self._config.namespace_xsd,
            )
        else:
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
        """Retrieve stock levels for all articles.

        Uses readAllAMDV04 when lot_management_enabled=True, readAllAMDReqV01 otherwise.
        """
        lot = self._config.lot_management_enabled
        operation = "readAllAMDV04" if lot else "readAllAMDReqV01"
        logger.info("get_inventory: initiating %s", operation)
        if lot:
            envelope = _xml.build_get_inventory_envelope_v04(
                self._config.namespace_main
            )
        else:
            envelope = _xml.build_get_inventory_envelope(self._config.namespace_main)
        raw = self._transport.post(envelope, operation)
        raw_records = _xml.parse_stock_records(
            raw, operation, self._config.namespace_xsd
        )
        results = [
            StockRecord(
                article_number=str(r["article_number"]),
                article_name=str(r["article_name"]),
                lift_number=int(r["lift_number"]),  # type: ignore[call-overload]
                shelf_number=int(r["shelf_number"]),  # type: ignore[call-overload]
                compartment_number=int(r["compartment_number"]),  # type: ignore[call-overload]
                compartment_depth_number=int(r["compartment_depth_number"]),  # type: ignore[call-overload]
                container_size=int(r["container_size"]),  # type: ignore[call-overload]
                fifo=int(r["fifo"]),  # type: ignore[call-overload]
                inventory_at_storage_location=float(r["inventory_at_storage_location"]),  # type: ignore[arg-type]
                minimum_inventory=float(r["minimum_inventory"]),  # type: ignore[arg-type]
                batch_number=r["batch_number"],  # type: ignore[arg-type]
                h10_special_field=r["h10_special_field"],  # type: ignore[arg-type]
            )
            for r in raw_records
        ]
        logger.info("get_inventory: %s returned %d records", operation, len(results))
        return results

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
            _raise_application_error(operation, return_value, raw=xml_response)

        logger.info(
            "cancel_order: %s succeeded for job_number=%r",
            operation,
            order_number,
        )
        return True

    def ping(self) -> bool:
        """Check whether the warehouse t-Server is reachable.

        Health-check that sends the lightweight read-only readAllJobs request
        (no dedicated echo/ping operation exists on the Hanel t-Server). Any
        HTTP reply (including a SOAP fault or a non-2xx status) proves the
        server is alive; only a network failure (connection refused / timeout)
        is treated as unreachable.

        Unlike the regular operations, the probe must answer quickly, so it
        runs against a derived config with a single attempt and a capped
        timeout: otherwise an unreachable server would block for the full
        retry sequence (retry_attempts x timeout_seconds plus the delays
        between attempts). The response body is intentionally not parsed —
        reachability only depends on whether an HTTP reply came back at all.

        Returns:
            True if the server responded with any HTTP reply; False if it
            could not be reached over the network.
        """
        # Copy the config but collapse retries to one and cap the timeout, so a
        # dead server fails fast instead of inheriting the operational settings.
        probe_config = dataclasses.replace(
            self._config,
            retry_attempts=1,
            timeout_seconds=min(self._config.timeout_seconds, _PING_TIMEOUT_SECONDS),
        )
        # Short-lived transport bound to the probe config; the instance's own
        # transport (and its operational timeout/retry) is left untouched.
        probe_transport = SoapTransport(probe_config)
        envelope = _xml.build_read_jobs_envelope(
            mode=0,
            namespace_main=self._config.namespace_main,
            namespace_xsd=self._config.namespace_xsd,
        )
        logger.info("ping: probing connectivity via readAllJobs")
        try:
            probe_transport.post(envelope, "ping")
        except HanelGatewayNetworkError:
            # No HTTP reply reached us: the server is unreachable.
            logger.warning("ping: warehouse unreachable (network error)")
            return False
        except HanelGatewayError:
            # The server replied (HTTP error, SOAP fault, ...): it is alive even
            # though this particular response was not a clean success.
            logger.info("ping: warehouse reachable (non-success response)")
            return True
        logger.info("ping: warehouse reachable")
        return True

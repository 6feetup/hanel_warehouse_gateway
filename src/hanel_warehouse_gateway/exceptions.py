"""Exception hierarchy for hanel_warehouse_gateway."""

from __future__ import annotations


class HanelGatewayError(Exception):
    """Base exception for all module errors."""

    def __init__(
        self,
        message: str,
        operation: str,
        detail: str,
        timestamp: str,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.operation = operation
        self.detail = detail
        self.timestamp = timestamp

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"operation={self.operation!r}, "
            f"timestamp={self.timestamp!r})"
        )


class HanelGatewayNetworkError(HanelGatewayError):
    """Network error after all retry attempts are exhausted."""


class HanelGatewayHttpError(HanelGatewayError):
    """HTTP response with a non-2xx status code."""

    def __init__(
        self,
        message: str,
        operation: str,
        detail: str,
        timestamp: str,
        http_status: int,
    ) -> None:
        super().__init__(message, operation, detail, timestamp)
        self.http_status = http_status


class HanelGatewaySoapFaultError(HanelGatewayError):
    """SOAP fault present in the response envelope."""

    def __init__(
        self,
        message: str,
        operation: str,
        detail: str,
        timestamp: str,
        fault_string: str,
        fault_code: str,
    ) -> None:
        super().__init__(message, operation, detail, timestamp)
        self.fault_string = fault_string
        self.fault_code = fault_code


class HanelGatewayApplicationError(HanelGatewayError):
    """returnValue != 0 in the application response."""

    def __init__(
        self,
        message: str,
        operation: str,
        detail: str,
        timestamp: str,
        return_value: int,
    ) -> None:
        super().__init__(message, operation, detail, timestamp)
        self.return_value = return_value


class HanelGatewayParseError(HanelGatewayError):
    """Response could not be parsed (malformed XML or missing expected element)."""


class HanelGatewayValidationError(HanelGatewayError):
    """Invalid input detected before sending. No HTTP call is made."""

    def __init__(
        self,
        message: str,
        operation: str,
        detail: str,
        timestamp: str,
        field: str,
        value: str,
    ) -> None:
        super().__init__(message, operation, detail, timestamp)
        self.field = field
        self.value = value

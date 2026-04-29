"""Gerarchia di eccezioni per hanel_warehouse_gateway."""

from __future__ import annotations


class HanelGatewayError(Exception):
    """Eccezione base per tutti gli errori del modulo."""

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
    """Errore di rete dopo esaurimento di tutti i tentativi di retry."""


class HanelGatewayHttpError(HanelGatewayError):
    """Risposta HTTP con status code non 2xx."""

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
    """Fault SOAP presente nell'envelope di risposta."""

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
    """returnValue != 0 nella risposta applicativa."""

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


class HanelGatewayValidationError(HanelGatewayError):
    """Input non valido rilevato prima dell'invio. Nessuna chiamata HTTP."""

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

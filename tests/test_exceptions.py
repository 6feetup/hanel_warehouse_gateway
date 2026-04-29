"""Test per la gerarchia di eccezioni di hanel_warehouse_gateway."""

from __future__ import annotations

import pytest

from hanel_warehouse_gateway import (
    HanelGatewayApplicationError,
    HanelGatewayError,
    HanelGatewayHttpError,
    HanelGatewayNetworkError,
    HanelGatewaySoapFaultError,
    HanelGatewayValidationError,
)

_BASE = {
    "message": "test error",
    "operation": "test_op",
    "detail": "some detail",
    "timestamp": "2024-01-01T00:00:00",
}


class TestHanelGatewayError:
    def test_is_exception(self) -> None:
        assert isinstance(HanelGatewayError(**_BASE), Exception)

    def test_attributes(self) -> None:
        exc = HanelGatewayError(**_BASE)
        assert exc.message == "test error"
        assert exc.operation == "test_op"
        assert exc.detail == "some detail"
        assert exc.timestamp == "2024-01-01T00:00:00"

    def test_str_contains_message(self) -> None:
        assert "test error" in str(HanelGatewayError(**_BASE))


class TestSubclassHierarchy:
    def test_network_error_is_base(self) -> None:
        assert isinstance(HanelGatewayNetworkError(**_BASE), HanelGatewayError)

    def test_http_error_attributes(self) -> None:
        exc = HanelGatewayHttpError(**_BASE, http_status=503)
        assert isinstance(exc, HanelGatewayError)
        assert exc.http_status == 503

    def test_soap_fault_error_attributes(self) -> None:
        exc = HanelGatewaySoapFaultError(
            **_BASE, fault_string="Server error", fault_code="env:Server"
        )
        assert isinstance(exc, HanelGatewayError)
        assert exc.fault_string == "Server error"
        assert exc.fault_code == "env:Server"

    def test_application_error_attributes(self) -> None:
        exc = HanelGatewayApplicationError(**_BASE, return_value=5)
        assert isinstance(exc, HanelGatewayError)
        assert exc.return_value == 5

    def test_validation_error_attributes(self) -> None:
        exc = HanelGatewayValidationError(
            **_BASE, field="article_number", value="X" * 50
        )
        assert isinstance(exc, HanelGatewayError)
        assert exc.field == "article_number"

    def test_catch_by_base(self) -> None:
        with pytest.raises(HanelGatewayError):
            raise HanelGatewayNetworkError(**_BASE)

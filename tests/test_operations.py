"""Tests for SoapOperations.register_article (Layer 2)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from hanel_warehouse_gateway import GatewayConfig
from hanel_warehouse_gateway.exceptions import (
    HanelGatewayApplicationError,
    HanelGatewaySoapFaultError,
    HanelGatewayValidationError,
)
from hanel_warehouse_gateway.operations import SoapOperations

_FIXTURES = Path(__file__).parent / "fixtures"


def _make_operations(
    mock_response: str = "",
    **config_kwargs: object,
) -> tuple[SoapOperations, MagicMock]:
    config = GatewayConfig(
        endpoint_url="http://mock/",
        **config_kwargs,  # type: ignore[arg-type]
    )
    transport = MagicMock()
    transport.post.return_value = mock_response
    return SoapOperations(config, transport), transport


class TestRegisterArticle:
    def test_success_returns_true(self) -> None:
        xml = (_FIXTURES / "sendAPDReqV01_success.xml").read_text()
        ops, transport = _make_operations(xml)
        result = ops.register_article("ART001", "Bolt M6")
        assert result is True
        transport.post.assert_called_once()

    def test_calls_correct_soap_operation(self) -> None:
        xml = (_FIXTURES / "sendAPDReqV01_success.xml").read_text()
        ops, transport = _make_operations(xml)
        ops.register_article("ART001", "Bolt M6")
        _, call_operation = transport.post.call_args[0]
        assert call_operation == "sendAPDReqV01"

    def test_envelope_contains_article_number(self) -> None:
        xml = (_FIXTURES / "sendAPDReqV01_success.xml").read_text()
        ops, transport = _make_operations(xml)
        ops.register_article("ART001", "Bolt M6")
        envelope, _ = transport.post.call_args[0]
        assert "ART001" in envelope

    def test_envelope_contains_article_name(self) -> None:
        xml = (_FIXTURES / "sendAPDReqV01_success.xml").read_text()
        ops, transport = _make_operations(xml)
        ops.register_article("ART001", "Bolt M6")
        envelope, _ = transport.post.call_args[0]
        assert "Bolt M6" in envelope

    def test_application_error_raises(self) -> None:
        xml = (_FIXTURES / "sendAPDReqV01_error.xml").read_text()
        ops, _ = _make_operations(xml)
        with pytest.raises(HanelGatewayApplicationError) as exc_info:
            ops.register_article("ART001", "Bolt M6")
        assert exc_info.value.return_value == 1
        assert exc_info.value.operation == "sendAPDReqV01"

    def test_soap_fault_raises(self) -> None:
        xml = (_FIXTURES / "soap_fault.xml").read_text()
        ops, _ = _make_operations(xml)
        with pytest.raises(HanelGatewaySoapFaultError) as exc_info:
            ops.register_article("ART001", "Bolt M6")
        assert exc_info.value.fault_code == "soapenv:Server"
        assert "Internal error" in exc_info.value.fault_string

    def test_article_number_too_long_raises_validation_error(self) -> None:
        ops, transport = _make_operations()
        long_number = "A" * 41
        with pytest.raises(HanelGatewayValidationError) as exc_info:
            ops.register_article(long_number, "Valid Name")
        assert exc_info.value.field == "article_number"
        transport.post.assert_not_called()

    def test_article_name_too_long_raises_validation_error(self) -> None:
        ops, transport = _make_operations()
        long_name = "N" * 41
        with pytest.raises(HanelGatewayValidationError) as exc_info:
            ops.register_article("ART001", long_name)
        assert exc_info.value.field == "article_name"
        transport.post.assert_not_called()

    def test_article_number_exactly_40_chars_is_valid(self) -> None:
        xml = (_FIXTURES / "sendAPDReqV01_success.xml").read_text()
        ops, transport = _make_operations(xml)
        ops.register_article("A" * 40, "Valid Name")
        transport.post.assert_called_once()

    def test_article_name_exactly_40_chars_is_valid(self) -> None:
        xml = (_FIXTURES / "sendAPDReqV01_success.xml").read_text()
        ops, transport = _make_operations(xml)
        ops.register_article("ART001", "N" * 40)
        transport.post.assert_called_once()

    def test_validation_truncate_article_number(self) -> None:
        xml = (_FIXTURES / "sendAPDReqV01_success.xml").read_text()
        ops, transport = _make_operations(xml, validation_truncate=True)
        ops.register_article("A" * 41, "Valid Name")
        envelope, _ = transport.post.call_args[0]
        assert "A" * 40 in envelope
        assert "A" * 41 not in envelope

    def test_validation_truncate_article_name(self) -> None:
        xml = (_FIXTURES / "sendAPDReqV01_success.xml").read_text()
        ops, transport = _make_operations(xml, validation_truncate=True)
        ops.register_article("ART001", "N" * 41)
        envelope, _ = transport.post.call_args[0]
        assert "N" * 40 in envelope
        assert "N" * 41 not in envelope

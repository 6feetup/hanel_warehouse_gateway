"""Tests for SoapOperations (Layer 2)."""

from __future__ import annotations

import pathlib
from unittest.mock import MagicMock

import pytest
import responses as responses_lib

from hanel_warehouse_gateway import GatewayConfig
from hanel_warehouse_gateway.exceptions import (
    HanelGatewayApplicationError,
    HanelGatewaySoapFaultError,
    HanelGatewayValidationError,
)
from hanel_warehouse_gateway.operations import SoapOperations
from hanel_warehouse_gateway.transport import SoapTransport

_ENDPOINT = "http://mock-hanel.test/HanelService"
_FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def _fixture(name: str) -> str:
    return (_FIXTURES / name).read_text(encoding="utf-8")


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


def _config(**overrides: object) -> GatewayConfig:
    defaults: dict[str, object] = {
        "endpoint_url": _ENDPOINT,
        "retry_attempts": 1,
        "retry_delay_seconds": 0.0,
    }
    defaults.update(overrides)
    return GatewayConfig(**defaults)  # type: ignore[arg-type]


def _ops(config: GatewayConfig) -> SoapOperations:
    return SoapOperations(config, SoapTransport(config))


class TestRegisterArticle:
    def test_success_returns_true(self) -> None:
        xml = _fixture("sendAPDReqV01_success.xml")
        ops, transport = _make_operations(xml)
        result = ops.register_article("ART001", "Bolt M6")
        assert result is True
        transport.post.assert_called_once()

    def test_calls_correct_soap_operation(self) -> None:
        xml = _fixture("sendAPDReqV01_success.xml")
        ops, transport = _make_operations(xml)
        ops.register_article("ART001", "Bolt M6")
        _, call_operation = transport.post.call_args[0]
        assert call_operation == "sendAPDReqV01"

    def test_envelope_contains_article_number(self) -> None:
        xml = _fixture("sendAPDReqV01_success.xml")
        ops, transport = _make_operations(xml)
        ops.register_article("ART001", "Bolt M6")
        envelope, _ = transport.post.call_args[0]
        assert "ART001" in envelope

    def test_envelope_contains_article_name(self) -> None:
        xml = _fixture("sendAPDReqV01_success.xml")
        ops, transport = _make_operations(xml)
        ops.register_article("ART001", "Bolt M6")
        envelope, _ = transport.post.call_args[0]
        assert "Bolt M6" in envelope

    def test_application_error_raises(self) -> None:
        xml = _fixture("sendAPDReqV01_error.xml")
        ops, _ = _make_operations(xml)
        with pytest.raises(HanelGatewayApplicationError) as exc_info:
            ops.register_article("ART001", "Bolt M6")
        assert exc_info.value.return_value == 1
        assert exc_info.value.operation == "sendAPDReqV01"

    def test_soap_fault_raises(self) -> None:
        xml = _fixture("soap_fault.xml")
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
        xml = _fixture("sendAPDReqV01_success.xml")
        ops, transport = _make_operations(xml)
        ops.register_article("A" * 40, "Valid Name")
        transport.post.assert_called_once()

    def test_article_name_exactly_40_chars_is_valid(self) -> None:
        xml = _fixture("sendAPDReqV01_success.xml")
        ops, transport = _make_operations(xml)
        ops.register_article("ART001", "N" * 40)
        transport.post.assert_called_once()

    def test_validation_truncate_article_number(self) -> None:
        xml = _fixture("sendAPDReqV01_success.xml")
        ops, transport = _make_operations(xml, validation_truncate=True)
        ops.register_article("A" * 41, "Valid Name")
        envelope, _ = transport.post.call_args[0]
        assert "A" * 40 in envelope
        assert "A" * 41 not in envelope

    def test_validation_truncate_article_name(self) -> None:
        xml = _fixture("sendAPDReqV01_success.xml")
        ops, transport = _make_operations(xml, validation_truncate=True)
        ops.register_article("ART001", "N" * 41)
        envelope, _ = transport.post.call_args[0]
        assert "N" * 40 in envelope
        assert "N" * 41 not in envelope


class TestCancelOrder:
    @responses_lib.activate
    def test_returns_true_on_success(self) -> None:
        responses_lib.add(
            responses_lib.POST,
            _ENDPOINT,
            body=_fixture("response_delete_job_ok.xml"),
            status=200,
        )
        result = _ops(_config()).cancel_order("ORD-001")
        assert result is True

    @responses_lib.activate
    def test_returns_false_on_failure(self) -> None:
        responses_lib.add(
            responses_lib.POST,
            _ENDPOINT,
            body=_fixture("response_delete_job_error.xml"),
            status=200,
        )
        result = _ops(_config()).cancel_order("ORD-003")
        assert result is False

    @responses_lib.activate
    def test_envelope_contains_order_number(self) -> None:
        responses_lib.add(
            responses_lib.POST,
            _ENDPOINT,
            body=_fixture("response_delete_job_ok.xml"),
            status=200,
        )
        _ops(_config()).cancel_order("ORD-001")
        payload = responses_lib.calls[0].request.body.decode("utf-8")
        assert "<xsd:jobNumber>ORD-001</xsd:jobNumber>" in payload

    @responses_lib.activate
    def test_test_mode_prepends_prefix(self) -> None:
        responses_lib.add(
            responses_lib.POST,
            _ENDPOINT,
            body=_fixture("response_delete_job_ok.xml"),
            status=200,
        )
        _ops(_config(test_mode=True, test_prefix="TEST_")).cancel_order("ORD-001")
        payload = responses_lib.calls[0].request.body.decode("utf-8")
        assert "<xsd:jobNumber>TEST_ORD-001</xsd:jobNumber>" in payload

    def test_order_number_over_40_chars_raises_validation_error(self) -> None:
        with pytest.raises(HanelGatewayValidationError) as exc_info:
            _ops(_config()).cancel_order("X" * 41)
        exc = exc_info.value
        assert exc.field == "job_number"
        assert exc.operation == "deleteJobReqV01"

    def test_test_mode_prefix_counts_toward_length_limit(self) -> None:
        with pytest.raises(HanelGatewayValidationError):
            _ops(_config(test_mode=True, test_prefix="TEST_")).cancel_order("X" * 36)

    @responses_lib.activate
    def test_validation_truncate_truncates_and_sends(self) -> None:
        responses_lib.add(
            responses_lib.POST,
            _ENDPOINT,
            body=_fixture("response_delete_job_ok.xml"),
            status=200,
        )
        result = _ops(_config(validation_truncate=True)).cancel_order("X" * 41)
        assert result is True
        payload = responses_lib.calls[0].request.body.decode("utf-8")
        assert "X" * 40 in payload
        assert "X" * 41 not in payload


from hanel_warehouse_gateway.models import MovementLine  # noqa: E402

_SUCCESS_XML = _fixture("send_movement_order_success.xml")

_ONE_LINE = [
    MovementLine(article_number="ART-001", operation="+", nominal_quantity=5.0)
]


class TestSendMovementOrder:
    def test_success_returns_true(self) -> None:
        ops, transport = _make_operations(_SUCCESS_XML)
        assert ops.send_movement_order("JOB-1", _ONE_LINE) is True
        transport.post.assert_called_once()

    def test_calls_correct_soap_operation(self) -> None:
        ops, transport = _make_operations(_SUCCESS_XML)
        ops.send_movement_order("JOB-1", _ONE_LINE)
        _, call_operation = transport.post.call_args[0]
        assert call_operation == "sendJobsReqV01"

    def test_envelope_contains_job_number(self) -> None:
        ops, transport = _make_operations(_SUCCESS_XML)
        ops.send_movement_order("JOB-42", _ONE_LINE)
        envelope, _ = transport.post.call_args[0]
        assert "JOB-42" in envelope

    def test_envelope_contains_article_number(self) -> None:
        ops, transport = _make_operations(_SUCCESS_XML)
        ops.send_movement_order("JOB-1", _ONE_LINE)
        envelope, _ = transport.post.call_args[0]
        assert "ART-001" in envelope

    def test_envelope_contains_operation_and_quantity(self) -> None:
        ops, transport = _make_operations(_SUCCESS_XML)
        ops.send_movement_order("JOB-1", _ONE_LINE)
        envelope, _ = transport.post.call_args[0]
        assert "<xsd:operation>+</xsd:operation>" in envelope
        assert "5.0" in envelope

    def test_multiple_positions_all_in_envelope(self) -> None:
        positions = [
            MovementLine("ART-001", "+", 10.0),
            MovementLine("ART-002", "-", 3.5),
        ]
        ops, transport = _make_operations(_SUCCESS_XML)
        ops.send_movement_order("JOB-MULTI", positions)
        envelope, _ = transport.post.call_args[0]
        assert "ART-001" in envelope
        assert "ART-002" in envelope

    def test_test_mode_prepends_prefix(self) -> None:
        ops, transport = _make_operations(
            _SUCCESS_XML, test_mode=True, test_prefix="TEST_"
        )
        ops.send_movement_order("JOB-1", _ONE_LINE)
        envelope, _ = transport.post.call_args[0]
        assert "TEST_JOB-1" in envelope
        assert "<xsd:jobNumber>TEST_JOB-1</xsd:jobNumber>" in envelope

    def test_test_mode_false_no_prefix(self) -> None:
        ops, transport = _make_operations(_SUCCESS_XML, test_mode=False)
        ops.send_movement_order("JOB-1", _ONE_LINE)
        envelope, _ = transport.post.call_args[0]
        assert "<xsd:jobNumber>JOB-1</xsd:jobNumber>" in envelope

    def test_empty_positions_raises_validation_error(self) -> None:
        ops, transport = _make_operations()
        with pytest.raises(HanelGatewayValidationError) as exc_info:
            ops.send_movement_order("JOB-1", [])
        assert exc_info.value.field == "positions"
        transport.post.assert_not_called()

    def test_invalid_operation_raises_validation_error(self) -> None:
        ops, transport = _make_operations()
        bad = [MovementLine("ART-001", "X", 1.0)]
        with pytest.raises(HanelGatewayValidationError) as exc_info:
            ops.send_movement_order("JOB-1", bad)
        assert "operation" in exc_info.value.field
        transport.post.assert_not_called()

    def test_zero_quantity_raises_validation_error(self) -> None:
        ops, transport = _make_operations()
        bad = [
            MovementLine(article_number="ART-001", operation="+", nominal_quantity=0.0)
        ]
        with pytest.raises(HanelGatewayValidationError) as exc_info:
            ops.send_movement_order("JOB-1", bad)
        assert "nominal_quantity" in exc_info.value.field
        transport.post.assert_not_called()

    def test_negative_quantity_raises_validation_error(self) -> None:
        ops, transport = _make_operations()
        bad = [
            MovementLine(article_number="ART-001", operation="+", nominal_quantity=-1.0)
        ]
        with pytest.raises(HanelGatewayValidationError) as exc_info:
            ops.send_movement_order("JOB-1", bad)
        assert "nominal_quantity" in exc_info.value.field
        transport.post.assert_not_called()

    def test_order_number_too_long_raises_validation_error(self) -> None:
        ops, transport = _make_operations()
        with pytest.raises(HanelGatewayValidationError) as exc_info:
            ops.send_movement_order("J" * 41, _ONE_LINE)
        assert exc_info.value.field == "job_number"
        transport.post.assert_not_called()

    def test_article_number_too_long_raises_validation_error(self) -> None:
        ops, transport = _make_operations()
        bad = [
            MovementLine(article_number="A" * 41, operation="+", nominal_quantity=1.0)
        ]
        with pytest.raises(HanelGatewayValidationError) as exc_info:
            ops.send_movement_order("JOB-1", bad)
        assert "article_number" in exc_info.value.field
        transport.post.assert_not_called()

    def test_order_number_exactly_40_chars_is_valid(self) -> None:
        ops, transport = _make_operations(_SUCCESS_XML)
        ops.send_movement_order("J" * 40, _ONE_LINE)
        transport.post.assert_called_once()

    def test_validation_truncate_order_number(self) -> None:
        ops, transport = _make_operations(_SUCCESS_XML, validation_truncate=True)
        ops.send_movement_order("J" * 41, _ONE_LINE)
        envelope, _ = transport.post.call_args[0]
        assert "J" * 40 in envelope
        assert "J" * 41 not in envelope

    def test_test_mode_prefix_counts_toward_length_limit(self) -> None:
        ops, transport = _make_operations(test_mode=True, test_prefix="TEST_")
        with pytest.raises(HanelGatewayValidationError):
            ops.send_movement_order("J" * 36, _ONE_LINE)
        transport.post.assert_not_called()

    def test_nonzero_return_value_raises_application_error(self) -> None:
        error_xml = _fixture("sendAPDReqV01_error.xml")
        ops, _ = _make_operations(error_xml)
        with pytest.raises(HanelGatewayApplicationError) as exc_info:
            ops.send_movement_order("JOB-1", _ONE_LINE)
        assert exc_info.value.return_value == 1
        assert exc_info.value.operation == "sendJobsReqV01"

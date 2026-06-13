"""Tests for SoapOperations (Layer 2)."""

from __future__ import annotations

import pathlib
from unittest.mock import MagicMock

import pytest
import responses as responses_lib

from hanel_warehouse_gateway import GatewayConfig
from hanel_warehouse_gateway.exceptions import (
    HanelGatewayApplicationError,
    HanelGatewayParseError,
    HanelGatewaySoapFaultError,
    HanelGatewayValidationError,
)
from hanel_warehouse_gateway.models import (
    MovementLine,
    MovementLineResult,
    MovementResult,
    StockRecord,
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
        result = ops.register_article("1001", "Bolt M6")
        assert result is True
        transport.post.assert_called_once()

    def test_calls_correct_soap_operation(self) -> None:
        xml = _fixture("sendAPDReqV01_success.xml")
        ops, transport = _make_operations(xml)
        ops.register_article("1001", "Bolt M6")
        _, call_operation = transport.post.call_args[0]
        assert call_operation == "sendAPDReqV01"

    def test_envelope_contains_article_number(self) -> None:
        xml = _fixture("sendAPDReqV01_success.xml")
        ops, transport = _make_operations(xml)
        ops.register_article("1001", "Bolt M6")
        envelope, _ = transport.post.call_args[0]
        assert "1001" in envelope

    def test_envelope_contains_article_name(self) -> None:
        xml = _fixture("sendAPDReqV01_success.xml")
        ops, transport = _make_operations(xml)
        ops.register_article("1001", "Bolt M6")
        envelope, _ = transport.post.call_args[0]
        assert "Bolt M6" in envelope

    def test_application_error_raises(self) -> None:
        xml = _fixture("sendAPDReqV01_error.xml")
        ops, _ = _make_operations(xml)
        with pytest.raises(HanelGatewayApplicationError) as exc_info:
            ops.register_article("1001", "Bolt M6")
        assert exc_info.value.return_value == 1
        assert exc_info.value.operation == "sendAPDReqV01"

    def test_application_error_includes_response_snippet(self) -> None:
        xml = _fixture("sendAPDReqV01_error.xml")
        ops, _ = _make_operations(xml)
        with pytest.raises(HanelGatewayApplicationError) as exc_info:
            ops.register_article("1001", "Bolt M6")
        assert "returnValue=1" in exc_info.value.detail
        assert "response=" in exc_info.value.detail

    def test_application_error_logs_error(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        xml = _fixture("sendAPDReqV01_error.xml")
        ops, _ = _make_operations(xml)
        with caplog.at_level("ERROR", logger="hanel_warehouse_gateway"):
            with pytest.raises(HanelGatewayApplicationError):
                ops.register_article("1001", "Bolt M6")
        assert any(
            "Application error" in r.message and r.levelname == "ERROR"
            for r in caplog.records
        )

    def test_soap_fault_raises(self) -> None:
        xml = _fixture("soap_fault.xml")
        ops, _ = _make_operations(xml)
        with pytest.raises(HanelGatewaySoapFaultError) as exc_info:
            ops.register_article("1001", "Bolt M6")
        assert exc_info.value.fault_code == "soapenv:Server"
        assert "Internal error" in exc_info.value.fault_string

    def test_article_number_too_long_raises_validation_error(self) -> None:
        ops, transport = _make_operations()
        long_number = "1" * 41
        with pytest.raises(HanelGatewayValidationError) as exc_info:
            ops.register_article(long_number, "Valid Name")
        assert exc_info.value.field == "article_number"
        transport.post.assert_not_called()

    def test_article_name_too_long_raises_validation_error(self) -> None:
        ops, transport = _make_operations()
        long_name = "N" * 41
        with pytest.raises(HanelGatewayValidationError) as exc_info:
            ops.register_article("1001", long_name)
        assert exc_info.value.field == "article_name"
        transport.post.assert_not_called()

    def test_article_number_exactly_40_chars_is_valid(self) -> None:
        xml = _fixture("sendAPDReqV01_success.xml")
        ops, transport = _make_operations(xml)
        ops.register_article("1" * 40, "Valid Name")
        transport.post.assert_called_once()

    def test_article_name_exactly_40_chars_is_valid(self) -> None:
        xml = _fixture("sendAPDReqV01_success.xml")
        ops, transport = _make_operations(xml)
        ops.register_article("1001", "N" * 40)
        transport.post.assert_called_once()

    def test_validation_truncate_article_number(self) -> None:
        xml = _fixture("sendAPDReqV01_success.xml")
        ops, transport = _make_operations(xml, validation_truncate=True)
        ops.register_article("1" * 41, "Valid Name")
        envelope, _ = transport.post.call_args[0]
        assert "1" * 40 in envelope
        assert "1" * 41 not in envelope

    def test_validation_truncate_article_name(self) -> None:
        xml = _fixture("sendAPDReqV01_success.xml")
        ops, transport = _make_operations(xml, validation_truncate=True)
        ops.register_article("1001", "N" * 41)
        envelope, _ = transport.post.call_args[0]
        assert "N" * 40 in envelope
        assert "N" * 41 not in envelope

    def test_test_mode_prepends_prefix(self) -> None:
        xml = _fixture("sendAPDReqV01_success.xml")
        ops, transport = _make_operations(xml, test_mode=True, test_prefix="TEST_")
        ops.register_article("1001", "Bolt M6")
        envelope, _ = transport.post.call_args[0]
        assert "TEST_1001" in envelope

    def test_test_mode_false_no_prefix(self) -> None:
        xml = _fixture("sendAPDReqV01_success.xml")
        ops, transport = _make_operations(xml, test_mode=False)
        ops.register_article("1001", "Bolt M6")
        envelope, _ = transport.post.call_args[0]
        assert "1001" in envelope
        assert "TEST_1001" not in envelope

    def test_test_mode_prefix_counts_toward_length_limit(self) -> None:
        ops, transport = _make_operations(test_mode=True, test_prefix="TEST_")
        with pytest.raises(HanelGatewayValidationError):
            ops.register_article("1" * 36, "Valid Name")
        transport.post.assert_not_called()

    def test_article_number_with_hyphen_raises_validation_error(self) -> None:
        ops, transport = _make_operations()
        with pytest.raises(HanelGatewayValidationError) as exc_info:
            ops.register_article("ART-001", "Valid Name")
        assert exc_info.value.field == "article_number"
        transport.post.assert_not_called()

    def test_article_number_with_space_raises_validation_error(self) -> None:
        ops, transport = _make_operations()
        with pytest.raises(HanelGatewayValidationError) as exc_info:
            ops.register_article("12 34", "Valid Name")
        assert exc_info.value.field == "article_number"
        transport.post.assert_not_called()

    def test_article_number_with_symbol_raises_validation_error(self) -> None:
        ops, transport = _make_operations()
        with pytest.raises(HanelGatewayValidationError) as exc_info:
            ops.register_article("12/34", "Valid Name")
        assert exc_info.value.field == "article_number"
        transport.post.assert_not_called()

    def test_article_number_with_letters_raises_validation_error(self) -> None:
        # The article number is a numeric code: letters are rejected.
        ops, transport = _make_operations()
        with pytest.raises(HanelGatewayValidationError) as exc_info:
            ops.register_article("ART001", "Valid Name")
        assert exc_info.value.field == "article_number"
        transport.post.assert_not_called()

    def test_article_name_may_contain_spaces_and_symbols(self) -> None:
        # The charset constraint applies only to article_number, not article_name.
        xml = _fixture("sendAPDReqV01_success.xml")
        ops, transport = _make_operations(xml)
        ops.register_article("1001", "M6 stainless bolt - A2/70")
        transport.post.assert_called_once()

    def test_validation_truncate_does_not_bypass_charset_check(self) -> None:
        # Unlike the length check, the charset rule always raises even with
        # validation_truncate=True: an article number cannot be auto-corrected.
        ops, transport = _make_operations(validation_truncate=True)
        with pytest.raises(HanelGatewayValidationError) as exc_info:
            ops.register_article("ART-001", "Valid Name")
        assert exc_info.value.field == "article_number"
        transport.post.assert_not_called()

    def test_test_mode_prefix_underscore_does_not_trigger_charset_error(self) -> None:
        # The test_prefix ("TEST_") contains an underscore; the charset check
        # runs on the caller value before the prefix is prepended.
        xml = _fixture("sendAPDReqV01_success.xml")
        ops, transport = _make_operations(xml, test_mode=True, test_prefix="TEST_")
        ops.register_article("1001", "Valid Name")
        envelope, _ = transport.post.call_args[0]
        assert "TEST_1001" in envelope


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
    def test_raises_application_error_on_nonzero_return_value(self) -> None:
        responses_lib.add(
            responses_lib.POST,
            _ENDPOINT,
            body=_fixture("response_delete_job_error.xml"),
            status=200,
        )
        with pytest.raises(HanelGatewayApplicationError) as exc_info:
            _ops(_config()).cancel_order("ORD-003")
        exc = exc_info.value
        assert exc.operation == "deleteJobReqV01"
        assert exc.return_value != 0

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


_SUCCESS_XML = _fixture("send_movement_order_success.xml")

_ONE_LINE = [
    MovementLine(article_number="1001", operation="+", nominal_quantity=5.0)
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
        assert "1001" in envelope

    def test_envelope_contains_operation_and_quantity(self) -> None:
        ops, transport = _make_operations(_SUCCESS_XML)
        ops.send_movement_order("JOB-1", _ONE_LINE)
        envelope, _ = transport.post.call_args[0]
        assert "<xsd:operation>+</xsd:operation>" in envelope
        assert "5.0" in envelope

    def test_multiple_positions_all_in_envelope(self) -> None:
        positions = [
            MovementLine("1001", "+", 10.0),
            MovementLine("1002", "-", 3.5),
        ]
        ops, transport = _make_operations(_SUCCESS_XML)
        ops.send_movement_order("JOB-MULTI", positions)
        envelope, _ = transport.post.call_args[0]
        assert "1001" in envelope
        assert "1002" in envelope

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
        bad = [MovementLine("1001", "X", 1.0)]
        with pytest.raises(HanelGatewayValidationError) as exc_info:
            ops.send_movement_order("JOB-1", bad)
        assert "operation" in exc_info.value.field
        transport.post.assert_not_called()

    def test_zero_quantity_raises_validation_error(self) -> None:
        ops, transport = _make_operations()
        bad = [
            MovementLine(article_number="1001", operation="+", nominal_quantity=0.0)
        ]
        with pytest.raises(HanelGatewayValidationError) as exc_info:
            ops.send_movement_order("JOB-1", bad)
        assert "nominal_quantity" in exc_info.value.field
        transport.post.assert_not_called()

    def test_negative_quantity_raises_validation_error(self) -> None:
        ops, transport = _make_operations()
        bad = [
            MovementLine(article_number="1001", operation="+", nominal_quantity=-1.0)
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
            MovementLine(article_number="1" * 41, operation="+", nominal_quantity=1.0)
        ]
        with pytest.raises(HanelGatewayValidationError) as exc_info:
            ops.send_movement_order("JOB-1", bad)
        assert "article_number" in exc_info.value.field
        transport.post.assert_not_called()

    def test_article_number_with_hyphen_raises_validation_error(self) -> None:
        ops, transport = _make_operations()
        bad = [
            MovementLine(article_number="ART-001", operation="+", nominal_quantity=1.0)
        ]
        with pytest.raises(HanelGatewayValidationError) as exc_info:
            ops.send_movement_order("JOB-1", bad)
        assert exc_info.value.field == "positions[0].article_number"
        transport.post.assert_not_called()

    def test_order_number_with_hyphen_is_allowed(self) -> None:
        # The charset constraint applies to article_number only, not job_number.
        ops, transport = _make_operations(_SUCCESS_XML)
        ops.send_movement_order("JOB-001", _ONE_LINE)
        transport.post.assert_called_once()

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

class TestGetCompletedMovements:
    def test_returns_list_of_movement_results(self) -> None:
        xml = _fixture("read_jobs_response_mode1.xml")
        ops, _ = _make_operations(xml)
        results = ops.get_completed_movements()
        assert isinstance(results, list)
        assert all(isinstance(r, MovementResult) for r in results)

    def test_returns_correct_number_of_results(self) -> None:
        xml = _fixture("read_jobs_response_mode1.xml")
        ops, _ = _make_operations(xml)
        results = ops.get_completed_movements()
        assert len(results) == 2

    def test_envelope_contains_mode_1(self) -> None:
        xml = _fixture("read_jobs_response_mode1.xml")
        ops, transport = _make_operations(xml)
        ops.get_completed_movements()
        envelope, _ = transport.post.call_args[0]
        assert "<xsd:mode>1</xsd:mode>" in envelope

    def test_calls_read_all_jobs_operation(self) -> None:
        xml = _fixture("read_jobs_response_mode1.xml")
        ops, transport = _make_operations(xml)
        ops.get_completed_movements()
        _, operation = transport.post.call_args[0]
        assert operation == "readAllJobsReqV01"

    def test_maps_job_number(self) -> None:
        xml = _fixture("read_jobs_response_mode1.xml")
        ops, _ = _make_operations(xml)
        results = ops.get_completed_movements()
        assert results[0].job_number == "ORD-003"
        assert results[1].job_number == "ORD-004"

    def test_maps_positions_to_movement_line_results(self) -> None:
        xml = _fixture("read_jobs_response_mode1.xml")
        ops, _ = _make_operations(xml)
        results = ops.get_completed_movements()
        assert all(
            isinstance(p, MovementLineResult) for r in results for p in r.positions
        )

    def test_maps_actual_quantity(self) -> None:
        xml = _fixture("read_jobs_response_mode1.xml")
        ops, _ = _make_operations(xml)
        results = ops.get_completed_movements()
        assert results[1].positions[0].actual_quantity == 15.0
        assert results[1].positions[0].nominal_quantity == 40.0

    def test_soap_fault_propagates(self) -> None:
        ops, _ = _make_operations(_fixture("soap_fault.xml"))
        with pytest.raises(HanelGatewaySoapFaultError):
            ops.get_completed_movements()


class TestGetAllOrders:
    def test_returns_list_of_movement_results(self) -> None:
        xml = _fixture("read_jobs_response_mode0.xml")
        ops, _ = _make_operations(xml)
        results = ops.get_all_orders()
        assert isinstance(results, list)
        assert all(isinstance(r, MovementResult) for r in results)

    def test_returns_correct_number_of_results(self) -> None:
        xml = _fixture("read_jobs_response_mode0.xml")
        ops, _ = _make_operations(xml)
        results = ops.get_all_orders()
        assert len(results) == 3

    def test_envelope_contains_mode_0(self) -> None:
        xml = _fixture("read_jobs_response_mode0.xml")
        ops, transport = _make_operations(xml)
        ops.get_all_orders()
        envelope, _ = transport.post.call_args[0]
        assert "<xsd:mode>0</xsd:mode>" in envelope

    def test_calls_read_all_jobs_operation(self) -> None:
        xml = _fixture("read_jobs_response_mode0.xml")
        ops, transport = _make_operations(xml)
        ops.get_all_orders()
        _, operation = transport.post.call_args[0]
        assert operation == "readAllJobsReqV01"

    def test_maps_job_number(self) -> None:
        xml = _fixture("read_jobs_response_mode0.xml")
        ops, _ = _make_operations(xml)
        results = ops.get_all_orders()
        assert results[0].job_number == "ORD-001"
        assert results[1].job_number == "ORD-002"
        assert results[2].job_number == "ORD-003"

    def test_maps_positions_to_movement_line_results(self) -> None:
        xml = _fixture("read_jobs_response_mode0.xml")
        ops, _ = _make_operations(xml)
        results = ops.get_all_orders()
        assert all(
            isinstance(p, MovementLineResult) for r in results for p in r.positions
        )

    def test_includes_queued_and_in_progress_orders(self) -> None:
        xml = _fixture("read_jobs_response_mode0.xml")
        ops, _ = _make_operations(xml)
        results = ops.get_all_orders()
        statuses = {r.job_status for r in results}
        assert 0 in statuses
        assert 1 in statuses

    def test_soap_fault_propagates(self) -> None:
        ops, _ = _make_operations(_fixture("soap_fault.xml"))
        with pytest.raises(HanelGatewaySoapFaultError):
            ops.get_all_orders()


class TestGetInventory:
    def test_returns_list_of_stock_records(self) -> None:
        ops, _ = _make_operations(_fixture("read_inventory_response.xml"))
        results = ops.get_inventory()
        assert isinstance(results, list)
        assert all(isinstance(r, StockRecord) for r in results)

    def test_returns_correct_number_of_records(self) -> None:
        ops, _ = _make_operations(_fixture("read_inventory_response.xml"))
        results = ops.get_inventory()
        assert len(results) == 2

    def test_calls_correct_soap_operation(self) -> None:
        ops, transport = _make_operations(_fixture("read_inventory_response.xml"))
        ops.get_inventory()
        _, operation = transport.post.call_args[0]
        assert operation == "readAllAMDReqV01"

    def test_envelope_has_no_parameters(self) -> None:
        ops, transport = _make_operations(_fixture("read_inventory_response.xml"))
        ops.get_inventory()
        envelope, _ = transport.post.call_args[0]
        assert "<main:param>" not in envelope

    def test_maps_article_number(self) -> None:
        ops, _ = _make_operations(_fixture("read_inventory_response.xml"))
        results = ops.get_inventory()
        assert results[0].article_number == "1001"
        assert results[1].article_number == "1002"

    def test_maps_article_name(self) -> None:
        ops, _ = _make_operations(_fixture("read_inventory_response.xml"))
        results = ops.get_inventory()
        assert results[0].article_name == "Bolt M6"

    def test_maps_numeric_fields(self) -> None:
        ops, _ = _make_operations(_fixture("read_inventory_response.xml"))
        results = ops.get_inventory()
        assert results[0].lift_number == 1
        assert results[0].shelf_number == 5
        assert results[0].compartment_number == 12
        assert results[0].compartment_depth_number == 3
        assert results[0].container_size == 1
        assert results[0].fifo == 0

    def test_maps_float_fields(self) -> None:
        ops, _ = _make_operations(_fixture("read_inventory_response.xml"))
        results = ops.get_inventory()
        assert results[0].inventory_at_storage_location == 250.0
        assert results[0].minimum_inventory == 50.0

    def test_zero_location_record(self) -> None:
        ops, _ = _make_operations(_fixture("read_inventory_response.xml"))
        results = ops.get_inventory()
        assert results[1].lift_number == 0
        assert results[1].shelf_number == 0
        assert results[1].inventory_at_storage_location == 0.0

    def test_soap_fault_propagates(self) -> None:
        ops, _ = _make_operations(_fixture("soap_fault.xml"))
        with pytest.raises(HanelGatewaySoapFaultError):
            ops.get_inventory()

    def test_malformed_xml_raises_parse_error(self) -> None:
        ops, _ = _make_operations("NOT VALID XML<<<")
        with pytest.raises(HanelGatewayParseError):
            ops.get_inventory()


class TestRegisterArticleV03:
    def test_lot_mode_calls_sendAPDV03(self) -> None:
        xml = _fixture("sendAPDV03_success.xml")
        ops, transport = _make_operations(xml, lot_management_enabled=True)
        ops.register_article("1001", "Bolt M6")
        _, operation = transport.post.call_args[0]
        assert operation == "sendAPDV03"

    def test_lot_mode_false_calls_sendAPDReqV01(self) -> None:
        xml = _fixture("sendAPDReqV01_success.xml")
        ops, transport = _make_operations(xml, lot_management_enabled=False)
        ops.register_article("1001", "Bolt M6")
        _, operation = transport.post.call_args[0]
        assert operation == "sendAPDReqV01"

    def test_batch_number_in_envelope(self) -> None:
        xml = _fixture("sendAPDV03_success.xml")
        ops, transport = _make_operations(xml, lot_management_enabled=True)
        ops.register_article("1001", "Bolt M6", batch_number="LOT-X")
        envelope, _ = transport.post.call_args[0]
        assert "LOT-X" in envelope

    def test_batch_number_absent_when_none(self) -> None:
        xml = _fixture("sendAPDV03_success.xml")
        ops, transport = _make_operations(xml, lot_management_enabled=True)
        ops.register_article("1001", "Bolt M6", batch_number=None)
        envelope, _ = transport.post.call_args[0]
        assert "batchNumber" not in envelope

    def test_batch_number_too_long_raises_validation(self) -> None:
        ops, transport = _make_operations(lot_management_enabled=True)
        with pytest.raises(HanelGatewayValidationError) as exc_info:
            ops.register_article("1001", "Bolt M6", batch_number="L" * 41)
        assert exc_info.value.field == "batch_number"
        transport.post.assert_not_called()

    def test_application_error_hint_in_lot_mode(self) -> None:
        xml = _fixture("sendAPDV03_error.xml")
        ops, _ = _make_operations(xml, lot_management_enabled=True)
        with pytest.raises(HanelGatewayApplicationError) as exc_info:
            ops.register_article("1001", "Bolt M6")
        assert "hint" in exc_info.value.message


class TestSendMovementOrderV02:
    def test_lot_mode_calls_sendJobsV02(self) -> None:
        xml = _fixture("send_movement_order_v02_success.xml")
        ops, transport = _make_operations(xml, lot_management_enabled=True)
        ops.send_movement_order("JOB-1", [MovementLine("1001", "+", 5.0)])
        _, operation = transport.post.call_args[0]
        assert operation == "sendJobsV02"

    def test_lot_mode_false_calls_sendJobsReqV01(self) -> None:
        xml = _fixture("send_movement_order_success.xml")
        ops, transport = _make_operations(xml, lot_management_enabled=False)
        ops.send_movement_order("JOB-1", [MovementLine("1001", "+", 5.0)])
        _, operation = transport.post.call_args[0]
        assert operation == "sendJobsReqV01"

    def test_batch_number_in_envelope(self) -> None:
        xml = _fixture("send_movement_order_v02_success.xml")
        ops, transport = _make_operations(xml, lot_management_enabled=True)
        line = MovementLine("1001", "+", 5.0, batch_number="LOT-B")
        ops.send_movement_order("JOB-1", [line])
        envelope, _ = transport.post.call_args[0]
        assert "LOT-B" in envelope

    def test_batch_number_absent_when_none(self) -> None:
        xml = _fixture("send_movement_order_v02_success.xml")
        ops, transport = _make_operations(xml, lot_management_enabled=True)
        line = MovementLine("1001", "+", 5.0)
        ops.send_movement_order("JOB-1", [line])
        envelope, _ = transport.post.call_args[0]
        assert "batchNumber" not in envelope

    def test_application_error_hint_in_lot_mode(self) -> None:
        xml = _fixture("sendAPDReqV01_error.xml")
        ops, _ = _make_operations(xml, lot_management_enabled=True)
        with pytest.raises(HanelGatewayApplicationError) as exc_info:
            ops.send_movement_order("JOB-1", [MovementLine("1001", "+", 5.0)])
        assert "hint" in exc_info.value.message


class TestGetCompletedMovementsV02:
    def test_lot_mode_calls_readAllJobsV02(self) -> None:
        xml = _fixture("read_jobs_v02_response_mode1.xml")
        ops, transport = _make_operations(xml, lot_management_enabled=True)
        ops.get_completed_movements()
        _, operation = transport.post.call_args[0]
        assert operation == "readAllJobsV02"

    def test_lot_mode_envelope_contains_mode_1(self) -> None:
        xml = _fixture("read_jobs_v02_response_mode1.xml")
        ops, transport = _make_operations(xml, lot_management_enabled=True)
        ops.get_completed_movements()
        envelope, _ = transport.post.call_args[0]
        assert "<xsd:mode>1</xsd:mode>" in envelope

    def test_batch_number_mapped_in_positions(self) -> None:
        xml = _fixture("read_jobs_v02_response_mode1.xml")
        ops, _ = _make_operations(xml, lot_management_enabled=True)
        results = ops.get_completed_movements()
        assert results[0].positions[0].batch_number == "LOT-A"

    def test_lot_mode_false_calls_readAllJobsReqV01(self) -> None:
        xml = _fixture("read_jobs_response_mode1.xml")
        ops, transport = _make_operations(xml, lot_management_enabled=False)
        ops.get_completed_movements()
        _, operation = transport.post.call_args[0]
        assert operation == "readAllJobsReqV01"


class TestGetAllOrdersV02:
    def test_lot_mode_calls_readAllJobsV02(self) -> None:
        xml = _fixture("read_jobs_v02_response_mode0.xml")
        ops, transport = _make_operations(xml, lot_management_enabled=True)
        ops.get_all_orders()
        _, operation = transport.post.call_args[0]
        assert operation == "readAllJobsV02"

    def test_lot_mode_envelope_contains_mode_0(self) -> None:
        xml = _fixture("read_jobs_v02_response_mode0.xml")
        ops, transport = _make_operations(xml, lot_management_enabled=True)
        ops.get_all_orders()
        envelope, _ = transport.post.call_args[0]
        assert "<xsd:mode>0</xsd:mode>" in envelope

    def test_batch_number_none_when_absent(self) -> None:
        xml = _fixture("read_jobs_v02_response_mode0.xml")
        ops, _ = _make_operations(xml, lot_management_enabled=True)
        results = ops.get_all_orders()
        assert results[1].positions[0].batch_number is None


class TestGetInventoryV04:
    def test_lot_mode_calls_readAllAMDV04(self) -> None:
        xml = _fixture("read_inventory_v04_response.xml")
        ops, transport = _make_operations(xml, lot_management_enabled=True)
        ops.get_inventory()
        _, operation = transport.post.call_args[0]
        assert operation == "readAllAMDV04"

    def test_lot_mode_false_calls_readAllAMDReqV01(self) -> None:
        xml = _fixture("read_inventory_response.xml")
        ops, transport = _make_operations(xml, lot_management_enabled=False)
        ops.get_inventory()
        _, operation = transport.post.call_args[0]
        assert operation == "readAllAMDReqV01"

    def test_batch_number_mapped_in_stock_records(self) -> None:
        xml = _fixture("read_inventory_v04_response.xml")
        ops, _ = _make_operations(xml, lot_management_enabled=True)
        results = ops.get_inventory()
        assert results[0].batch_number == "LOT-2024"

    def test_batch_number_none_when_absent(self) -> None:
        xml = _fixture("read_inventory_v04_response.xml")
        ops, _ = _make_operations(xml, lot_management_enabled=True)
        results = ops.get_inventory()
        assert results[1].batch_number is None

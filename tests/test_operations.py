"""Integration tests for SoapOperations.cancel_order — HTTP mocked with `responses`."""

from __future__ import annotations

import pathlib

import pytest
import responses as responses_lib

from hanel_warehouse_gateway.config import GatewayConfig
from hanel_warehouse_gateway.exceptions import HanelGatewayValidationError
from hanel_warehouse_gateway.operations import SoapOperations
from hanel_warehouse_gateway.transport import SoapTransport

_ENDPOINT = "http://mock-hanel.test/HanelService"
_FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def _fixture(name: str) -> str:
    return (_FIXTURES / name).read_text(encoding="utf-8")


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

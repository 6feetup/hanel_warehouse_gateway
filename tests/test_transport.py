"""Integration tests for SoapTransport — HTTP mocked with `responses`."""

from __future__ import annotations

import pytest
import responses as responses_lib
from responses import ConnectionError as MockConnectionError

from hanel_warehouse_gateway.config import GatewayConfig
from hanel_warehouse_gateway.exceptions import (
    HanelGatewayHttpError,
    HanelGatewayNetworkError,
)
from hanel_warehouse_gateway.transport import SoapTransport

_ENDPOINT = "http://mock-hanel.test/HanelService"
_ENVELOPE = "<soapenv:Envelope/>"
_OPERATION = "deleteJobReqV01"
_OK_BODY = "<response><returnValue>0</returnValue></response>"


def _config(**overrides: object) -> GatewayConfig:
    defaults: dict[str, object] = {
        "endpoint_url": _ENDPOINT,
        "retry_attempts": 3,
        "retry_delay_seconds": 0.0,
    }
    defaults.update(overrides)
    return GatewayConfig(**defaults)  # type: ignore[arg-type]


class TestPostSuccess:
    @responses_lib.activate
    def test_returns_response_body(self) -> None:
        responses_lib.add(responses_lib.POST, _ENDPOINT, body=_OK_BODY, status=200)
        transport = SoapTransport(_config())
        result = transport.post(_ENVELOPE, _OPERATION)
        assert result == _OK_BODY

    @responses_lib.activate
    def test_sends_correct_content_type(self) -> None:
        responses_lib.add(responses_lib.POST, _ENDPOINT, body=_OK_BODY, status=200)
        transport = SoapTransport(_config())
        transport.post(_ENVELOPE, _OPERATION)
        ct = responses_lib.calls[0].request.headers["Content-Type"]
        assert ct == "text/xml; charset=utf-8"

    @responses_lib.activate
    def test_sends_envelope_as_body(self) -> None:
        responses_lib.add(responses_lib.POST, _ENDPOINT, body=_OK_BODY, status=200)
        transport = SoapTransport(_config())
        transport.post(_ENVELOPE, _OPERATION)
        assert responses_lib.calls[0].request.body == _ENVELOPE.encode("utf-8")


class TestHttpError:
    @responses_lib.activate
    def test_http_500_raises_http_error(self) -> None:
        responses_lib.add(
            responses_lib.POST, _ENDPOINT, body="Server Error", status=500
        )
        transport = SoapTransport(_config())
        with pytest.raises(HanelGatewayHttpError) as exc_info:
            transport.post(_ENVELOPE, _OPERATION)
        assert exc_info.value.http_status == 500
        assert exc_info.value.operation == _OPERATION

    @responses_lib.activate
    def test_http_404_raises_http_error(self) -> None:
        responses_lib.add(responses_lib.POST, _ENDPOINT, body="Not Found", status=404)
        transport = SoapTransport(_config())
        with pytest.raises(HanelGatewayHttpError) as exc_info:
            transport.post(_ENVELOPE, _OPERATION)
        assert exc_info.value.http_status == 404

    @responses_lib.activate
    def test_http_error_logs_error(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        responses_lib.add(
            responses_lib.POST, _ENDPOINT, body="Server Error", status=500
        )
        transport = SoapTransport(_config())
        with caplog.at_level("ERROR", logger="hanel_warehouse_gateway"):
            with pytest.raises(HanelGatewayHttpError):
                transport.post(_ENVELOPE, _OPERATION)
        assert any(
            "HTTP 500" in r.message and r.levelname == "ERROR"
            for r in caplog.records
        )

    @responses_lib.activate
    def test_http_500_does_not_retry(self) -> None:
        responses_lib.add(responses_lib.POST, _ENDPOINT, body="Error", status=500)
        transport = SoapTransport(_config(retry_attempts=3))
        with pytest.raises(HanelGatewayHttpError):
            transport.post(_ENVELOPE, _OPERATION)
        assert len(responses_lib.calls) == 1


class TestNetworkError:
    @responses_lib.activate
    def test_connection_error_exhausts_retries(self) -> None:
        for _ in range(3):
            responses_lib.add(
                responses_lib.POST, _ENDPOINT, body=MockConnectionError()
            )
        transport = SoapTransport(_config(retry_attempts=3))
        with pytest.raises(HanelGatewayNetworkError) as exc_info:
            transport.post(_ENVELOPE, _OPERATION)
        assert exc_info.value.operation == _OPERATION
        assert len(responses_lib.calls) == 3

    @responses_lib.activate
    def test_network_error_logs_error(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        for _ in range(2):
            responses_lib.add(
                responses_lib.POST, _ENDPOINT, body=MockConnectionError()
            )
        transport = SoapTransport(_config(retry_attempts=2))
        with caplog.at_level("ERROR", logger="hanel_warehouse_gateway"):
            with pytest.raises(HanelGatewayNetworkError):
                transport.post(_ENVELOPE, _OPERATION)
        assert any(
            "Network failure" in r.message and r.levelname == "ERROR"
            for r in caplog.records
        )

    @responses_lib.activate
    def test_succeeds_after_transient_failure(self) -> None:
        responses_lib.add(
            responses_lib.POST, _ENDPOINT, body=MockConnectionError()
        )
        responses_lib.add(responses_lib.POST, _ENDPOINT, body=_OK_BODY, status=200)
        transport = SoapTransport(_config(retry_attempts=3))
        result = transport.post(_ENVELOPE, _OPERATION)
        assert result == _OK_BODY
        assert len(responses_lib.calls) == 2

    @responses_lib.activate
    def test_network_error_is_gateway_error(self) -> None:
        from hanel_warehouse_gateway.exceptions import HanelGatewayError

        responses_lib.add(
            responses_lib.POST, _ENDPOINT, body=MockConnectionError()
        )
        transport = SoapTransport(_config(retry_attempts=1))
        with pytest.raises(HanelGatewayError):
            transport.post(_ENVELOPE, _OPERATION)

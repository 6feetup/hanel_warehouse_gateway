"""Tests for SoapTransport (Layer 1)."""

from __future__ import annotations

import pytest
import requests
import responses as responses_lib

from hanel_warehouse_gateway import GatewayConfig
from hanel_warehouse_gateway.exceptions import (
    HanelGatewayHttpError,
    HanelGatewayNetworkError,
)
from hanel_warehouse_gateway.transport import SoapTransport

_ENDPOINT = "http://mock-server/HanelService"
_ENVELOPE = "<soapenv:Envelope/>"
_OPERATION = "sendAPDReqV01"
_SUCCESS_BODY = "<response>ok</response>"
_CONN_ERR = requests.ConnectionError("refused")


def _config(**kwargs: object) -> GatewayConfig:
    defaults: dict[str, object] = {
        "endpoint_url": _ENDPOINT,
        "retry_attempts": 3,
        "retry_delay_seconds": 0.0,
    }
    defaults.update(kwargs)
    return GatewayConfig(**defaults)  # type: ignore[arg-type]


class TestSoapTransportPost:
    @responses_lib.activate
    def test_success_returns_body(self) -> None:
        responses_lib.add(responses_lib.POST, _ENDPOINT, body=_SUCCESS_BODY, status=200)
        transport = SoapTransport(_config())
        result = transport.post(_ENVELOPE, _OPERATION)
        assert result == _SUCCESS_BODY

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
    def test_connection_error_exhausts_retries(self) -> None:
        responses_lib.add(responses_lib.POST, _ENDPOINT, body=_CONN_ERR)
        transport = SoapTransport(_config(retry_attempts=2))
        with pytest.raises(HanelGatewayNetworkError) as exc_info:
            transport.post(_ENVELOPE, _OPERATION)
        assert exc_info.value.operation == _OPERATION

    @responses_lib.activate
    def test_retry_succeeds_on_third_attempt(self) -> None:
        responses_lib.add(responses_lib.POST, _ENDPOINT, body=_CONN_ERR)
        responses_lib.add(responses_lib.POST, _ENDPOINT, body=_CONN_ERR)
        responses_lib.add(responses_lib.POST, _ENDPOINT, body=_SUCCESS_BODY, status=200)
        transport = SoapTransport(_config(retry_attempts=3))
        result = transport.post(_ENVELOPE, _OPERATION)
        assert result == _SUCCESS_BODY
        assert len(responses_lib.calls) == 3

    @responses_lib.activate
    def test_http_error_does_not_retry(self) -> None:
        responses_lib.add(responses_lib.POST, _ENDPOINT, body="Error", status=503)
        transport = SoapTransport(_config(retry_attempts=3))
        with pytest.raises(HanelGatewayHttpError):
            transport.post(_ENVELOPE, _OPERATION)
        assert len(responses_lib.calls) == 1

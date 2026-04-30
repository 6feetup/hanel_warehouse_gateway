"""Unit tests for _xml.py — envelope builders and response parsers."""

from __future__ import annotations

import pathlib

import pytest

from hanel_warehouse_gateway._xml import (
    build_cancel_order_envelope,
    parse_return_value,
)
from hanel_warehouse_gateway.exceptions import (
    HanelGatewayParseError,
    HanelGatewaySoapFaultError,
)

_FIXTURES = pathlib.Path(__file__).parent / "fixtures"

_NS_MAIN = "http://main.jws.com.hanel.de"
_NS_XSD = "http://main.jws.com.hanel.de/xsd"


def _fixture(name: str) -> str:
    return (_FIXTURES / name).read_text(encoding="utf-8")


class TestBuildCancelOrderEnvelope:
    def test_contains_job_number(self) -> None:
        xml = build_cancel_order_envelope("ORD-001", _NS_MAIN, _NS_XSD)
        assert "<xsd:jobNumber>ORD-001</xsd:jobNumber>" in xml

    def test_contains_operation_name(self) -> None:
        xml = build_cancel_order_envelope("ORD-001", _NS_MAIN, _NS_XSD)
        assert "deleteJobReqV01" in xml

    def test_contains_namespace_main(self) -> None:
        xml = build_cancel_order_envelope("ORD-001", _NS_MAIN, _NS_XSD)
        assert _NS_MAIN in xml

    def test_contains_namespace_xsd(self) -> None:
        xml = build_cancel_order_envelope("ORD-001", _NS_MAIN, _NS_XSD)
        assert _NS_XSD in xml

    def test_contains_soap_envelope_namespace(self) -> None:
        xml = build_cancel_order_envelope("ORD-001", _NS_MAIN, _NS_XSD)
        assert "http://schemas.xmlsoap.org/soap/envelope/" in xml

    def test_interpolates_custom_job_number(self) -> None:
        xml = build_cancel_order_envelope("JOB-XYZ-99", _NS_MAIN, _NS_XSD)
        assert "JOB-XYZ-99" in xml
        assert "ORD-001" not in xml


class TestParseReturnValue:
    def test_ok_fixture_returns_zero(self) -> None:
        xml = _fixture("response_delete_job_ok.xml")
        assert parse_return_value(xml, "deleteJobReqV01", _NS_XSD) == 0

    def test_error_fixture_returns_one(self) -> None:
        xml = _fixture("response_delete_job_error.xml")
        assert parse_return_value(xml, "deleteJobReqV01", _NS_XSD) == 1

    def test_soap_fault_raises_soap_fault_error(self) -> None:
        xml = _fixture("response_soap_fault.xml")
        with pytest.raises(HanelGatewaySoapFaultError) as exc_info:
            parse_return_value(xml, "deleteJobReqV01", _NS_XSD)
        exc = exc_info.value
        assert exc.fault_code == "env:Server"
        assert exc.fault_string == "Unknown operation"
        assert exc.operation == "deleteJobReqV01"

    def test_soap_fault_error_is_gateway_error(self) -> None:
        from hanel_warehouse_gateway.exceptions import HanelGatewayError

        xml = _fixture("response_soap_fault.xml")
        with pytest.raises(HanelGatewayError):
            parse_return_value(xml, "deleteJobReqV01", _NS_XSD)

    def test_malformed_xml_raises_parse_error(self) -> None:
        with pytest.raises(HanelGatewayParseError):
            parse_return_value("<not-xml", "deleteJobReqV01", _NS_XSD)

    def test_missing_return_value_raises_parse_error(self) -> None:
        xml = "<root><other>1</other></root>"
        with pytest.raises(HanelGatewayParseError):
            parse_return_value(xml, "deleteJobReqV01", _NS_XSD)

    def test_custom_namespace_xsd_is_honored(self) -> None:
        xml = (
            '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"'
            ' xmlns:xsd="http://example.com/custom">'
            "<soapenv:Body><xsd:return>"
            "<xsd:returnValue>0</xsd:returnValue>"
            "</xsd:return></soapenv:Body></soapenv:Envelope>"
        )
        assert parse_return_value(xml, "op", "http://example.com/custom") == 0

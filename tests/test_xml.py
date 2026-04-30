"""Unit tests for _xml.py — envelope builders and response parsers."""

from __future__ import annotations

import pathlib

import pytest

from hanel_warehouse_gateway._xml import (
    build_cancel_order_envelope,
    build_register_article_envelope,
    build_send_movement_order_envelope,
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


class TestBuildRegisterArticleEnvelope:
    def test_contains_article_number(self) -> None:
        xml = build_register_article_envelope("ART001", "Bolt M6", _NS_MAIN, _NS_XSD)
        assert "ART001" in xml

    def test_contains_article_name(self) -> None:
        xml = build_register_article_envelope("ART001", "Bolt M6", _NS_MAIN, _NS_XSD)
        assert "Bolt M6" in xml

    def test_contains_operation_tag(self) -> None:
        xml = build_register_article_envelope("ART001", "Bolt M6", _NS_MAIN, _NS_XSD)
        assert "sendAPDReqV01" in xml

    def test_contains_article_pool_data_record(self) -> None:
        xml = build_register_article_envelope("ART001", "Bolt M6", _NS_MAIN, _NS_XSD)
        assert "articlePoolDataRecord" in xml

    def test_uses_provided_namespaces(self) -> None:
        xml = build_register_article_envelope("X", "Y", _NS_MAIN, _NS_XSD)
        assert _NS_MAIN in xml
        assert _NS_XSD in xml

    def test_is_valid_xml(self) -> None:
        import xml.etree.ElementTree as ET

        xml = build_register_article_envelope("ART001", "Bolt M6", _NS_MAIN, _NS_XSD)
        ET.fromstring(xml)  # must not raise

    def test_escapes_special_characters(self) -> None:
        import xml.etree.ElementTree as ET

        xml = build_register_article_envelope(
            "A&B<1>", 'Bolt "M6" & <Nut>', _NS_MAIN, _NS_XSD
        )
        assert "<xsd:articleNumber>A&B<1></xsd:articleNumber>" not in xml
        assert 'Bolt "M6" & <Nut>' not in xml
        root = ET.fromstring(xml)
        ns = {"xsd": _NS_XSD}
        number_el = root.find(".//xsd:articleNumber", ns)
        name_el = root.find(".//xsd:articleName", ns)
        assert number_el is not None and number_el.text == "A&B<1>"
        assert name_el is not None and name_el.text == 'Bolt "M6" & <Nut>'


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

    def test_register_article_success_fixture(self) -> None:
        xml = _fixture("sendAPDReqV01_success.xml")
        assert parse_return_value(xml, "sendAPDReqV01", _NS_XSD) == 0

    def test_register_article_error_fixture(self) -> None:
        xml = _fixture("sendAPDReqV01_error.xml")
        assert parse_return_value(xml, "sendAPDReqV01", _NS_XSD) == 1

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

    def test_send_movement_order_success_fixture(self) -> None:
        xml = _fixture("send_movement_order_success.xml")
        assert parse_return_value(xml, "sendJobsReqV01", _NS_XSD) == 0

    def test_custom_namespace_xsd_is_honored(self) -> None:
        xml = (
            '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"'
            ' xmlns:xsd="http://example.com/custom">'
            "<soapenv:Body><xsd:return>"
            "<xsd:returnValue>0</xsd:returnValue>"
            "</xsd:return></soapenv:Body></soapenv:Envelope>"
        )
        assert parse_return_value(xml, "op", "http://example.com/custom") == 0


_ONE_POSITION = [
    {"article_number": "ART-001", "operation": "+", "nominal_quantity": 5.0}
]


def _build_smo(job_number: str, positions: list[dict[str, object]]) -> str:
    return build_send_movement_order_envelope(job_number, positions, _NS_MAIN, _NS_XSD)


class TestBuildSendMovementOrderEnvelope:
    def test_contains_job_number(self) -> None:
        xml = _build_smo("JOB-123", _ONE_POSITION)
        assert "<xsd:jobNumber>JOB-123</xsd:jobNumber>" in xml

    def test_contains_operation_name(self) -> None:
        xml = _build_smo("JOB-1", _ONE_POSITION)
        assert "sendJobsReqV01" in xml

    def test_single_position_fields(self) -> None:
        xml = _build_smo("JOB-1", _ONE_POSITION)
        assert "<xsd:articleNumber>ART-001</xsd:articleNumber>" in xml
        assert "<xsd:operation>+</xsd:operation>" in xml
        assert "<xsd:nominalQuantity>5.0</xsd:nominalQuantity>" in xml

    def test_multiple_positions_all_present(self) -> None:
        positions = [
            {"article_number": "ART-001", "operation": "+", "nominal_quantity": 10.0},
            {"article_number": "ART-002", "operation": "-", "nominal_quantity": 3.5},
        ]
        xml = _build_smo("JOB-MULTI", positions)
        assert "ART-001" in xml
        assert "ART-002" in xml
        assert xml.count("<xsd:JobPosition>") == 2

    def test_namespaces_declared(self) -> None:
        xml = _build_smo("JOB-1", _ONE_POSITION)
        assert _NS_MAIN in xml
        assert _NS_XSD in xml
        assert "http://schemas.xmlsoap.org/soap/envelope/" in xml

    def test_is_valid_xml(self) -> None:
        import xml.etree.ElementTree as ET

        xml = _build_smo("JOB-1", _ONE_POSITION)
        ET.fromstring(xml)  # must not raise

    def test_escapes_special_chars_in_job_number(self) -> None:
        import xml.etree.ElementTree as ET

        xml = _build_smo("JOB&<>", _ONE_POSITION)
        assert "JOB&<>" not in xml
        root = ET.fromstring(xml)
        el = root.find(f".//{{{_NS_XSD}}}jobNumber")
        assert el is not None and el.text == "JOB&<>"

    def test_escapes_special_chars_in_article_number(self) -> None:
        import xml.etree.ElementTree as ET

        positions = [
            {"article_number": "ART&01", "operation": "+", "nominal_quantity": 1.0}
        ]
        xml = _build_smo("JOB-1", positions)
        root = ET.fromstring(xml)
        el = root.find(f".//{{{_NS_XSD}}}articleNumber")
        assert el is not None and el.text == "ART&01"

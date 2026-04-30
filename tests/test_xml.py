"""Tests for _xml module: envelope builders and parsers."""

from __future__ import annotations

from pathlib import Path

import pytest

from hanel_warehouse_gateway._xml import (
    build_register_article_envelope,
    extract_soap_fault,
    parse_return_value,
)

_FIXTURES = Path(__file__).parent / "fixtures"

NS_MAIN = "http://main.jws.com.hanel.de"
NS_XSD = "http://main.jws.com.hanel.de/xsd"


class TestBuildRegisterArticleEnvelope:
    def test_contains_article_number(self) -> None:
        xml = build_register_article_envelope("ART001", "Bolt M6", NS_MAIN, NS_XSD)
        assert "ART001" in xml

    def test_contains_article_name(self) -> None:
        xml = build_register_article_envelope("ART001", "Bolt M6", NS_MAIN, NS_XSD)
        assert "Bolt M6" in xml

    def test_contains_operation_tag(self) -> None:
        xml = build_register_article_envelope("ART001", "Bolt M6", NS_MAIN, NS_XSD)
        assert "sendAPDReqV01" in xml

    def test_contains_article_pool_data_record(self) -> None:
        xml = build_register_article_envelope("ART001", "Bolt M6", NS_MAIN, NS_XSD)
        assert "articlePoolDataRecord" in xml

    def test_uses_provided_namespaces(self) -> None:
        xml = build_register_article_envelope("X", "Y", NS_MAIN, NS_XSD)
        assert NS_MAIN in xml
        assert NS_XSD in xml

    def test_is_valid_xml(self) -> None:
        import xml.etree.ElementTree as ET

        xml = build_register_article_envelope("ART001", "Bolt M6", NS_MAIN, NS_XSD)
        ET.fromstring(xml)  # must not raise


class TestParseReturnValue:
    def test_success_fixture(self) -> None:
        xml = (_FIXTURES / "sendAPDReqV01_success.xml").read_text()
        assert parse_return_value(xml) == 0

    def test_error_fixture(self) -> None:
        xml = (_FIXTURES / "sendAPDReqV01_error.xml").read_text()
        assert parse_return_value(xml) == 1

    def test_missing_element_raises(self) -> None:
        xml = "<soapenv:Envelope xmlns:soapenv='http://schemas.xmlsoap.org/soap/envelope/'><soapenv:Body/></soapenv:Envelope>"
        with pytest.raises(ValueError, match="returnValue"):
            parse_return_value(xml)


class TestExtractSoapFault:
    def test_fault_fixture(self) -> None:
        xml = (_FIXTURES / "soap_fault.xml").read_text()
        result = extract_soap_fault(xml)
        assert result is not None
        fault_code, fault_string = result
        assert fault_code == "soapenv:Server"
        assert fault_string == "Internal error"

    def test_success_response_returns_none(self) -> None:
        xml = (_FIXTURES / "sendAPDReqV01_success.xml").read_text()
        assert extract_soap_fault(xml) is None

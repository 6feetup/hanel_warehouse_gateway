"""Unit tests for _xml.py — envelope builders and response parsers."""

from __future__ import annotations

import pathlib

import pytest

from hanel_warehouse_gateway._xml import (
    build_cancel_order_envelope,
    build_get_inventory_envelope_v04,
    build_read_jobs_envelope,
    build_read_jobs_envelope_v02,
    build_register_article_envelope,
    build_register_article_envelope_v03,
    build_send_movement_order_envelope,
    build_send_movement_order_envelope_v02,
    parse_movement_results,
    parse_return_value,
    parse_stock_records,
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


class TestBuildReadJobsEnvelope:
    def test_mode_1_in_envelope(self) -> None:
        xml = build_read_jobs_envelope(1, _NS_MAIN, _NS_XSD)
        assert "<xsd:mode>1</xsd:mode>" in xml

    def test_mode_0_in_envelope(self) -> None:
        xml = build_read_jobs_envelope(0, _NS_MAIN, _NS_XSD)
        assert "<xsd:mode>0</xsd:mode>" in xml

    def test_contains_operation_name(self) -> None:
        xml = build_read_jobs_envelope(1, _NS_MAIN, _NS_XSD)
        assert "readAllJobsReqV01" in xml

    def test_uses_namespaces(self) -> None:
        xml = build_read_jobs_envelope(1, _NS_MAIN, _NS_XSD)
        assert _NS_MAIN in xml
        assert _NS_XSD in xml

    def test_is_valid_xml(self) -> None:
        import xml.etree.ElementTree as ET

        xml = build_read_jobs_envelope(1, _NS_MAIN, _NS_XSD)
        ET.fromstring(xml)  # must not raise


_EMPTY_JOBS_RESPONSE = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"'
    ' xmlns:main="http://main.jws.com.hanel.de"'
    ' xmlns:xsd="http://main.jws.com.hanel.de/xsd">'
    "<soapenv:Header/><soapenv:Body>"
    "<main:readAllJobsReqV01Response><main:return/></main:readAllJobsReqV01Response>"
    "</soapenv:Body></soapenv:Envelope>"
)

_OPERATION = "readAllJobsReqV01"


class TestParseMovementResults:
    def test_two_completed_jobs(self) -> None:
        xml = _fixture("read_jobs_response_mode1.xml")
        results = parse_movement_results(xml, _OPERATION, _NS_XSD)
        assert len(results) == 2

    def test_job_fields(self) -> None:
        xml = _fixture("read_jobs_response_mode1.xml")
        results = parse_movement_results(xml, _OPERATION, _NS_XSD)
        job = results[0]
        assert job["job_number"] == "ORD-003"
        assert job["job_status"] == 3
        assert job["job_date"] == "280426"
        assert job["job_time"] == "1430"
        assert job["job_priority"] == 1

    def test_position_fields(self) -> None:
        xml = _fixture("read_jobs_response_mode1.xml")
        results = parse_movement_results(xml, _OPERATION, _NS_XSD)
        pos = results[0]["positions"][0]  # type: ignore[index]
        assert pos["article_number"] == "ART-001"
        assert pos["actual_quantity"] == 50.0
        assert pos["container_size"] == 1
        assert pos["position_status"] == 1

    def test_partial_quantity_job(self) -> None:
        xml = _fixture("read_jobs_response_mode1.xml")
        results = parse_movement_results(xml, _OPERATION, _NS_XSD)
        pos = results[1]["positions"][0]  # type: ignore[index]
        assert pos["nominal_quantity"] == 40.0
        assert pos["actual_quantity"] == 15.0

    def test_empty_response_returns_empty_list(self) -> None:
        results = parse_movement_results(_EMPTY_JOBS_RESPONSE, _OPERATION, _NS_XSD)
        assert results == []

    def test_soap_fault_raises(self) -> None:
        xml = _fixture("response_soap_fault.xml")
        with pytest.raises(HanelGatewaySoapFaultError):
            parse_movement_results(xml, _OPERATION, _NS_XSD)

    def test_malformed_xml_raises_parse_error(self) -> None:
        with pytest.raises(HanelGatewayParseError):
            parse_movement_results("<not-xml", _OPERATION, _NS_XSD)

    def test_batch_number_present_in_v02_fixture(self) -> None:
        xml = _fixture("read_jobs_v02_response_mode1.xml")
        results = parse_movement_results(xml, "readAllJobsV02", _NS_XSD)
        assert results[0]["positions"][0]["batch_number"] == "LOT-A"  # type: ignore[index]

    def test_batch_number_absent_returns_none(self) -> None:
        xml = _fixture("read_jobs_v02_response_mode0.xml")
        results = parse_movement_results(xml, "readAllJobsV02", _NS_XSD)
        assert results[1]["positions"][0]["batch_number"] is None  # type: ignore[index]

    def test_v01_fixture_batch_number_is_none(self) -> None:
        xml = _fixture("read_jobs_response_mode1.xml")
        results = parse_movement_results(xml, "readAllJobsReqV01", _NS_XSD)
        assert results[0]["positions"][0]["batch_number"] is None  # type: ignore[index]


class TestParseStockRecords:
    def test_batch_number_present_in_v04_fixture(self) -> None:
        xml = _fixture("read_inventory_v04_response.xml")
        results = parse_stock_records(xml, "readAllAMDV04", _NS_XSD)
        assert results[0]["batch_number"] == "LOT-2024"

    def test_batch_number_absent_returns_none(self) -> None:
        xml = _fixture("read_inventory_v04_response.xml")
        results = parse_stock_records(xml, "readAllAMDV04", _NS_XSD)
        assert results[1]["batch_number"] is None

    def test_v01_fixture_batch_number_is_none(self) -> None:
        xml = _fixture("read_inventory_response.xml")
        results = parse_stock_records(xml, "readAllAMDReqV01", _NS_XSD)
        assert results[0]["batch_number"] is None


def _build_apd_v03(
    article_number: str,
    article_name: str,
    batch_number: str | None,
) -> str:
    return build_register_article_envelope_v03(
        article_number, article_name, batch_number, _NS_MAIN, _NS_XSD
    )


def _build_smo_v02(job_number: str, positions: list[dict[str, object]]) -> str:
    return build_send_movement_order_envelope_v02(
        job_number, positions, _NS_MAIN, _NS_XSD
    )


class TestBuildRegisterArticleEnvelopeV03:
    def test_contains_operation_tag(self) -> None:
        xml = _build_apd_v03("ART001", "Bolt M6", None)
        assert "sendAPDV03" in xml

    def test_contains_article_number(self) -> None:
        xml = _build_apd_v03("ART001", "Bolt M6", None)
        assert "ART001" in xml

    def test_batch_number_emitted_when_set(self) -> None:
        xml = _build_apd_v03("ART001", "Bolt M6", "LOT-X")
        assert "<xsd:batchNumber>LOT-X</xsd:batchNumber>" in xml

    def test_batch_number_absent_when_none(self) -> None:
        xml = _build_apd_v03("ART001", "Bolt M6", None)
        assert "batchNumber" not in xml

    def test_is_valid_xml(self) -> None:
        import xml.etree.ElementTree as ET
        xml = _build_apd_v03("ART001", "Bolt M6", "LOT-1")
        ET.fromstring(xml)


_ONE_POSITION_V02 = [
    {"article_number": "ART-001", "operation": "+", "nominal_quantity": 5.0}
]


class TestBuildSendMovementOrderEnvelopeV02:
    def test_contains_operation_tag(self) -> None:
        xml = _build_smo_v02("JOB-1", _ONE_POSITION_V02)
        assert "sendJobsV02" in xml

    def test_batch_number_emitted_when_set(self) -> None:
        positions = [
            {
                "article_number": "ART-001",
                "operation": "+",
                "nominal_quantity": 5.0,
                "batch_number": "LOT-A",
            }
        ]
        xml = _build_smo_v02("JOB-1", positions)
        assert "<xsd:batchNumber>LOT-A</xsd:batchNumber>" in xml

    def test_batch_number_absent_when_none(self) -> None:
        positions = [
            {
                "article_number": "ART-001",
                "operation": "+",
                "nominal_quantity": 5.0,
                "batch_number": None,
            }
        ]
        xml = _build_smo_v02("JOB-1", positions)
        assert "batchNumber" not in xml

    def test_batch_number_absent_when_key_missing(self) -> None:
        xml = _build_smo_v02("JOB-1", _ONE_POSITION_V02)
        assert "batchNumber" not in xml

    def test_is_valid_xml(self) -> None:
        import xml.etree.ElementTree as ET
        positions = [
            {
                "article_number": "ART-001",
                "operation": "+",
                "nominal_quantity": 5.0,
                "batch_number": "L1",
            }
        ]
        xml = _build_smo_v02("JOB-1", positions)
        ET.fromstring(xml)


class TestBuildReadJobsEnvelopeV02:
    def test_contains_operation_tag(self) -> None:
        xml = build_read_jobs_envelope_v02(1, _NS_MAIN, _NS_XSD)
        assert "readAllJobsV02" in xml

    def test_mode_1_in_envelope(self) -> None:
        xml = build_read_jobs_envelope_v02(1, _NS_MAIN, _NS_XSD)
        assert "<xsd:mode>1</xsd:mode>" in xml

    def test_mode_0_in_envelope(self) -> None:
        xml = build_read_jobs_envelope_v02(0, _NS_MAIN, _NS_XSD)
        assert "<xsd:mode>0</xsd:mode>" in xml

    def test_is_valid_xml(self) -> None:
        import xml.etree.ElementTree as ET
        xml = build_read_jobs_envelope_v02(1, _NS_MAIN, _NS_XSD)
        ET.fromstring(xml)


class TestBuildGetInventoryEnvelopeV04:
    def test_contains_operation_tag(self) -> None:
        xml = build_get_inventory_envelope_v04(_NS_MAIN)
        assert "readAllAMDV04" in xml

    def test_is_valid_xml(self) -> None:
        import xml.etree.ElementTree as ET
        xml = build_get_inventory_envelope_v04(_NS_MAIN)
        ET.fromstring(xml)

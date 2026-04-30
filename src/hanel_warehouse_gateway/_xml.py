"""PRIVATE helper: SOAP envelope construction and XML response parsing.

Private module — do not import directly. Access via operations.py.
XML templates use f-strings; parsing uses xml.etree.ElementTree.
"""

from __future__ import annotations

import datetime
import xml.etree.ElementTree as ET

from .exceptions import HanelGatewaySoapFaultError

_NS_SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
_NS_XSD = "http://main.jws.com.hanel.de/xsd"


def build_register_article_envelope(
    article_number: str,
    article_name: str,
    namespace_main: str,
    namespace_xsd: str,
) -> str:
    """Build the SOAP envelope for sendAPDReqV01."""
    raise NotImplementedError


def build_send_movement_order_envelope(
    job_number: str,
    positions: list[dict[str, object]],
    namespace_main: str,
    namespace_xsd: str,
) -> str:
    """Build the SOAP envelope for sendJobsReqV01."""
    raise NotImplementedError


def build_read_jobs_envelope(
    mode: int,
    namespace_main: str,
    namespace_xsd: str,
) -> str:
    """Build the SOAP envelope for readAllJobsReqV01.

    mode=0: all orders, mode=1: completed only.
    """
    raise NotImplementedError


def build_get_inventory_envelope(namespace_main: str) -> str:
    """Build the SOAP envelope for readAllAMDReqV01."""
    raise NotImplementedError


def build_cancel_order_envelope(
    job_number: str,
    namespace_main: str,
    namespace_xsd: str,
) -> str:
    """Build the SOAP envelope for deleteJobReqV01."""
    return (
        f'<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"'
        f' xmlns:main="{namespace_main}" xmlns:xsd="{namespace_xsd}">'
        "<soapenv:Header/>"
        "<soapenv:Body>"
        "<main:deleteJobReqV01>"
        "<main:param>"
        f"<xsd:jobNumber>{job_number}</xsd:jobNumber>"
        "</main:param>"
        "</main:deleteJobReqV01>"
        "</soapenv:Body>"
        "</soapenv:Envelope>"
    )


def parse_return_value(xml_text: str, operation: str) -> int:
    """Extract returnValue from a SOAP response envelope.

    Raises HanelGatewaySoapFaultError if a SOAP Fault is detected.
    """
    root = ET.fromstring(xml_text)

    fault = root.find(f".//{{{_NS_SOAP}}}Fault")
    if fault is not None:
        fault_code = fault.findtext("faultcode") or ""
        fault_string = fault.findtext("faultstring") or ""
        raise HanelGatewaySoapFaultError(
            message=f"SOAP fault in {operation}: {fault_string}",
            operation=operation,
            detail=fault_string,
            timestamp=datetime.datetime.utcnow().isoformat(),
            fault_string=fault_string,
            fault_code=fault_code,
        )

    el = root.find(f".//{{{_NS_XSD}}}returnValue")
    if el is None or el.text is None:
        raise ValueError(f"returnValue not found in response for {operation}")
    return int(el.text)


def parse_movement_results(xml_text: str) -> list[dict[str, object]]:
    """Extract the list of movement orders from a readAllJobsReqV01 response."""
    raise NotImplementedError


def parse_stock_records(xml_text: str) -> list[dict[str, object]]:
    """Extract the list of stock records from a readAllAMDReqV01 response."""
    raise NotImplementedError

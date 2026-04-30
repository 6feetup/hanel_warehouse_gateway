"""PRIVATE helper: SOAP envelope construction and XML response parsing.

Private module — do not import directly. Access via operations.py.
XML templates use f-strings; parsing uses xml.etree.ElementTree.
"""

from __future__ import annotations

import datetime
import xml.etree.ElementTree as ET

from .exceptions import HanelGatewayParseError, HanelGatewaySoapFaultError

_NS_SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
_NS_MAIN = "http://main.jws.com.hanel.de"
_NS_XSD = "http://main.jws.com.hanel.de/xsd"

_NAMESPACES: dict[str, str] = {
    "soapenv": _NS_SOAP,
    "main": _NS_MAIN,
    "xsd": _NS_XSD,
}


def _namespaces(namespace_xsd: str) -> dict[str, str]:
    """Return the namespace dict for find()/findall(), honoring config override."""
    return {**_NAMESPACES, "xsd": namespace_xsd}


def _xml_escape(value: str) -> str:
    """Escape characters that are reserved in XML text content and attributes."""
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def build_register_article_envelope(
    article_number: str,
    article_name: str,
    namespace_main: str,
    namespace_xsd: str,
) -> str:
    """Build the SOAP envelope for sendAPDReqV01."""
    article_number_escaped = _xml_escape(article_number)
    article_name_escaped = _xml_escape(article_name)
    return (
        f'<soapenv:Envelope xmlns:soapenv="{_NS_SOAP}"'
        f' xmlns:main="{namespace_main}"'
        f' xmlns:xsd="{namespace_xsd}">'
        f"<soapenv:Header/>"
        f"<soapenv:Body>"
        f"<main:sendAPDReqV01>"
        f"<main:param>"
        f"<xsd:articlePoolDataRecord>"
        f"<xsd:articleNumber>{article_number_escaped}</xsd:articleNumber>"
        f"<xsd:articleName>{article_name_escaped}</xsd:articleName>"
        f"</xsd:articlePoolDataRecord>"
        f"</main:param>"
        f"</main:sendAPDReqV01>"
        f"</soapenv:Body>"
        f"</soapenv:Envelope>"
    )


def build_send_movement_order_envelope(
    job_number: str,
    positions: list[dict[str, object]],
    namespace_main: str,
    namespace_xsd: str,
) -> str:
    """Build the SOAP envelope for sendJobsReqV01."""
    job_number_escaped = _xml_escape(job_number)
    positions_xml = "".join(
        f"<xsd:JobPosition>"
        f"<xsd:articleNumber>{_xml_escape(str(p['article_number']))}</xsd:articleNumber>"
        f"<xsd:operation>{_xml_escape(str(p['operation']))}</xsd:operation>"
        f"<xsd:nominalQuantity>{p['nominal_quantity']}</xsd:nominalQuantity>"
        f"</xsd:JobPosition>"
        for p in positions
    )
    return (
        f'<soapenv:Envelope xmlns:soapenv="{_NS_SOAP}"'
        f' xmlns:main="{namespace_main}"'
        f' xmlns:xsd="{namespace_xsd}">'
        f"<soapenv:Header/>"
        f"<soapenv:Body>"
        f"<main:sendJobsReqV01>"
        f"<main:param>"
        f"<xsd:job>"
        f"<xsd:jobNumber>{job_number_escaped}</xsd:jobNumber>"
        f"{positions_xml}"
        f"</xsd:job>"
        f"</main:param>"
        f"</main:sendJobsReqV01>"
        f"</soapenv:Body>"
        f"</soapenv:Envelope>"
    )


def build_read_jobs_envelope(
    mode: int,
    namespace_main: str,
    namespace_xsd: str,
) -> str:
    """Build the SOAP envelope for readAllJobsReqV01.

    mode=0: all orders, mode=1: completed only.
    """
    return (
        f'<soapenv:Envelope xmlns:soapenv="{_NS_SOAP}"'
        f' xmlns:main="{namespace_main}"'
        f' xmlns:xsd="{namespace_xsd}">'
        f"<soapenv:Header/>"
        f"<soapenv:Body>"
        f"<main:readAllJobsReqV01>"
        f"<main:param>"
        f"<xsd:mode>{mode}</xsd:mode>"
        f"</main:param>"
        f"</main:readAllJobsReqV01>"
        f"</soapenv:Body>"
        f"</soapenv:Envelope>"
    )


def build_get_inventory_envelope(namespace_main: str) -> str:
    """Build the SOAP envelope for readAllAMDReqV01."""
    return (
        f'<soapenv:Envelope xmlns:soapenv="{_NS_SOAP}"'
        f' xmlns:main="{namespace_main}">'
        f"<soapenv:Header/>"
        f"<soapenv:Body>"
        f"<main:readAllAMDReqV01/>"
        f"</soapenv:Body>"
        f"</soapenv:Envelope>"
    )


def build_cancel_order_envelope(
    job_number: str,
    namespace_main: str,
    namespace_xsd: str,
) -> str:
    """Build the SOAP envelope for deleteJobReqV01."""
    job_number_escaped = _xml_escape(job_number)
    return (
        f'<soapenv:Envelope xmlns:soapenv="{_NS_SOAP}"'
        f' xmlns:main="{namespace_main}" xmlns:xsd="{namespace_xsd}">'
        "<soapenv:Header/>"
        "<soapenv:Body>"
        "<main:deleteJobReqV01>"
        "<main:param>"
        f"<xsd:jobNumber>{job_number_escaped}</xsd:jobNumber>"
        "</main:param>"
        "</main:deleteJobReqV01>"
        "</soapenv:Body>"
        "</soapenv:Envelope>"
    )


def parse_return_value(xml_text: str, operation: str, namespace_xsd: str) -> int:
    """Extract returnValue from a SOAP response envelope.

    Raises HanelGatewaySoapFaultError if a SOAP Fault is detected.
    Raises HanelGatewayParseError if the response cannot be parsed.
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise HanelGatewayParseError(
            message=f"Malformed XML in response for {operation}",
            operation=operation,
            detail=str(exc),
            timestamp=datetime.datetime.utcnow().isoformat(),
        ) from exc

    ns = _namespaces(namespace_xsd)

    fault = root.find(".//soapenv:Fault", ns)
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

    el = root.find(".//xsd:returnValue", ns)
    if el is None or el.text is None:
        raise HanelGatewayParseError(
            message=f"returnValue not found in response for {operation}",
            operation=operation,
            detail=xml_text[:500],
            timestamp=datetime.datetime.utcnow().isoformat(),
        )
    return int(el.text)


def parse_movement_results(
    xml_text: str, operation: str, namespace_xsd: str
) -> list[dict[str, object]]:
    """Extract the list of movement orders from a readAllJobsReqV01 response."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise HanelGatewayParseError(
            message=f"Malformed XML in response for {operation}",
            operation=operation,
            detail=str(exc),
            timestamp=datetime.datetime.utcnow().isoformat(),
        ) from exc

    ns = _namespaces(namespace_xsd)

    fault = root.find(".//soapenv:Fault", ns)
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

    results = []
    for job_el in root.findall(".//xsd:job", ns):
        positions = []
        for pos_el in job_el.findall("xsd:JobPosition", ns):
            positions.append({
                "article_number": pos_el.findtext("xsd:articleNumber", "", ns),
                "operation": pos_el.findtext("xsd:operation", "", ns),
                "nominal_quantity": float(
                    pos_el.findtext("xsd:nominalQuantity", "0", ns)
                ),
                "actual_quantity": float(
                    pos_el.findtext("xsd:actualQuantity", "0", ns)
                ),
                "container_size": int(
                    pos_el.findtext("xsd:containerSize", "0", ns)
                ),
                "position_status": int(
                    pos_el.findtext("xsd:positionStatus", "0", ns)
                ),
            })
        results.append({
            "job_number": job_el.findtext("xsd:jobNumber", "", ns),
            "job_priority": int(job_el.findtext("xsd:jobPriority", "0", ns)),
            "job_status": int(job_el.findtext("xsd:jobStatus", "0", ns)),
            "job_date": job_el.findtext("xsd:jobDate", "", ns),
            "job_time": job_el.findtext("xsd:jobTime", "", ns),
            "positions": positions,
        })
    return results


def parse_stock_records(
    xml_text: str, operation: str, namespace_xsd: str
) -> list[dict[str, object]]:
    """Extract the list of stock records from a readAllAMDReqV01 response."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise HanelGatewayParseError(
            message=f"Malformed XML in response for {operation}",
            operation=operation,
            detail=str(exc),
            timestamp=datetime.datetime.utcnow().isoformat(),
        ) from exc

    ns = _namespaces(namespace_xsd)

    fault = root.find(".//soapenv:Fault", ns)
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

    results = []
    for rec_el in root.findall(".//xsd:articleMasterDataRecord", ns):
        results.append({
            "article_number": rec_el.findtext("xsd:articleNumber", "", ns),
            "article_name": rec_el.findtext("xsd:articleName", "", ns),
            "lift_number": int(rec_el.findtext("xsd:liftNumber", "0", ns)),
            "shelf_number": int(rec_el.findtext("xsd:shelfNumber", "0", ns)),
            "compartment_number": int(
                rec_el.findtext("xsd:compartmentNumber", "0", ns)
            ),
            "compartment_depth_number": int(
                rec_el.findtext("xsd:compartmentDepthNumber", "0", ns)
            ),
            "container_size": int(rec_el.findtext("xsd:containerSize", "0", ns)),
            "fifo": int(rec_el.findtext("xsd:fifo", "0", ns)),
            "inventory_at_storage_location": float(
                rec_el.findtext("xsd:inventoryAtStorageLocation", "0", ns)
            ),
            "minimum_inventory": float(
                rec_el.findtext("xsd:minimumInventory", "0", ns)
            ),
        })
    return results

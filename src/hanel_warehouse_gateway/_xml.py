"""PRIVATE helper: SOAP envelope construction and XML response parsing.

Private module — do not import directly. Access via operations.py.
XML templates use f-strings; parsing uses xml.etree.ElementTree.
"""

from __future__ import annotations


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
    raise NotImplementedError


def parse_return_value(xml_text: str) -> int:
    """Extract returnValue from a SOAP response envelope."""
    raise NotImplementedError


def parse_movement_results(xml_text: str) -> list[dict[str, object]]:
    """Extract the list of movement orders from a readAllJobsReqV01 response."""
    raise NotImplementedError


def parse_stock_records(xml_text: str) -> list[dict[str, object]]:
    """Extract the list of stock records from a readAllAMDReqV01 response."""
    raise NotImplementedError

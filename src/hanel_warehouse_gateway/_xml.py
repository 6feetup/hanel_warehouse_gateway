"""Helper PRIVATO: costruzione envelope SOAP e parsing risposte XML.

Modulo privato — non importare direttamente. Accesso tramite operations.py.
I template XML usano f-string; il parsing usa xml.etree.ElementTree.
"""

from __future__ import annotations


def build_register_article_envelope(
    article_number: str,
    article_name: str,
    namespace_main: str,
    namespace_xsd: str,
) -> str:
    """Costruisce l'envelope SOAP per sendAPDReqV01."""
    raise NotImplementedError


def build_send_movement_order_envelope(
    job_number: str,
    positions: list[dict[str, object]],
    namespace_main: str,
    namespace_xsd: str,
) -> str:
    """Costruisce l'envelope SOAP per sendJobsReqV01."""
    raise NotImplementedError


def build_read_jobs_envelope(
    mode: int,
    namespace_main: str,
    namespace_xsd: str,
) -> str:
    """Costruisce l'envelope SOAP per readAllJobsReqV01.

    mode=0: tutti gli ordini, mode=1: solo completati.
    """
    raise NotImplementedError


def build_get_inventory_envelope(namespace_main: str) -> str:
    """Costruisce l'envelope SOAP per readAllAMDReqV01."""
    raise NotImplementedError


def build_cancel_order_envelope(
    job_number: str,
    namespace_main: str,
    namespace_xsd: str,
) -> str:
    """Costruisce l'envelope SOAP per deleteJobReqV01."""
    raise NotImplementedError


def parse_return_value(xml_text: str) -> int:
    """Estrae returnValue da un envelope di risposta SOAP."""
    raise NotImplementedError


def parse_movement_results(xml_text: str) -> list[dict[str, object]]:
    """Estrae la lista di ordini di movimento da una risposta readAllJobsReqV01."""
    raise NotImplementedError


def parse_stock_records(xml_text: str) -> list[dict[str, object]]:
    """Estrae la lista di record di stock da una risposta readAllAMDReqV01."""
    raise NotImplementedError

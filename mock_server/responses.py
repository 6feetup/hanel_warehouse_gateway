from typing import List
from state import Job, ArticleMasterData

NS_SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
NS_MAIN = "http://main.jws.com.hanel.de"
NS_XSD  = "http://main.jws.com.hanel.de/xsd"

_ENVELOPE_OPEN = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<soapenv:Envelope'
    f' xmlns:soapenv="{NS_SOAP}"'
    f' xmlns:main="{NS_MAIN}"'
    f' xmlns:xsd="{NS_XSD}">'
    "<soapenv:Header/><soapenv:Body>"
)
_ENVELOPE_CLOSE = "</soapenv:Body></soapenv:Envelope>"


def simple_return_response(operation_response: str, return_value: int) -> str:
    return (
        _ENVELOPE_OPEN
        + f"<main:{operation_response}><main:return>"
        + f"<xsd:returnValue>{return_value}</xsd:returnValue>"
        + f"</main:return></main:{operation_response}>"
        + _ENVELOPE_CLOSE
    )


def _position_xml(p, include_batch: bool = False) -> str:
    batch_xml = (
        f"<xsd:batchNumber>{_esc(p.batch_number)}</xsd:batchNumber>"
        if include_batch and p.batch_number is not None
        else ""
    )
    return (
        f"<xsd:JobPosition>"
        f"<xsd:articleNumber>{_esc(p.article_number)}</xsd:articleNumber>"
        f"<xsd:operation>{_esc(p.operation)}</xsd:operation>"
        f"<xsd:nominalQuantity>{p.nominal_quantity}</xsd:nominalQuantity>"
        f"<xsd:actualQuantity>{p.actual_quantity}</xsd:actualQuantity>"
        f"<xsd:containerSize>{p.container_size}</xsd:containerSize>"
        f"<xsd:positionStatus>{p.position_status}</xsd:positionStatus>"
        f"{batch_xml}"
        f"</xsd:JobPosition>"
    )


def _jobs_xml(jobs: List[Job], include_batch: bool = False) -> str:
    result = ""
    for job in jobs:
        positions_xml = "".join(_position_xml(p, include_batch) for p in job.positions)
        result += (
            f"<xsd:job>"
            f"<xsd:jobNumber>{_esc(job.job_number)}</xsd:jobNumber>"
            f"<xsd:jobPriority>{job.job_priority}</xsd:jobPriority>"
            f"<xsd:jobStatus>{job.job_status}</xsd:jobStatus>"
            f"<xsd:jobDate>{job.job_date}</xsd:jobDate>"
            f"<xsd:jobTime>{job.job_time}</xsd:jobTime>"
            f"{positions_xml}"
            f"</xsd:job>"
        )
    return result


def read_jobs_response(jobs: List[Job]) -> str:
    return (
        _ENVELOPE_OPEN
        + "<main:readAllJobsReqV01Response><main:return>"
        + _jobs_xml(jobs, include_batch=False)
        + "</main:return></main:readAllJobsReqV01Response>"
        + _ENVELOPE_CLOSE
    )


def read_jobs_v02_response(jobs: List[Job]) -> str:
    return (
        _ENVELOPE_OPEN
        + "<main:readAllJobsV02Response><main:return>"
        + _jobs_xml(jobs, include_batch=True)
        + "</main:return></main:readAllJobsV02Response>"
        + _ENVELOPE_CLOSE
    )


def _amd_record_xml(r: ArticleMasterData, include_batch: bool = False) -> str:
    batch_xml = (
        f"<xsd:batchNumber>{_esc(r.batch_number)}</xsd:batchNumber>"
        if include_batch and r.batch_number is not None
        else ""
    )
    return (
        f"<xsd:articleMasterDataRecord>"
        f"<xsd:articleNumber>{_esc(r.article_number)}</xsd:articleNumber>"
        f"<xsd:articleName>{_esc(r.article_name)}</xsd:articleName>"
        f"<xsd:liftNumber>{r.lift_number}</xsd:liftNumber>"
        f"<xsd:shelfNumber>{r.shelf_number}</xsd:shelfNumber>"
        f"<xsd:compartmentNumber>{r.compartment_number}</xsd:compartmentNumber>"
        f"<xsd:compartmentDepthNumber>{r.compartment_depth_number}</xsd:compartmentDepthNumber>"
        f"<xsd:containerSize>{r.container_size}</xsd:containerSize>"
        f"<xsd:fifo>{r.fifo}</xsd:fifo>"
        f"<xsd:inventoryAtStorageLocation>{r.inventory_at_storage_location}</xsd:inventoryAtStorageLocation>"
        f"<xsd:minimumInventory>{r.minimum_inventory}</xsd:minimumInventory>"
        f"{batch_xml}"
        f"</xsd:articleMasterDataRecord>"
    )


def read_amd_response(records: List[ArticleMasterData]) -> str:
    records_xml = "".join(_amd_record_xml(r, include_batch=False) for r in records)
    return (
        _ENVELOPE_OPEN
        + "<main:readAllAMDReqV01Response><main:return>"
        + records_xml
        + "</main:return></main:readAllAMDReqV01Response>"
        + _ENVELOPE_CLOSE
    )


def read_amd_v04_response(records: List[ArticleMasterData]) -> str:
    records_xml = "".join(_amd_record_xml(r, include_batch=True) for r in records)
    return (
        _ENVELOPE_OPEN
        + "<main:readAllAMDV04Response><main:return>"
        + records_xml
        + "</main:return></main:readAllAMDV04Response>"
        + _ENVELOPE_CLOSE
    )


def soap_fault_response(message: str) -> str:
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<soapenv:Envelope xmlns:soapenv="{NS_SOAP}">'
        f"<soapenv:Body><soapenv:Fault>"
        f"<faultcode>soapenv:Server</faultcode>"
        f"<faultstring>{_esc(message)}</faultstring>"
        f"</soapenv:Fault></soapenv:Body></soapenv:Envelope>"
    )


def _esc(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

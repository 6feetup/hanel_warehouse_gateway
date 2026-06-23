import time
import xml.etree.ElementTree as ET
from datetime import datetime

from state import ArticleMasterData, Job, JobPosition, MockState, complete_job
from responses import (
    read_amd_response,
    read_amd_v04_response,
    read_jobs_response,
    read_jobs_v02_response,
    simple_return_response,
)

NS_MAIN = "http://main.jws.com.hanel.de"
NS_XSD = "http://main.jws.com.hanel.de/xsd"
_BODY = "{http://schemas.xmlsoap.org/soap/envelope/}Body"


def handle_send_apd(root: ET.Element, state: MockState) -> str:
    body = root.find(_BODY)
    param = body[0].find(f"{{{NS_MAIN}}}param")
    record = param.find(f"{{{NS_XSD}}}articlePoolDataRecord")
    article_number = (record.findtext(f"{{{NS_XSD}}}articleNumber") or "").strip()
    article_name = (record.findtext(f"{{{NS_XSD}}}articleName") or "").strip()
    with state._lock:
        state.articles[article_number] = {
            "article_number": article_number,
            "article_name": article_name,
        }
        for rec in state.inventory:
            if rec.article_number == article_number:
                rec.article_name = article_name
    return simple_return_response("sendAPDReqV01Response", 0)


def handle_send_apd_v03(root: ET.Element, state: MockState) -> str:
    body = root.find(_BODY)
    param = body[0].find(f"{{{NS_MAIN}}}param")
    record = param.find(f"{{{NS_XSD}}}articlePoolDataRecord")
    article_number = (record.findtext(f"{{{NS_XSD}}}articleNumber") or "").strip()
    article_name = (record.findtext(f"{{{NS_XSD}}}articleName") or "").strip()
    batch_number = record.findtext(f"{{{NS_XSD}}}batchNumber") or None
    with state._lock:
        state.articles[article_number] = {
            "article_number": article_number,
            "article_name": article_name,
            "batch_number": batch_number,
        }
        for rec in state.inventory:
            if rec.article_number == article_number:
                rec.article_name = article_name
                if batch_number is not None:
                    rec.batch_number = batch_number
    return simple_return_response("sendAPDReqV03Response", 0)


def handle_send_jobs(root: ET.Element, state: MockState) -> str:
    body = root.find(_BODY)
    param = body[0].find(f"{{{NS_MAIN}}}param")
    job_el = param.find(f"{{{NS_XSD}}}job")
    job_number = (job_el.findtext(f"{{{NS_XSD}}}jobNumber") or "").strip()
    positions = []
    for pos_el in job_el.findall(f"{{{NS_XSD}}}JobPosition"):
        positions.append(
            JobPosition(
                article_number=(pos_el.findtext(f"{{{NS_XSD}}}articleNumber") or "").strip(),
                operation=(pos_el.findtext(f"{{{NS_XSD}}}operation") or "+").strip(),
                nominal_quantity=float(pos_el.findtext(f"{{{NS_XSD}}}nominalQuantity") or 0),
                actual_quantity=0.0,
                container_size=1,
                position_status=0,
            )
        )
    dt = datetime.now()
    job = Job(
        job_number=job_number,
        job_priority=1,
        job_status=0,
        job_date=dt.strftime("%d%m%y"),
        job_time=dt.strftime("%H%M"),
        positions=positions,
        created_at=time.time(),
    )
    with state._lock:
        state.jobs[job_number] = job
    return simple_return_response("sendJobsReqV01Response", 0)


def handle_send_jobs_v02(root: ET.Element, state: MockState) -> str:
    body = root.find(_BODY)
    param = body[0].find(f"{{{NS_MAIN}}}param")
    job_el = param.find(f"{{{NS_XSD}}}job")
    job_number = (job_el.findtext(f"{{{NS_XSD}}}jobNumber") or "").strip()
    positions = []
    for pos_el in job_el.findall(f"{{{NS_XSD}}}JobPosition"):
        batch_number = pos_el.findtext(f"{{{NS_XSD}}}batchNumber") or None
        positions.append(
            JobPosition(
                article_number=(pos_el.findtext(f"{{{NS_XSD}}}articleNumber") or "").strip(),
                operation=(pos_el.findtext(f"{{{NS_XSD}}}operation") or "+").strip(),
                nominal_quantity=float(pos_el.findtext(f"{{{NS_XSD}}}nominalQuantity") or 0),
                actual_quantity=0.0,
                container_size=1,
                position_status=0,
                batch_number=batch_number,
            )
        )
    dt = datetime.now()
    job = Job(
        job_number=job_number,
        job_priority=1,
        job_status=0,
        job_date=dt.strftime("%d%m%y"),
        job_time=dt.strftime("%H%M"),
        positions=positions,
        created_at=time.time(),
    )
    with state._lock:
        state.jobs[job_number] = job
    return simple_return_response("sendJobsV02Response", 0)


def handle_read_jobs(root: ET.Element, state: MockState) -> str:
    body = root.find(_BODY)
    param = body[0].find(f"{{{NS_MAIN}}}param")
    mode = int(param.findtext(f"{{{NS_XSD}}}mode") or 0)
    with state._lock:
        if mode == 1:
            jobs = [j for j in state.jobs.values() if j.job_status == 3]
        else:
            jobs = list(state.jobs.values())
    return read_jobs_response(jobs)


def handle_read_jobs_v02(root: ET.Element, state: MockState) -> str:
    body = root.find(_BODY)
    param = body[0].find(f"{{{NS_MAIN}}}param")
    mode = int(param.findtext(f"{{{NS_XSD}}}mode") or 0)
    with state._lock:
        if mode == 1:
            jobs = [j for j in state.jobs.values() if j.job_status == 3]
        else:
            jobs = list(state.jobs.values())
    return read_jobs_v02_response(jobs)


def handle_read_amd(root: ET.Element, state: MockState) -> str:
    with state._lock:
        records = list(state.inventory)
    return read_amd_response(records)


def handle_read_amd_v04(root: ET.Element, state: MockState) -> str:
    with state._lock:
        records = list(state.inventory)
    return read_amd_v04_response(records)


def handle_delete_job(root: ET.Element, state: MockState) -> str:
    body = root.find(_BODY)
    param = body[0].find(f"{{{NS_MAIN}}}param")
    job_number = (param.findtext(f"{{{NS_XSD}}}jobNumber") or "").strip()
    with state._lock:
        job = state.jobs.get(job_number)
        if job is None or job.job_status != 0:
            return_value = 1
        else:
            del state.jobs[job_number]
            return_value = 0
    return simple_return_response("deleteJobReqV01Response", return_value)

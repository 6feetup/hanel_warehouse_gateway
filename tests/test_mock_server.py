"""
Tests for the Hanel SOAP mock server.
Requires the server running at http://localhost:8080.

Start: docker compose up --build
Run: pytest tests/test_mock_server.py -v
"""
import xml.etree.ElementTree as ET

import pytest
import requests

BASE_URL = "http://localhost:8080"
SOAP_URL = f"{BASE_URL}/HanelService"
HEADERS = {"Content-Type": "text/xml; charset=utf-8"}

NS_XSD = "http://main.jws.com.hanel.de/xsd"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def post_soap(body: str) -> requests.Response:
    return requests.post(SOAP_URL, data=body.encode("utf-8"), headers=HEADERS)


def get_return_value(response_text: str) -> int:
    root = ET.fromstring(response_text)
    el = root.find(f".//{{{NS_XSD}}}returnValue")
    return int(el.text)


def envelope(operation_xml: str) -> str:
    return (
        '<soapenv:Envelope'
        ' xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"'
        ' xmlns:main="http://main.jws.com.hanel.de"'
        ' xmlns:xsd="http://main.jws.com.hanel.de/xsd">'
        "<soapenv:Header/>"
        f"<soapenv:Body>{operation_xml}</soapenv:Body>"
        "</soapenv:Envelope>"
    )


def send_apd(article_number: str, article_name: str) -> requests.Response:
    return post_soap(envelope(
        f"<main:sendAPDReqV01><main:param>"
        f"<xsd:articlePoolDataRecord>"
        f"<xsd:articleNumber>{article_number}</xsd:articleNumber>"
        f"<xsd:articleName>{article_name}</xsd:articleName>"
        f"</xsd:articlePoolDataRecord>"
        f"</main:param></main:sendAPDReqV01>"
    ))


def send_jobs(job_number: str, positions: list) -> requests.Response:
    pos_xml = "".join(
        f"<xsd:JobPosition>"
        f"<xsd:articleNumber>{p['article_number']}</xsd:articleNumber>"
        f"<xsd:operation>{p['operation']}</xsd:operation>"
        f"<xsd:nominalQuantity>{p['nominal_quantity']}</xsd:nominalQuantity>"
        f"</xsd:JobPosition>"
        for p in positions
    )
    return post_soap(envelope(
        f"<main:sendJobsReqV01><main:param>"
        f"<xsd:job>"
        f"<xsd:jobNumber>{job_number}</xsd:jobNumber>"
        f"{pos_xml}"
        f"</xsd:job>"
        f"</main:param></main:sendJobsReqV01>"
    ))


def read_jobs(mode: int) -> requests.Response:
    return post_soap(envelope(
        f"<main:readAllJobsReqV01><main:param>"
        f"<xsd:mode>{mode}</xsd:mode>"
        f"</main:param></main:readAllJobsReqV01>"
    ))


def read_amd() -> requests.Response:
    return post_soap(envelope("<main:readAllAMDReqV01/>"))


def delete_job(job_number: str) -> requests.Response:
    return post_soap(envelope(
        f"<main:deleteJobReqV01><main:param>"
        f"<xsd:jobNumber>{job_number}</xsd:jobNumber>"
        f"</main:param></main:deleteJobReqV01>"
    ))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_state():
    requests.post(f"{BASE_URL}/admin/reset")
    yield


# ---------------------------------------------------------------------------
# sendAPDReqV01
# ---------------------------------------------------------------------------

class TestSendAPD:
    def test_registers_new_article(self):
        resp = send_apd("1999", "New Article")
        assert resp.status_code == 200
        assert get_return_value(resp.text) == 0

    def test_article_appears_in_state(self):
        send_apd("1999", "New Article")
        state = requests.get(f"{BASE_URL}/admin/state").json()
        assert "1999" in state["articles"]
        assert state["articles"]["1999"]["article_name"] == "New Article"

    def test_updates_existing_article(self):
        send_apd("1001", "Updated Name")
        state = requests.get(f"{BASE_URL}/admin/state").json()
        assert state["articles"]["1001"]["article_name"] == "Updated Name"


# ---------------------------------------------------------------------------
# sendJobsReqV01
# ---------------------------------------------------------------------------

class TestSendJobs:
    def test_send_job_returns_0(self):
        lines = [
            {"article_number": "1001", "operation": "+", "nominal_quantity": 5.0}
        ]
        resp = send_jobs("JOB-TEST", lines)
        assert resp.status_code == 200
        assert get_return_value(resp.text) == 0

    def test_new_job_has_status_0(self):
        lines = [
            {"article_number": "1001", "operation": "+", "nominal_quantity": 5.0}
        ]
        send_jobs("JOB-TEST", lines)
        state = requests.get(f"{BASE_URL}/admin/state").json()
        assert state["jobs"]["JOB-TEST"]["job_status"] == 0

    def test_job_with_multiple_positions(self):
        positions = [
            {"article_number": "1001", "operation": "+", "nominal_quantity": 10.0},
            {"article_number": "1002", "operation": "-", "nominal_quantity": 3.0},
        ]
        resp = send_jobs("JOB-MULTI", positions)
        assert get_return_value(resp.text) == 0
        state = requests.get(f"{BASE_URL}/admin/state").json()
        assert len(state["jobs"]["JOB-MULTI"]["positions"]) == 2


# ---------------------------------------------------------------------------
# readAllJobsReqV01
# ---------------------------------------------------------------------------

class TestReadAllJobs:
    def test_mode_0_returns_all_jobs(self):
        resp = read_jobs(0)
        assert resp.status_code == 200
        root = ET.fromstring(resp.text)
        jobs = root.findall(f".//{{{NS_XSD}}}job")
        assert len(jobs) == 4

    def test_mode_1_returns_only_completed(self):
        resp = read_jobs(1)
        assert resp.status_code == 200
        root = ET.fromstring(resp.text)
        jobs = root.findall(f".//{{{NS_XSD}}}job")
        assert len(jobs) == 2

    def test_new_job_appears_in_mode_0(self):
        lines = [
            {"article_number": "1001", "operation": "+", "nominal_quantity": 1.0}
        ]
        send_jobs("JOB-NEW", lines)
        root = ET.fromstring(read_jobs(0).text)
        job_numbers = [
            j.findtext(f"{{{NS_XSD}}}jobNumber")
            for j in root.findall(f".//{{{NS_XSD}}}job")
        ]
        assert "JOB-NEW" in job_numbers

    def test_new_job_not_in_mode_1(self):
        lines = [
            {"article_number": "1001", "operation": "+", "nominal_quantity": 1.0}
        ]
        send_jobs("JOB-NEW", lines)
        root = ET.fromstring(read_jobs(1).text)
        job_numbers = [
            j.findtext(f"{{{NS_XSD}}}jobNumber")
            for j in root.findall(f".//{{{NS_XSD}}}job")
        ]
        assert "JOB-NEW" not in job_numbers

    def test_after_complete_all_appears_in_mode_1(self):
        lines = [
            {"article_number": "1001", "operation": "+", "nominal_quantity": 1.0}
        ]
        send_jobs("JOB-NEW", lines)
        requests.post(f"{BASE_URL}/admin/complete-all")
        root = ET.fromstring(read_jobs(1).text)
        job_numbers = [
            j.findtext(f"{{{NS_XSD}}}jobNumber")
            for j in root.findall(f".//{{{NS_XSD}}}job")
        ]
        assert "JOB-NEW" in job_numbers


# ---------------------------------------------------------------------------
# readAllAMDReqV01
# ---------------------------------------------------------------------------

class TestReadAllAMD:
    def test_returns_inventory_records(self):
        resp = read_amd()
        assert resp.status_code == 200
        root = ET.fromstring(resp.text)
        records = root.findall(f".//{{{NS_XSD}}}article")
        assert len(records) == 6

    def test_record_with_lift_zero_present(self):
        root = ET.fromstring(read_amd().text)
        lift_zeros = [
            r for r in root.findall(f".//{{{NS_XSD}}}article")
            if r.findtext(f"{{{NS_XSD}}}liftNumber") == "0"
        ]
        assert len(lift_zeros) >= 1


# ---------------------------------------------------------------------------
# deleteJobReqV01
# ---------------------------------------------------------------------------

class TestDeleteJob:
    def test_delete_queued_job_returns_0(self):
        resp = delete_job("ORD-001")
        assert resp.status_code == 200
        assert get_return_value(resp.text) == 0

    def test_deleted_job_no_longer_appears(self):
        delete_job("ORD-001")
        root = ET.fromstring(read_jobs(0).text)
        job_numbers = [
            j.findtext(f"{{{NS_XSD}}}jobNumber")
            for j in root.findall(f".//{{{NS_XSD}}}job")
        ]
        assert "ORD-001" not in job_numbers

    def test_delete_completed_job_returns_1(self):
        resp = delete_job("ORD-003")
        assert get_return_value(resp.text) == 1

    def test_delete_nonexistent_job_returns_1(self):
        resp = delete_job("NON-EXISTENT")
        assert get_return_value(resp.text) == 1

    def test_delete_in_progress_job_returns_1(self):
        resp = delete_job("ORD-002")
        assert get_return_value(resp.text) == 1


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------

class TestAdmin:
    def test_state_returns_json(self):
        resp = requests.get(f"{BASE_URL}/admin/state")
        assert resp.status_code == 200
        data = resp.json()
        assert "articles" in data
        assert "jobs" in data
        assert "inventory" in data

    def test_reset_restores_initial_data(self):
        send_apd("1998", "Extra")
        requests.post(f"{BASE_URL}/admin/reset")
        state = requests.get(f"{BASE_URL}/admin/state").json()
        assert "1998" not in state["articles"]
        assert len(state["articles"]) == 3

    def test_complete_all_completes_pending_jobs(self):
        lines = [
            {"article_number": "1001", "operation": "+", "nominal_quantity": 2.0}
        ]
        send_jobs("JOB-PEND", lines)
        resp = requests.post(f"{BASE_URL}/admin/complete-all")
        assert resp.status_code == 200
        assert "JOB-PEND" in resp.json()["completed"]
        state = requests.get(f"{BASE_URL}/admin/state").json()
        assert state["jobs"]["JOB-PEND"]["job_status"] == 3

    def test_unknown_operation_returns_soap_fault(self):
        resp = post_soap(envelope("<main:unknownOperation/>"))
        assert resp.status_code == 500
        assert "Fault" in resp.text


# ---------------------------------------------------------------------------
# V02/V03/V04 helpers
# ---------------------------------------------------------------------------

def send_apd_v03(
    article_number: str, article_name: str, batch_number: str = None
) -> requests.Response:
    batch_xml = (
        f"<xsd:batchNumber>{batch_number}</xsd:batchNumber>" if batch_number else ""
    )
    return post_soap(envelope(
        f"<main:sendAPDReqV03><main:param>"
        f"<xsd:articlePoolDataRecord>"
        f"<xsd:articleNumber>{article_number}</xsd:articleNumber>"
        f"<xsd:articleName>{article_name}</xsd:articleName>"
        f"{batch_xml}"
        f"</xsd:articlePoolDataRecord>"
        f"</main:param></main:sendAPDReqV03>"
    ))


def send_jobs_v02(job_number: str, positions: list) -> requests.Response:
    pos_xml = ""
    for p in positions:
        batch_xml = (
            f"<xsd:batchNumber>{p['batch_number']}</xsd:batchNumber>"
            if p.get("batch_number")
            else ""
        )
        pos_xml += (
            f"<xsd:JobPosition>"
            f"<xsd:articleNumber>{p['article_number']}</xsd:articleNumber>"
            f"<xsd:operation>{p['operation']}</xsd:operation>"
            f"<xsd:nominalQuantity>{p['nominal_quantity']}</xsd:nominalQuantity>"
            f"{batch_xml}"
            f"</xsd:JobPosition>"
        )
    return post_soap(envelope(
        f"<main:sendJobsV02><main:param>"
        f"<xsd:job>"
        f"<xsd:jobNumber>{job_number}</xsd:jobNumber>"
        f"{pos_xml}"
        f"</xsd:job>"
        f"</main:param></main:sendJobsV02>"
    ))


def read_jobs_v02(mode: int) -> requests.Response:
    return post_soap(envelope(
        f"<main:readAllJobsV02><main:param>"
        f"<xsd:mode>{mode}</xsd:mode>"
        f"</main:param></main:readAllJobsV02>"
    ))


def read_amd_v04() -> requests.Response:
    return post_soap(envelope("<main:readAllAMDV04/>"))


# ---------------------------------------------------------------------------
# sendAPDReqV03
# ---------------------------------------------------------------------------

class TestSendAPDV03:
    def test_registers_article_without_batch(self):
        resp = send_apd_v03("3001", "V03 Article")
        assert resp.status_code == 200
        assert get_return_value(resp.text) == 0

    def test_registers_article_with_batch(self):
        resp = send_apd_v03("3001", "V03 Article", batch_number="LOT-001")
        assert resp.status_code == 200
        assert get_return_value(resp.text) == 0

    def test_response_tag_is_sendAPDReqV03Response(self):
        resp = send_apd_v03("3001", "V03 Article", batch_number="LOT-X")
        assert "sendAPDReqV03Response" in resp.text

    def test_article_appears_in_state(self):
        send_apd_v03("3002", "New V03 Article", batch_number="LOT-A")
        state = requests.get(f"{BASE_URL}/admin/state").json()
        assert "3002" in state["articles"]


# ---------------------------------------------------------------------------
# sendJobsV02
# ---------------------------------------------------------------------------

class TestSendJobsV02:
    def test_send_job_returns_0(self):
        positions = [
            {"article_number": "1001", "operation": "+", "nominal_quantity": 5.0, "batch_number": "LOT-B"}  # noqa: E501
        ]
        resp = send_jobs_v02("JOB-V02-1", positions)
        assert resp.status_code == 200
        assert get_return_value(resp.text) == 0

    def test_response_tag_is_sendJobsV02Response(self):
        positions = [
            {"article_number": "1001", "operation": "+", "nominal_quantity": 5.0}
        ]
        resp = send_jobs_v02("JOB-V02-2", positions)
        assert "sendJobsV02Response" in resp.text

    def test_job_with_batch_stored(self):
        positions = [
            {"article_number": "1001", "operation": "+", "nominal_quantity": 3.0, "batch_number": "LOT-C"}  # noqa: E501
        ]
        send_jobs_v02("JOB-V02-3", positions)
        state = requests.get(f"{BASE_URL}/admin/state").json()
        pos = state["jobs"]["JOB-V02-3"]["positions"][0]
        assert pos["batch_number"] == "LOT-C"

    def test_job_without_batch_stored_as_none(self):
        positions = [
            {"article_number": "1001", "operation": "+", "nominal_quantity": 3.0}
        ]
        send_jobs_v02("JOB-V02-4", positions)
        state = requests.get(f"{BASE_URL}/admin/state").json()
        pos = state["jobs"]["JOB-V02-4"]["positions"][0]
        assert pos["batch_number"] is None


# ---------------------------------------------------------------------------
# readAllJobsV02
# ---------------------------------------------------------------------------

class TestReadAllJobsV02:
    def test_mode_0_returns_all_jobs(self):
        resp = read_jobs_v02(0)
        assert resp.status_code == 200
        root = ET.fromstring(resp.text)
        jobs = root.findall(f".//{{{NS_XSD}}}job")
        assert len(jobs) >= 1

    def test_response_tag_is_readAllJobsV02Response(self):
        resp = read_jobs_v02(0)
        assert "readAllJobsV02Response" in resp.text

    def test_batch_number_present_in_response(self):
        positions = [
            {"article_number": "1001", "operation": "+", "nominal_quantity": 2.0, "batch_number": "LOT-D"}  # noqa: E501
        ]
        send_jobs_v02("JOB-V02-LOT", positions)
        requests.post(f"{BASE_URL}/admin/complete-all")
        root = ET.fromstring(read_jobs_v02(1).text)
        jobs = root.findall(f".//{{{NS_XSD}}}job")
        v02_job = next(
            (j for j in jobs if j.findtext(f"{{{NS_XSD}}}jobNumber") == "JOB-V02-LOT"),
            None,
        )
        assert v02_job is not None
        pos = v02_job.find(f".//{{{NS_XSD}}}JobPosition")
        batch = pos.findtext(f"{{{NS_XSD}}}batchNumber")
        assert batch == "LOT-D"

    def test_mode_1_returns_completed_only(self):
        positions = [
            {"article_number": "1001", "operation": "+", "nominal_quantity": 1.0}
        ]
        send_jobs_v02("JOB-V02-PEND", positions)
        root_before = ET.fromstring(read_jobs_v02(1).text)
        job_numbers_before = [
            j.findtext(f"{{{NS_XSD}}}jobNumber")
            for j in root_before.findall(f".//{{{NS_XSD}}}job")
        ]
        assert "JOB-V02-PEND" not in job_numbers_before
        requests.post(f"{BASE_URL}/admin/complete-all")
        root_after = ET.fromstring(read_jobs_v02(1).text)
        job_numbers_after = [
            j.findtext(f"{{{NS_XSD}}}jobNumber")
            for j in root_after.findall(f".//{{{NS_XSD}}}job")
        ]
        assert "JOB-V02-PEND" in job_numbers_after


# ---------------------------------------------------------------------------
# readAllAMDV04
# ---------------------------------------------------------------------------

class TestReadAllAMDV04:
    def test_returns_inventory_records(self):
        resp = read_amd_v04()
        assert resp.status_code == 200
        root = ET.fromstring(resp.text)
        records = root.findall(f".//{{{NS_XSD}}}article")
        assert len(records) >= 1

    def test_response_tag_is_readAllAMDResV04(self):
        resp = read_amd_v04()
        assert "readAllAMDResV04" in resp.text


# ---------------------------------------------------------------------------
# Backward compatibility: V01 and V02 on the same mock state
# ---------------------------------------------------------------------------

class TestBackwardCompatibility:
    def test_v01_send_apd_still_works(self):
        resp = send_apd("1997", "Compat Article")
        assert resp.status_code == 200
        assert get_return_value(resp.text) == 0

    def test_v01_send_jobs_still_works(self):
        positions = [
            {"article_number": "1001", "operation": "+", "nominal_quantity": 1.0}
        ]
        resp = send_jobs("JOB-COMPAT-V01", positions)
        assert resp.status_code == 200
        assert get_return_value(resp.text) == 0

    def test_v01_and_v02_jobs_coexist_in_state(self):
        positions = [
            {"article_number": "1001", "operation": "+", "nominal_quantity": 1.0}
        ]
        send_jobs("JOB-V01-COEX", positions)
        send_jobs_v02("JOB-V02-COEX", positions)
        state = requests.get(f"{BASE_URL}/admin/state").json()
        assert "JOB-V01-COEX" in state["jobs"]
        assert "JOB-V02-COEX" in state["jobs"]

    def test_v01_read_jobs_does_not_include_batch_tag(self):
        positions = [
            {"article_number": "1001", "operation": "+", "nominal_quantity": 1.0, "batch_number": "LOT-X"}  # noqa: E501
        ]
        send_jobs_v02("JOB-MIXED", positions)
        requests.post(f"{BASE_URL}/admin/complete-all")
        resp = read_jobs(1)
        assert "batchNumber" not in resp.text

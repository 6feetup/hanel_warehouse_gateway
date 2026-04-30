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
        resp = send_apd("ART-NEW", "New Article")
        assert resp.status_code == 200
        assert get_return_value(resp.text) == 0

    def test_article_appears_in_state(self):
        send_apd("ART-NEW", "New Article")
        state = requests.get(f"{BASE_URL}/admin/state").json()
        assert "ART-NEW" in state["articles"]
        assert state["articles"]["ART-NEW"]["article_name"] == "New Article"

    def test_updates_existing_article(self):
        send_apd("ART-001", "Updated Name")
        state = requests.get(f"{BASE_URL}/admin/state").json()
        assert state["articles"]["ART-001"]["article_name"] == "Updated Name"


# ---------------------------------------------------------------------------
# sendJobsReqV01
# ---------------------------------------------------------------------------

class TestSendJobs:
    def test_send_job_returns_0(self):
        lines = [
            {"article_number": "ART-001", "operation": "+", "nominal_quantity": 5.0}
        ]
        resp = send_jobs("JOB-TEST", lines)
        assert resp.status_code == 200
        assert get_return_value(resp.text) == 0

    def test_new_job_has_status_0(self):
        lines = [
            {"article_number": "ART-001", "operation": "+", "nominal_quantity": 5.0}
        ]
        send_jobs("JOB-TEST", lines)
        state = requests.get(f"{BASE_URL}/admin/state").json()
        assert state["jobs"]["JOB-TEST"]["job_status"] == 0

    def test_job_with_multiple_positions(self):
        positions = [
            {"article_number": "ART-001", "operation": "+", "nominal_quantity": 10.0},
            {"article_number": "ART-002", "operation": "-", "nominal_quantity": 3.0},
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
            {"article_number": "ART-001", "operation": "+", "nominal_quantity": 1.0}
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
            {"article_number": "ART-001", "operation": "+", "nominal_quantity": 1.0}
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
            {"article_number": "ART-001", "operation": "+", "nominal_quantity": 1.0}
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
        records = root.findall(f".//{{{NS_XSD}}}articleMasterData")
        assert len(records) == 6

    def test_record_with_lift_zero_present(self):
        root = ET.fromstring(read_amd().text)
        lift_zeros = [
            r for r in root.findall(f".//{{{NS_XSD}}}articleMasterData")
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
        send_apd("ART-EXTRA", "Extra")
        requests.post(f"{BASE_URL}/admin/reset")
        state = requests.get(f"{BASE_URL}/admin/state").json()
        assert "ART-EXTRA" not in state["articles"]
        assert len(state["articles"]) == 3

    def test_complete_all_completes_pending_jobs(self):
        lines = [
            {"article_number": "ART-001", "operation": "+", "nominal_quantity": 2.0}
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

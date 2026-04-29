"""
Test del mock server SOAP Hanel.
Richiede il server in esecuzione su http://localhost:8080.

Avvio: docker compose up --build
Esecuzione: pytest tests/test_mock_server.py -v
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
    def test_registra_articolo_nuovo(self):
        resp = send_apd("ART-NEW", "Nuovo Articolo")
        assert resp.status_code == 200
        assert get_return_value(resp.text) == 0

    def test_articolo_compare_nello_stato(self):
        send_apd("ART-NEW", "Nuovo Articolo")
        state = requests.get(f"{BASE_URL}/admin/state").json()
        assert "ART-NEW" in state["articles"]
        assert state["articles"]["ART-NEW"]["article_name"] == "Nuovo Articolo"

    def test_aggiorna_articolo_esistente(self):
        send_apd("ART-001", "Nome Aggiornato")
        state = requests.get(f"{BASE_URL}/admin/state").json()
        assert state["articles"]["ART-001"]["article_name"] == "Nome Aggiornato"


# ---------------------------------------------------------------------------
# sendJobsReqV01
# ---------------------------------------------------------------------------

class TestSendJobs:
    def test_invia_ordine_ritorna_0(self):
        resp = send_jobs("JOB-TEST", [{"article_number": "ART-001", "operation": "+", "nominal_quantity": 5.0}])
        assert resp.status_code == 200
        assert get_return_value(resp.text) == 0

    def test_nuovo_ordine_ha_status_0(self):
        send_jobs("JOB-TEST", [{"article_number": "ART-001", "operation": "+", "nominal_quantity": 5.0}])
        state = requests.get(f"{BASE_URL}/admin/state").json()
        assert state["jobs"]["JOB-TEST"]["job_status"] == 0

    def test_ordine_con_piu_posizioni(self):
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
    def test_mode_0_ritorna_tutti_gli_ordini(self):
        resp = read_jobs(0)
        assert resp.status_code == 200
        root = ET.fromstring(resp.text)
        jobs = root.findall(f".//{{{NS_XSD}}}job")
        assert len(jobs) == 4

    def test_mode_1_ritorna_solo_completati(self):
        resp = read_jobs(1)
        assert resp.status_code == 200
        root = ET.fromstring(resp.text)
        jobs = root.findall(f".//{{{NS_XSD}}}job")
        assert len(jobs) == 2

    def test_nuovo_ordine_compare_in_mode_0(self):
        send_jobs("JOB-NEW", [{"article_number": "ART-001", "operation": "+", "nominal_quantity": 1.0}])
        root = ET.fromstring(read_jobs(0).text)
        job_numbers = [j.findtext(f"{{{NS_XSD}}}jobNumber") for j in root.findall(f".//{{{NS_XSD}}}job")]
        assert "JOB-NEW" in job_numbers

    def test_nuovo_ordine_non_compare_in_mode_1(self):
        send_jobs("JOB-NEW", [{"article_number": "ART-001", "operation": "+", "nominal_quantity": 1.0}])
        root = ET.fromstring(read_jobs(1).text)
        job_numbers = [j.findtext(f"{{{NS_XSD}}}jobNumber") for j in root.findall(f".//{{{NS_XSD}}}job")]
        assert "JOB-NEW" not in job_numbers

    def test_dopo_complete_all_compare_in_mode_1(self):
        send_jobs("JOB-NEW", [{"article_number": "ART-001", "operation": "+", "nominal_quantity": 1.0}])
        requests.post(f"{BASE_URL}/admin/complete-all")
        root = ET.fromstring(read_jobs(1).text)
        job_numbers = [j.findtext(f"{{{NS_XSD}}}jobNumber") for j in root.findall(f".//{{{NS_XSD}}}job")]
        assert "JOB-NEW" in job_numbers


# ---------------------------------------------------------------------------
# readAllAMDReqV01
# ---------------------------------------------------------------------------

class TestReadAllAMD:
    def test_ritorna_record_inventario(self):
        resp = read_amd()
        assert resp.status_code == 200
        root = ET.fromstring(resp.text)
        records = root.findall(f".//{{{NS_XSD}}}articleMasterData")
        assert len(records) == 6

    def test_record_con_lift_zero_presente(self):
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
    def test_cancella_ordine_in_coda_ritorna_0(self):
        resp = delete_job("ORD-001")
        assert resp.status_code == 200
        assert get_return_value(resp.text) == 0

    def test_ordine_cancellato_non_compare_piu(self):
        delete_job("ORD-001")
        root = ET.fromstring(read_jobs(0).text)
        job_numbers = [j.findtext(f"{{{NS_XSD}}}jobNumber") for j in root.findall(f".//{{{NS_XSD}}}job")]
        assert "ORD-001" not in job_numbers

    def test_cancella_ordine_completato_ritorna_1(self):
        resp = delete_job("ORD-003")
        assert get_return_value(resp.text) == 1

    def test_cancella_ordine_inesistente_ritorna_1(self):
        resp = delete_job("NON-ESISTE")
        assert get_return_value(resp.text) == 1

    def test_cancella_ordine_in_progress_ritorna_1(self):
        resp = delete_job("ORD-002")
        assert get_return_value(resp.text) == 1


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------

class TestAdmin:
    def test_state_ritorna_json(self):
        resp = requests.get(f"{BASE_URL}/admin/state")
        assert resp.status_code == 200
        data = resp.json()
        assert "articles" in data
        assert "jobs" in data
        assert "inventory" in data

    def test_reset_ripristina_dati_iniziali(self):
        send_apd("ART-EXTRA", "Extra")
        requests.post(f"{BASE_URL}/admin/reset")
        state = requests.get(f"{BASE_URL}/admin/state").json()
        assert "ART-EXTRA" not in state["articles"]
        assert len(state["articles"]) == 3

    def test_complete_all_completa_ordini_pendenti(self):
        send_jobs("JOB-PEND", [{"article_number": "ART-001", "operation": "+", "nominal_quantity": 2.0}])
        resp = requests.post(f"{BASE_URL}/admin/complete-all")
        assert resp.status_code == 200
        assert "JOB-PEND" in resp.json()["completed"]
        state = requests.get(f"{BASE_URL}/admin/state").json()
        assert state["jobs"]["JOB-PEND"]["job_status"] == 3

    def test_operazione_sconosciuta_ritorna_soap_fault(self):
        resp = post_soap(envelope("<main:operazioneInesistente/>"))
        assert resp.status_code == 500
        assert "Fault" in resp.text

import os
import threading
import time
import xml.etree.ElementTree as ET

from flask import Flask, Response, jsonify, request

from handlers import (
    handle_delete_job,
    handle_read_amd,
    handle_read_jobs,
    handle_send_apd,
    handle_send_jobs,
)
from responses import soap_fault_response
from state import complete_job, state

app = Flask(__name__)

_SOAP_BODY = "{http://schemas.xmlsoap.org/soap/envelope/}Body"

_DISPATCH = {
    "sendAPDReqV01": handle_send_apd,
    "sendJobsReqV01": handle_send_jobs,
    "readAllJobsReqV01": handle_read_jobs,
    "readAllAMDReqV01": handle_read_amd,
    "deleteJobReqV01": handle_delete_job,
}


def _operation_name(root: ET.Element) -> str:
    body = root.find(_SOAP_BODY)
    if body is None or len(body) == 0:
        raise ValueError("SOAP Body vuoto o mancante")
    tag = body[0].tag
    return tag.split("}")[1] if "}" in tag else tag


@app.route("/HanelService", methods=["POST"])
def soap_endpoint():
    try:
        root = ET.fromstring(request.data)
        op = _operation_name(root)
    except ET.ParseError as exc:
        return Response(
            soap_fault_response(f"XML parse error: {exc}"),
            status=400,
            content_type="text/xml; charset=utf-8",
        )
    except ValueError as exc:
        return Response(
            soap_fault_response(str(exc)),
            status=400,
            content_type="text/xml; charset=utf-8",
        )
    handler = _DISPATCH.get(op)
    if handler is None:
        return Response(
            soap_fault_response(f"Operazione sconosciuta: {op}"),
            status=500,
            content_type="text/xml; charset=utf-8",
        )
    xml_response = handler(root, state)
    return Response(xml_response, status=200, content_type="text/xml; charset=utf-8")


@app.route("/admin/state", methods=["GET"])
def admin_state():
    return jsonify(state.to_dict())


@app.route("/admin/reset", methods=["POST"])
def admin_reset():
    state.reset()
    return jsonify({"status": "ok", "message": "State restored to initial data"})


@app.route("/admin/complete-all", methods=["POST"])
def admin_complete_all():
    completed = []
    with state._lock:
        for job in state.jobs.values():
            if job.job_status in (0, 1, 2):
                complete_job(job)
                completed.append(job.job_number)
    return jsonify({"status": "ok", "completed": completed})


def _auto_complete_worker(interval: float) -> None:
    while True:
        time.sleep(interval)
        now = time.time()
        with state._lock:
            for job in state.jobs.values():
                if job.job_status in (0, 1, 2) and (now - job.created_at) >= interval:
                    complete_job(job)


if __name__ == "__main__":
    auto_seconds = float(os.environ.get("AUTO_COMPLETE_SECONDS", "10"))
    if auto_seconds > 0:
        t = threading.Thread(
            target=_auto_complete_worker,
            args=(auto_seconds,),
            daemon=True,
            name="auto-complete",
        )
        t.start()
    app.run(host="0.0.0.0", port=8080, debug=False)

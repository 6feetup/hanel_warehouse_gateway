import json
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List


@dataclass
class JobPosition:
    article_number: str
    operation: str
    nominal_quantity: float
    actual_quantity: float
    container_size: int
    position_status: int
    batch_number: str = None  # type: ignore[assignment]


@dataclass
class Job:
    job_number: str
    job_priority: int
    job_status: int
    job_date: str
    job_time: str
    positions: List[JobPosition]
    created_at: float = field(default_factory=time.time)


@dataclass
class ArticleMasterData:
    article_number: str
    article_name: str
    lift_number: int
    shelf_number: int
    compartment_number: int
    compartment_depth_number: int
    container_size: int
    fifo: int
    inventory_at_storage_location: float
    minimum_inventory: float
    batch_number: str = None  # type: ignore[assignment]


def _data_dir() -> str:
    return os.environ.get("MOCK_DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))


def _load_articles() -> Dict[str, dict]:
    path = os.path.join(_data_dir(), "articles.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_jobs() -> Dict[str, Job]:
    path = os.path.join(_data_dir(), "jobs.json")
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    jobs = {}
    for item in raw:
        positions = [JobPosition(**p) for p in item["positions"]]
        job = Job(
            job_number=item["job_number"],
            job_priority=item["job_priority"],
            job_status=item["job_status"],
            job_date=item["job_date"],
            job_time=item["job_time"],
            positions=positions,
            created_at=time.time(),
        )
        jobs[job.job_number] = job
    return jobs


def _load_inventory() -> List[ArticleMasterData]:
    path = os.path.join(_data_dir(), "inventory.json")
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return [ArticleMasterData(**r) for r in raw]


def complete_job(job: Job) -> None:
    dt = datetime.now()
    job.job_status = 3
    job.job_date = dt.strftime("%d%m%y")
    job.job_time = dt.strftime("%H%M")
    for pos in job.positions:
        pos.actual_quantity = pos.nominal_quantity
        pos.position_status = 1


class MockState:
    def __init__(self):
        self._lock = threading.Lock()
        self.articles: Dict[str, dict] = {}
        self.jobs: Dict[str, Job] = {}
        self.inventory: List[ArticleMasterData] = []
        self._reload()

    def reset(self) -> None:
        with self._lock:
            self._reload()

    def _reload(self) -> None:
        self.articles = _load_articles()
        self.jobs = _load_jobs()
        self.inventory = _load_inventory()

    def to_dict(self) -> dict:
        with self._lock:
            return {
                "articles": dict(self.articles),
                "jobs": {k: _job_to_dict(v) for k, v in self.jobs.items()},
                "inventory": [_amd_to_dict(r) for r in self.inventory],
            }


def _job_to_dict(job: Job) -> dict:
    return {
        "job_number": job.job_number,
        "job_priority": job.job_priority,
        "job_status": job.job_status,
        "job_date": job.job_date,
        "job_time": job.job_time,
        "positions": [
            {
                "article_number": p.article_number,
                "operation": p.operation,
                "nominal_quantity": p.nominal_quantity,
                "actual_quantity": p.actual_quantity,
                "container_size": p.container_size,
                "position_status": p.position_status,
                "batch_number": p.batch_number,
            }
            for p in job.positions
        ],
    }


def _amd_to_dict(r: ArticleMasterData) -> dict:
    return {
        "article_number": r.article_number,
        "article_name": r.article_name,
        "lift_number": r.lift_number,
        "shelf_number": r.shelf_number,
        "compartment_number": r.compartment_number,
        "compartment_depth_number": r.compartment_depth_number,
        "container_size": r.container_size,
        "fifo": r.fifo,
        "inventory_at_storage_location": r.inventory_at_storage_location,
        "minimum_inventory": r.minimum_inventory,
        "batch_number": r.batch_number,
    }


state = MockState()

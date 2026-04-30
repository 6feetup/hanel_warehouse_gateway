"""Public dataclasses of the hanel_warehouse_gateway module."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MovementLine:
    """Single line of a movement order to send to the warehouse."""

    article_number: str
    operation: str  # '+' = pick, '-' = load
    nominal_quantity: float


@dataclass
class MovementLineResult:
    """Result of a single movement line confirmed by the warehouse.

    If actual_quantity < nominal_quantity, stock was insufficient.
    """

    article_number: str
    operation: str
    nominal_quantity: float
    actual_quantity: float
    container_size: int
    position_status: int  # 0=pending, 1=completed


@dataclass
class MovementResult:
    """Complete result of a movement order."""

    job_number: str
    job_priority: int
    job_status: int   # 0=queued, 1=in progress, 2=partial, 3=completed
    job_date: str     # format DDMMYY
    job_time: str     # format HHMM
    positions: list[MovementLineResult] = field(default_factory=list)


@dataclass
class StockRecord:
    """Stock level of an article at a specific physical location.

    An article may appear in multiple records if distributed across several locations.
    """

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

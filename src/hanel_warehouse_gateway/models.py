"""Dataclass pubblici del modulo hanel_warehouse_gateway."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MovementLine:
    """Singola riga di un ordine di movimento da inviare al magazzino."""

    article_number: str
    operation: str  # '+' = pick, '-' = load
    nominal_quantity: float


@dataclass
class MovementLineResult:
    """Risultato di una singola riga di movimento confermata dal magazzino.

    Se actual_quantity < nominal_quantity, lo stock era insufficiente.
    """

    article_number: str
    operation: str
    nominal_quantity: float
    actual_quantity: float
    container_size: int
    position_status: int  # 0=pending, 1=completed


@dataclass
class MovementResult:
    """Risultato completo di un ordine di movimento."""

    job_number: str
    job_priority: int
    job_status: int   # 0=queued, 1=in progress, 2=partial, 3=completed
    job_date: str     # format DDMMYY
    job_time: str     # format HHMM
    positions: list[MovementLineResult] = field(default_factory=list)


@dataclass
class StockRecord:
    """Livello di stock di un articolo in una specifica posizione fisica.

    Un articolo può apparire in più record se distribuito su più ubicazioni.
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

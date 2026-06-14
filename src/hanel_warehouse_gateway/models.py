"""Public dataclasses of the hanel_warehouse_gateway module."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MovementLine:
    """Single line of a movement order to send to the warehouse.

    Used as input for :meth:`HanelWarehouseGateway.send_movement_order`; pass a
    list with at least one element.

    Attributes:
        article_number: Article code (max 40 chars). Must match an article
            already registered via ``register_article``.
        operation: Movement direction. ``"+"`` = pick (retrieve from the
            warehouse), ``"-"`` = load (store into the warehouse).
        nominal_quantity: Requested quantity. Must be greater than 0.
        batch_number: Lot/batch number (max 40 chars). Only used when
            ``lot_management_enabled=True`` in ``GatewayConfig``; if omitted,
            the warehouse selects the lot autonomously (e.g. FIFO).
    """

    article_number: str
    operation: str
    nominal_quantity: float
    batch_number: str | None = None


@dataclass
class MovementLineResult:
    """Result of a single movement line confirmed by the warehouse.

    Returned inside :class:`MovementResult.positions` by
    :meth:`HanelWarehouseGateway.get_completed_movements` and
    :meth:`HanelWarehouseGateway.get_all_orders`.

    Attributes:
        article_number: Article code.
        operation: Movement direction. ``"+"`` = pick, ``"-"`` = load.
        nominal_quantity: Quantity originally requested in the order.
        actual_quantity: Quantity actually moved by the warehouse. When
            ``actual_quantity < nominal_quantity`` the warehouse moved less
            than requested (e.g. insufficient stock); handling this
            discrepancy is the caller's responsibility.
        container_size: Container size code.
        position_status: ``0`` = pending, ``1`` = completed.
        batch_number: Lot actually moved by the warehouse. Populated only when
            ``lot_management_enabled=True`` in ``GatewayConfig``.
    """

    article_number: str
    operation: str
    nominal_quantity: float
    actual_quantity: float
    container_size: int
    position_status: int
    batch_number: str | None = None


@dataclass
class MovementResult:
    """Complete result of a movement order.

    Returned by :meth:`HanelWarehouseGateway.get_completed_movements` and
    :meth:`HanelWarehouseGateway.get_all_orders`.

    Attributes:
        job_number: Order identifier.
        job_priority: Priority assigned to the order by the warehouse.
        job_status: Order status. ``0`` = queued/pending, ``1`` = in progress,
            ``2`` = partially completed, ``3`` = completed.
        job_date: Date the order was processed, formatted ``DDMMYY``.
        job_time: Time the order was processed, formatted ``HHMM``.
        positions: Order lines with the quantities actually moved.
    """

    job_number: str
    job_priority: int
    job_status: int
    job_date: str
    job_time: str
    positions: list[MovementLineResult] = field(default_factory=list)


@dataclass
class StockRecord:
    """Stock level of an article at a specific physical location.

    Returned by :meth:`HanelWarehouseGateway.get_inventory`. An article may
    appear in multiple records if distributed across several locations: the
    total stock for an article is the sum of all records sharing the same
    ``article_number``.

    Attributes:
        article_number: Article code.
        article_name: Article description.
        lift_number: Warehouse/lift number. ``lift_number`` and
            ``shelf_number`` both ``0`` indicate an article present in the
            master registry but with no physical stock.
        shelf_number: Shelf number.
        compartment_number: X position within the shelf.
        compartment_depth_number: Y position within the shelf.
        container_size: Container size code.
        fifo: FIFO ordering value.
        inventory_at_storage_location: Quantity stored at this location.
        minimum_inventory: Configured minimum stock threshold.
        batch_number: Lot number. Populated only when
            ``lot_management_enabled=True`` in ``GatewayConfig``; with lot
            management active an article appears in one record per lot ×
            location.
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
    batch_number: str | None = None

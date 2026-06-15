"""Tests for the public dataclasses of hanel_warehouse_gateway."""

from __future__ import annotations

from hanel_warehouse_gateway import (
    MovementLine,
    MovementLineResult,
    MovementResult,
    StockRecord,
)


class TestMovementLine:
    def test_instantiation(self) -> None:
        line = MovementLine(
            article_number="1001", operation="+", nominal_quantity=10
        )
        assert line.article_number == "1001"
        assert line.operation == "+"
        assert line.nominal_quantity == 10

    def test_batch_number_default_none(self) -> None:
        line = MovementLine(
            article_number="1001", operation="+", nominal_quantity=1
        )
        assert line.batch_number is None

    def test_batch_number_explicit(self) -> None:
        line = MovementLine(
            article_number="1001",
            operation="+",
            nominal_quantity=1,
            batch_number="LOT-A",
        )
        assert line.batch_number == "LOT-A"


class TestMovementLineResult:
    def test_instantiation(self) -> None:
        result = MovementLineResult(
            article_number="1001",
            operation="+",
            nominal_quantity=10.0,
            actual_quantity=8.0,
            container_size=1,
            position_status=1,
        )
        assert result.actual_quantity == 8.0
        assert result.position_status == 1

    def test_batch_number_default_none(self) -> None:
        result = MovementLineResult(
            article_number="1001",
            operation="+",
            nominal_quantity=10.0,
            actual_quantity=8.0,
            container_size=1,
            position_status=1,
        )
        assert result.batch_number is None

    def test_batch_number_explicit(self) -> None:
        result = MovementLineResult(
            article_number="1001",
            operation="+",
            nominal_quantity=10.0,
            actual_quantity=8.0,
            container_size=1,
            position_status=1,
            batch_number="LOT-B",
        )
        assert result.batch_number == "LOT-B"


class TestMovementResult:
    def test_default_positions_empty(self) -> None:
        result = MovementResult(
            job_number="ORD001",
            job_priority=1,
            job_status=3,
            job_date="010124",
            job_time="1430",
        )
        assert result.positions == []

    def test_with_positions(self) -> None:
        line = MovementLineResult(
            article_number="1001",
            operation="+",
            nominal_quantity=5.0,
            actual_quantity=5.0,
            container_size=1,
            position_status=1,
        )
        result = MovementResult(
            job_number="ORD001",
            job_priority=1,
            job_status=3,
            job_date="010124",
            job_time="1430",
            positions=[line],
        )
        assert len(result.positions) == 1


class TestStockRecord:
    def test_instantiation(self) -> None:
        record = StockRecord(
            article_number="1001",
            article_name="M6 Screw",
            lift_number=1,
            shelf_number=3,
            compartment_number=2,
            compartment_depth_number=1,
            container_size=1,
            fifo=0,
            inventory_at_storage_location=50.0,
            minimum_inventory=10.0,
        )
        assert record.article_number == "1001"
        assert record.inventory_at_storage_location == 50.0

    def test_batch_number_default_none(self) -> None:
        record = StockRecord(
            article_number="1001",
            article_name="M6 Screw",
            lift_number=1,
            shelf_number=3,
            compartment_number=2,
            compartment_depth_number=1,
            container_size=1,
            fifo=0,
            inventory_at_storage_location=50.0,
            minimum_inventory=10.0,
        )
        assert record.batch_number is None

    def test_batch_number_explicit(self) -> None:
        record = StockRecord(
            article_number="1001",
            article_name="M6 Screw",
            lift_number=1,
            shelf_number=3,
            compartment_number=2,
            compartment_depth_number=1,
            container_size=1,
            fifo=0,
            inventory_at_storage_location=50.0,
            minimum_inventory=10.0,
            batch_number="LOT-C",
        )
        assert record.batch_number == "LOT-C"

"""hanel_warehouse_gateway — Python gateway for the Hanel automatic warehouse.

Exposes only the public interface: main class, public dataclasses,
and exception hierarchy.

Typical usage:
    from hanel_warehouse_gateway import HanelWarehouseGateway, GatewayConfig

    config = GatewayConfig.from_env()
    gateway = HanelWarehouseGateway(config)
"""

from __future__ import annotations

import logging

from .config import GatewayConfig
from .exceptions import (
    HanelGatewayApplicationError,
    HanelGatewayError,
    HanelGatewayHttpError,
    HanelGatewayNetworkError,
    HanelGatewaySoapFaultError,
    HanelGatewayValidationError,
)
from .gateway import HanelWarehouseGateway
from .models import (
    MovementLine,
    MovementLineResult,
    MovementResult,
    StockRecord,
)

logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    "HanelWarehouseGateway",
    "GatewayConfig",
    "MovementLine",
    "MovementLineResult",
    "MovementResult",
    "StockRecord",
    "HanelGatewayError",
    "HanelGatewayNetworkError",
    "HanelGatewayHttpError",
    "HanelGatewaySoapFaultError",
    "HanelGatewayApplicationError",
    "HanelGatewayValidationError",
]

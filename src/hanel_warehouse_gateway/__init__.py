"""hanel_warehouse_gateway — Gateway Python per il magazzino automatico Hanel.

Espone esclusivamente l'interfaccia pubblica: classe principale, dataclass
pubblici e gerarchia di eccezioni.

Uso tipico:
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

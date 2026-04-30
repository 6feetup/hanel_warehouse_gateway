# Hanel Warehouse Gateway

Python module for communicating with the **Hanel automatic warehouse** via SOAP. Exposes a typed Python interface and completely hides SOAP, HTTP, and XML details from the caller.

## Requirements

- Python 3.10+
- Network access to the Hanel t-Server endpoint
- `requests` and `python-dotenv` (installed automatically)

## Installation

```bash
pip install hanel-warehouse-gateway
```

## Configuration

Create a `.env` file in your project root (never commit it):

```dotenv
HANEL_ENDPOINT_URL=http://192.168.1.100:8080/HanelService
HANEL_TEST_MODE=false
HANEL_TEST_PREFIX=TEST_
```

Then load the configuration and instantiate the gateway:

```python
from hanel_warehouse_gateway import HanelWarehouseGateway, GatewayConfig

config = GatewayConfig.from_env()
gateway = HanelWarehouseGateway(config)
```

## Quick start

```python
from hanel_warehouse_gateway import (
    HanelWarehouseGateway,
    GatewayConfig,
    MovementLine,
    HanelGatewayError,
)

config = GatewayConfig.from_env()
gateway = HanelWarehouseGateway(config)

# Register an article
gateway.register_article("ART-001", "M6 stainless bolt")

# Send a pick order
gateway.send_movement_order(
    order_number="ORD-001",
    positions=[MovementLine(article_number="ART-001", operation="+", nominal_quantity=5.0)],
)

# Retrieve completed orders
for result in gateway.get_completed_movements():
    for line in result.positions:
        if line.actual_quantity < line.nominal_quantity:
            print(f"Insufficient stock for {line.article_number}")
```

## Available operations

| Method | Description |
|--------|-------------|
| [`register_article()`](api/gateway.md) | Register or update an article in the warehouse catalogue |
| [`send_movement_order()`](api/gateway.md) | Send a pick (`+`) or load (`-`) movement order |
| [`get_completed_movements()`](api/gateway.md) | Retrieve completed orders |
| [`get_all_orders()`](api/gateway.md) | Retrieve all orders in the queue |
| [`get_inventory()`](api/gateway.md) | Retrieve current stock levels for all articles |
| [`cancel_order()`](api/gateway.md) | Cancel a queued order (status 0 only) |

## Error handling

All errors raise subclasses of [`HanelGatewayError`](api/exceptions.md):

```python
from hanel_warehouse_gateway import (
    HanelGatewayError,
    HanelGatewayNetworkError,
    HanelGatewayApplicationError,
)

try:
    gateway.send_movement_order("ORD-001", positions)
except HanelGatewayNetworkError as exc:
    print(f"Network unreachable after retries: {exc}")
except HanelGatewayApplicationError as exc:
    print(f"Warehouse rejected the order (returnValue={exc.return_value}): {exc}")
except HanelGatewayError as exc:
    print(f"Unexpected gateway error: {exc}")
```

See the [Exceptions reference](api/exceptions.md) for the full hierarchy.

## Thread safety

The module is **not thread-safe**. Instantiate one `HanelWarehouseGateway` per thread if concurrency is needed.

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

The gateway is configured with a `GatewayConfig` object. `endpoint_url` is the
only required field; every other parameter has a sensible default (see the
[Configuration reference](api/config.md) for the full list). There are three
ways to build it.

### 1. Direct instantiation (Python object)

The most common option when integrating the module into an existing
application — pass values straight from your own configuration system:

```python
from hanel_warehouse_gateway import HanelWarehouseGateway, GatewayConfig

config = GatewayConfig(
    endpoint_url="http://192.168.1.100:8080/HanelService",
    test_mode=True,
)
gateway = HanelWarehouseGateway(config)
```

### 2. From `.env` / environment variables

Useful to keep volatile parameters and secrets out of source code. Create a
`.env` file in your project root (never commit it):

```dotenv
HANEL_ENDPOINT_URL=http://192.168.1.100:8080/HanelService
HANEL_TEST_MODE=false
HANEL_TEST_PREFIX=TEST_
```

Then load it:

```python
config = GatewayConfig.from_env()
gateway = HanelWarehouseGateway(config)
```

### 3. From environment with overrides

Reads `.env` / environment variables, then applies the given overrides on top
(handy in tests or for per-environment tweaks):

```python
config = GatewayConfig.from_env({
    "endpoint_url": "http://localhost:8080/HanelService",
    "test_mode": True,
    "timeout_seconds": 5,
})
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
gateway.register_article("1001", "M6 stainless bolt")

# Send a load order
gateway.send_movement_order(
    order_number="ORD-001",
    positions=[MovementLine(article_number="1001", operation="+", nominal_quantity=5)],
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
| [`send_movement_order()`](api/gateway.md) | Send a load (`+`) or pick (`-`) movement order |
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

# hanel_warehouse_gateway

Python module for communicating with the Hanel automatic warehouse via SOAP. Exposes a fully typed Python interface and hides all SOAP details from the caller.

## Requirements

- Python ≥ 3.10
- Dependencies: `requests`, `python-dotenv`

## Installation

```bash
# Editable install with dev tools (recommended for development)
pip install -e ".[dev]"

# Production only
pip install -e .
```

## Configuration

Copy `.env.example` to `.env` and fill in the values:

```dotenv
HANEL_ENDPOINT_URL=http://192.168.1.100:8080/HanelService
HANEL_TEST_MODE=false
HANEL_TEST_PREFIX=TEST_
```

| Variable | Description |
|---|---|
| `HANEL_ENDPOINT_URL` | URL of the Hanel t-Server SOAP endpoint |
| `HANEL_TEST_MODE` | Set to `true` to prefix order numbers, making them identifiable by warehouse operators |
| `HANEL_TEST_PREFIX` | Prefix applied to order numbers when `HANEL_TEST_MODE=true` (default: `TEST_`) |

Load the configuration in code with `GatewayConfig.from_env()`:

```python
from hanel_warehouse_gateway import HanelWarehouseGateway, GatewayConfig

# Reads from .env or environment variables
config = GatewayConfig.from_env()

# Optional overrides (useful in tests)
config = GatewayConfig.from_env({"endpoint_url": "http://localhost:8080/HanelService", "test_mode": True})
```

## Quick start

```python
from hanel_warehouse_gateway import (
    HanelWarehouseGateway,
    GatewayConfig,
    MovementLine,
)

config = GatewayConfig.from_env()
gateway = HanelWarehouseGateway(config)

# Register an article
gateway.register_article("ART-001", "Widget A")

# Send a movement order (operation "+" = pick, "-" = load)
gateway.send_movement_order("ORD-001", [
    MovementLine(article_number="ART-001", operation="+", nominal_quantity=5.0),
])

# Retrieve completed orders
results = gateway.get_completed_movements()
for r in results:
    print(r.job_number, r.job_status)
    for pos in r.positions:
        print(f"  {pos.article_number}: {pos.actual_quantity}/{pos.nominal_quantity}")

# Get stock levels
stock = gateway.get_inventory()
for record in stock:
    print(record.article_number, record.inventory_at_storage_location)
```

## Available operations

| Method | Description |
|---|---|
| `register_article(article_number, article_name)` | Register or update an article in the warehouse |
| `send_movement_order(order_number, positions)` | Send a pick or load order |
| `get_completed_movements()` | Retrieve orders with status = completed |
| `get_all_orders()` | Retrieve all orders currently in the warehouse queue |
| `get_inventory()` | Get stock levels for all articles across all physical locations |
| `cancel_order(order_number)` | Cancel a queued order (only works if the order has not started) |

## Error handling

All exceptions inherit from `HanelGatewayError`:

| Exception | When raised |
|---|---|
| `HanelGatewayNetworkError` | Network failure after all retry attempts are exhausted |
| `HanelGatewayHttpError` | Non-2xx HTTP response from the server |
| `HanelGatewaySoapFaultError` | SOAP fault element present in the response |
| `HanelGatewayApplicationError` | `returnValue != 0` in the application response |
| `HanelGatewayValidationError` | Invalid input detected before sending (no HTTP call is made) |

```python
from hanel_warehouse_gateway import (
    HanelWarehouseGateway,
    GatewayConfig,
    HanelGatewayNetworkError,
    HanelGatewayApplicationError,
    HanelGatewayValidationError,
)

gateway = HanelWarehouseGateway(GatewayConfig.from_env())

try:
    gateway.register_article("ART-001", "Widget A")
except HanelGatewayValidationError as e:
    print(f"Invalid input for field '{e.field}': {e.value}")
except HanelGatewayNetworkError as e:
    print(f"Network error on {e.operation}: {e}")
except HanelGatewayApplicationError as e:
    print(f"t-Server returned error code {e.return_value}")
```

## Running tests

```bash
# Run all tests
pytest tests/ --tb=short -q

# With coverage report
pytest tests/ --cov=src/hanel_warehouse_gateway --cov-report=term-missing

# Type checking
mypy src/hanel_warehouse_gateway/

# Lint
ruff check src/ tests/
```

## Mock server

The `mock_server/` directory contains a Flask implementation of the Hanel t-Server SOAP interface, intended for local development and integration testing without access to the physical warehouse. It supports all five SOAP operations (`sendAPDReqV01`, `sendJobsReqV01`, `readAllJobsReqV01`, `readAllAMDReqV01`, `deleteJobReqV01`), simulates automatic order completion after a configurable delay, and exposes additional HTTP endpoints (`/admin/state`, `/admin/reset`, `/admin/complete-all`) to inspect and control state during testing.

Start it with:

```bash
docker compose up --build
```

The server listens at `http://localhost:8080/HanelService`.

See [`mock_server/README.md`](mock_server/README.md) for full documentation, including data formats, environment variables, and example curl requests for each operation.

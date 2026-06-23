# Hanel Warehouse Gateway

Python module for communicating with the Hanel automatic warehouse via SOAP. Exposes a fully typed Python interface and hides all SOAP details from the caller.

## Requirements

- Python ≥ 3.10
- [`uv`](https://docs.astral.sh/uv/) (install with `brew install uv` or `pip install uv`)
- Dependencies: `requests`, `python-dotenv`

## Installation

```bash
# Install all dependencies including dev tools (recommended for development)
uv sync

# Production only (no dev dependencies)
uv sync --no-dev
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

# Send a movement order (operation "+" = load, "-" = pick)
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

## Release process

Releases are automated via [release-please](https://github.com/googleapis/release-please) and triggered by merging commits into `main`.

### Commit convention

All commits must follow the [Conventional Commits](https://www.conventionalcommits.org/) format. The commit type determines the version bump:

| Prefix | Version bump | When to use |
|---|---|---|
| `fix:` | patch (0.1.0 → 0.1.1) | Bug fix |
| `feat:` | minor (0.1.0 → 0.2.0) | New operation or feature |
| `feat!:` or footer `BREAKING CHANGE:` | major (0.1.0 → 1.0.0) | Incompatible public API change |
| `chore:`, `docs:`, `test:`, `refactor:`, `ci:` | none | Everything else |

The `commitlint` CI check enforces this format on every PR.

### How a release works

1. Merge one or more conventional commits into `main`.
2. The **Release Please** workflow opens (or updates) a "Release PR" automatically, with the computed version and a generated `CHANGELOG.md`.
3. Review and optionally edit the changelog text in the PR.
4. Merge the Release PR.
5. Release Please creates the git tag and the GitHub Release; a second CI job builds the wheel and sdist and attaches them as release assets.

### One-time repository setup

In **Settings → Actions → General**, enable _"Allow GitHub Actions to create and approve pull requests"_ — required for Release Please to open its PR.

## Running tests

```bash
# Unit tests (no external dependencies)
uv run pytest tests/ --ignore=tests/test_mock_server.py --tb=short -q

# Unit tests with coverage report
uv run pytest tests/ --ignore=tests/test_mock_server.py --cov=src/hanel_warehouse_gateway --cov-report=term-missing

# Integration tests against the mock server (requires: docker compose up --build)
uv run pytest tests/test_mock_server.py --tb=short -q

# Type checking
uv run mypy src/hanel_warehouse_gateway/

# Lint
uv run ruff check src/ tests/
```

## Mock server

The `mock_server/` directory contains a Flask implementation of the Hanel t-Server SOAP interface, intended for local development and integration testing without access to the physical warehouse. It supports all five SOAP operations (`sendAPDReqV01`, `sendJobsReqV01`, `readAllJobsReqV01`, `readAllAMDReqV01`, `deleteJobReqV01`), simulates automatic order completion after a configurable delay, and exposes additional HTTP endpoints (`/admin/state`, `/admin/reset`, `/admin/complete-all`) to inspect and control state during testing.

Start it with:

```bash
docker compose up --build
```

The server listens at `http://localhost:8080/HanelService`.

See [`mock_server/README.md`](mock_server/README.md) for full documentation, including data formats, environment variables, and example curl requests for each operation.

## License

This project is licensed under the **GNU Lesser General Public License v3.0 or later
(LGPL-3.0-or-later)**. See the [`LICENSE`](LICENSE) file for the full text; the LGPL
is supplemented by the GNU GPL v3 it incorporates, provided in [`LICENSE.GPL`](LICENSE.GPL).

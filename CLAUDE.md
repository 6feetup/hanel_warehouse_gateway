# CLAUDE.md — hanel_warehouse_gateway

Python module for communicating with the Hanel automatic warehouse via SOAP. Exposes a typed Python interface and completely hides SOAP details from the caller.

## Directory structure

```
src/hanel_warehouse_gateway/
├── __init__.py      ← exposes: HanelWarehouseGateway, public dataclasses, exceptions
├── gateway.py       ← Layer 3: public interface, single point of contact
├── operations.py    ← Layer 2: SOAP operation mapping, serialization/deserialization
├── transport.py     ← Layer 1: HTTP POST, retry, timeout, payload logging
├── models.py        ← dataclasses: MovementLine, MovementLineResult, MovementResult, StockRecord
├── exceptions.py    ← HanelGatewayError hierarchy
├── config.py        ← GatewayConfig dataclass + __post_init__ validation
└── _xml.py          ← PRIVATE: f-string envelope templates, ElementTree parsing
tests/
├── fixtures/        ← XML response files from t-Server (source of truth for parsers)
├── test_config.py
├── test_exceptions.py
├── test_models.py
├── test_xml.py
├── test_transport.py
└── test_operations.py
docs/
├── index.md         ← quick start for integrators (MkDocs home)
├── requirements/    ← technical specifications (read before implementing)
├── scripts.md       ← CLI tool and e2e testing guide
├── api/             ← API reference pages (rendered via mkdocstrings)
├── adr/             ← Architecture Decision Records (001–016)
└── contributing/    ← Development workflow, Claude agents, slash commands
```

## Development commands

```bash
# Install all dependencies including dev tools
uv sync

# Unit tests (no external dependencies)
uv run pytest tests/ --ignore=tests/test_mock_server.py --tb=short -q

# Unit tests with coverage
uv run pytest tests/ --ignore=tests/test_mock_server.py --cov=src/hanel_warehouse_gateway --cov-report=term-missing

# Integration tests against the mock server (requires: docker compose up --build)
uv run pytest tests/test_mock_server.py --tb=short -q

# Type checking
uv run mypy src/hanel_warehouse_gateway/

# Lint
uv run ruff check src/ tests/

# Serve documentation locally (http://127.0.0.1:8000)
uv run mkdocs serve

# Build static documentation (output in site/)
uv run mkdocs build
```

## Configuration (main parameters)

**Volatile parameters and secrets** (`endpoint_url`, `test_mode`, `test_prefix`) live in the `.env` file (not committed). Use `GatewayConfig.from_env()` to load them:

```python
# Standard usage — reads from .env or environment variables
client = HanelWarehouseGateway(GatewayConfig.from_env())

# With explicit overrides (e.g. in tests)
client = HanelWarehouseGateway(GatewayConfig.from_env({
    "endpoint_url": "http://mock/",
    "test_mode": True,
}))
```

`.env` file (do not commit — see `.env.example` for the template):

```dotenv
HANEL_ENDPOINT_URL=http://192.168.1.100:8080/HanelService
HANEL_TEST_MODE=false
HANEL_TEST_PREFIX=TEST_
```

Static parameters with defaults (can be passed as overrides):

| Parameter | Default | Notes |
|---|---|---|
| `timeout_seconds` | 30 | |
| `retry_attempts` | 3 | |
| `retry_delay_seconds` | 2.0 | |
| `log_level` | `INFO` | |
| `log_soap_payloads` | `False` | |
| `validation_truncate` | `False` | `True` → truncates to 40 chars instead of raise |
| `lot_management_enabled` | `False` | `True` → uses V02/V03/V04 SOAP ops with batch_number support |

## Critical constraints

- **NO production external dependencies** beyond `requests` and `python-dotenv`. zeep, lxml, pydantic, structlog are explicitly excluded. Adding a dependency requires an ADR.
- **NO changes to the public interface** (`HanelWarehouseGateway`, dataclasses in `models.py`) without an ADR and version bump.
- **NO `endpoint_url`, `test_mode`, credentials in source code or committed files**. Always from environment variables / `.env`.
- **NO logger handlers**: the module is a library and uses only `NullHandler`. The caller configures their own handlers.
- **XML templates live in `_xml.py`**: no XML envelopes elsewhere.
- **`__init__.py` exposes only**: `HanelWarehouseGateway`, `MovementLine`, `MovementLineResult`, `MovementResult`, `StockRecord`, and the `HanelGateway*` exceptions.
- **Tests do not make real HTTP calls**: every `requests` call in tests is intercepted by `responses`.
- **ADRs are never deleted**: if a decision changes, update the status to `Superseded` with a reference to the new ADR.
- **Documentation language**: all code comments, docstrings, ADRs, fixture descriptions, and technical notes must be written in **English**. Italian is reserved for user-facing communications only.

## Key ADRs

| ADR | Decision |
|-----|----------|
| [001](docs/adr/001-packaging-structure.md) | `pyproject.toml` + `src/` layout |
| [002](docs/adr/002-soap-transport.md) | `requests` + manual XML (no zeep) |
| [003](docs/adr/003-configuration.md) | `GatewayConfig` dataclass from dict |
| [004](docs/adr/004-xml-construction-parsing.md) | f-string templates + ElementTree |
| [005](docs/adr/005-error-handling-retry.md) | Exception hierarchy + retry on network errors only |
| [006](docs/adr/006-logging.md) | `logging` stdlib, NullHandler, no default handlers |
| [007](docs/adr/007-testing-strategy.md) | `pytest` + `unittest.mock` + `responses` |
| [008](docs/adr/008-input-validation.md) | Default raise on fields > 40 chars; truncate opt-in |
| [013](docs/adr/013-uv-package-manager.md) | `uv` as official package manager |
| [014](docs/adr/014-documentation-toolchain.md) | MkDocs + mkdocstrings for API docs |
| [015](docs/adr/015-lot-management.md) | Lot management via feature flag + V02/V03/V04 ops |
| [016](docs/adr/016-lot-tag-names-provisional.md) | Provisional XML tag names for lot management |
| [Contributing docs](docs/contributing/) | Development workflow, Claude agents, slash commands |

## Available slash commands

- `/new-operation` — full scaffold for a new SOAP operation
- `/check-adr` — verify ADR consistency vs current code
- `/soap-fixture` — generate XML fixture for an operation
- `/run-tests` — run pytest with coverage and show summary

## Operational notes

- The t-Server has no separate test environment. Use `test_mode=True` for orders identifiable by warehouse operators.
- The module is **not thread-safe**. Instantiate one client per thread if parallelism is needed.
- `get_inventory()` is the only way to detect manual movements performed directly at the warehouse console.
- `actual_quantity < nominal_quantity` in `MovementLineResult` indicates insufficient stock: handling is the caller's responsibility.

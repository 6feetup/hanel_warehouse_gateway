# ADR-001 — Python module packaging and structure

**Status:** Accepted

## Context

The project is a standalone Python module that exposes an interface for communicating with the Hanel automatic warehouse via SOAP. Before writing code, the packaging structure and source file layout must be established.

## Options evaluated

| Option | Pros | Cons |
|---|---|---|
| `setup.py` legacy | Familiar, universally supported | Deprecated, not PEP 621 standard |
| `setup.cfg` | Separation of config from code | Semi-legacy, superseded by pyproject.toml |
| `pyproject.toml` (PEP 517/621) | Modern standard, supported by pip/build/hatch/uv | None relevant |

## Decision

We adopt **`pyproject.toml`** with a `src/` layout (PEP 517/621).

The `src/` layout prevents the package from being importable directly from the project root during development, enforcing installation via `uv sync` and reducing false positives in tests.

## Directory structure

```
hanel_warehouse_gateway/           ← repository root
├── src/
│   └── hanel_warehouse_gateway/
│       ├── __init__.py            ← exposes HanelWarehouseGateway, GatewayConfig, public dataclasses, exceptions
│       ├── gateway.py             ← Layer 3: HanelWarehouseGateway (public interface)
│       ├── operations.py          ← Layer 2: SOAP operation mapping
│       ├── transport.py           ← Layer 1: HTTP/SOAP client, retry, timeout
│       ├── models.py              ← dataclasses: MovementLine, MovementResult, StockRecord…
│       ├── exceptions.py          ← HanelGatewayError hierarchy
│       ├── config.py              ← GatewayConfig dataclass + validation
│       └── _xml.py                ← private helper: envelope construction + response parsing
├── tests/
│   ├── fixtures/                  ← XML response files for tests
│   ├── test_config.py
│   ├── test_exceptions.py
│   ├── test_models.py
│   ├── test_xml.py
│   ├── test_transport.py
│   └── test_operations.py
├── docs/
│   ├── requirements/
│   └── adr/
├── CLAUDE.md
├── pyproject.toml
└── .claude/
    ├── agents/
    └── commands/
```

## File responsibilities

| File | Responsibility |
|---|---|
| `gateway.py` | Single point of contact for the caller; delegates to `operations.py` |
| `operations.py` | Builds the specific SOAP call, deserialises the response |
| `transport.py` | Executes HTTP POST, handles retry and timeout, logs payloads |
| `models.py` | Defines all public and internal dataclasses |
| `exceptions.py` | Defines the exception hierarchy |
| `config.py` | Validates and normalises incoming configuration |
| `_xml.py` | f-string envelope templates + ElementTree parsing functions |

## Consequences

- Editable mode installation required for development: `uv sync`
- The package is importable only after installation, not directly from `src/`
- `__init__.py` exposes exclusively `HanelWarehouseGateway`, `GatewayConfig`, the public dataclasses (`MovementLine`, `MovementLineResult`, `MovementResult`, `StockRecord`), and the exception hierarchy — nothing from `_xml.py` or the internal layers. `GatewayConfig` is part of the public surface because callers must construct it (typically via `GatewayConfig.from_env()`) to instantiate the gateway.

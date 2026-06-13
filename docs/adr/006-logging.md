# ADR-006 — Logging strategy

**Status:** Accepted

## Context

The module must produce structured logs at all levels (transport, operations, public interface) as per §6 of the requirements. It is a Python library: logging choices must follow best practices for libraries (do not force configuration on the calling application).

## Options evaluated

| Option | Pros | Cons |
|---|---|---|
| `logging` stdlib | Zero dependencies, configurable by caller, Python standard | JSON format requires a custom formatter |
| `structlog` | Native JSON logs, nested context, very powerful | External dependency, overhead for this use case |
| `loguru` | Simple API, coloured output | External dependency, different behaviour from stdlib |

## Decision

We adopt **`logging` stdlib**. The module uses a single logger named `hanel_warehouse_gateway` and adds no default handlers.

## Implementation rules

### Logger

```python
import logging
logger = logging.getLogger("hanel_warehouse_gateway")
```

Every sub-module uses the same logger (not per-module sub-loggers) for simplicity.

### Level

The logger level is applied once when the public `HanelWarehouseGateway` is
instantiated, based on `config.log_level`:

```python
logger.setLevel(getattr(logging, config.log_level, logging.INFO))
```

`config.log_level` is also readable from the environment via `HANEL_LOG_LEVEL`
(and `HANEL_LOG_SOAP_PAYLOADS` for payload logging).

### No default handlers

Python libraries must not add handlers. The caller is responsible for configuring handlers. To avoid the "No handlers could be found" message, a `NullHandler` is added:

```python
logging.getLogger("hanel_warehouse_gateway").addHandler(logging.NullHandler())
```

This goes in `src/hanel_warehouse_gateway/__init__.py`.

### Event format

Logs always include: `operation`, `duration_ms` (where applicable), `message`. No custom formatter is used; the format is delegated to the caller.

### SOAP payloads

XML payloads (outgoing envelope and incoming response) are logged **only if**:
- `config.log_soap_payloads = True`
- The effective logger level is `DEBUG`

```python
if config.log_soap_payloads:
    logger.debug("SOAP request [%s]: %s", operation, envelope)
```

## Required events

| Event | Level | Where |
|---|---|---|
| SOAP call started (operation + non-sensitive params) | `INFO` | `operations.py` |
| Successful outcome (operation + duration ms) | `INFO` | `operations.py` |
| Retry in progress (attempt N of M, reason) | `WARNING` | `transport.py` |
| Final failure (type, operation, detail) | `ERROR` | `transport.py` / `operations.py` |
| Outgoing XML envelope | `DEBUG` (only if `log_soap_payloads`) | `transport.py` |
| Incoming XML envelope | `DEBUG` (only if `log_soap_payloads`) | `transport.py` |

## Consequences

- The caller configures handlers, formatters, and log destinations without modifying the module
- SOAP payloads are disabled by default (they contain potentially sensitive warehouse data)
- Adding `structlog` in the future does not break the interface: just replace the internal logger

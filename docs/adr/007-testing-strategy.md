# ADR-007 — Testing strategy

**Status:** Accepted

## Context

The module communicates with an external system (Hanel t-Server) that is not available in the development environment and has no separate test environment. Tests must be runnable without connectivity to the warehouse.

## Options evaluated

| Framework | Pros | Cons |
|---|---|---|
| Pure `unittest` | Stdlib, zero dependencies | Verbose, more complex fixtures |
| `pytest` | Powerful fixtures, plugin ecosystem, readable output | Dev dependency |
| `pytest` + `pytest-mock` | Cleaner mock API | Extra dependency, `unittest.mock` is sufficient |
| `responses` (HTTP mock) | Intercepts `requests` without manual patching | Extra dev dependency but necessary |

## Decision

We adopt **`pytest`** + **`unittest.mock`** + **`responses`**.

`responses` is the correct choice for testing `transport.py`: it intercepts HTTP calls at the `requests` level without requiring manual patching of `requests.post`.

## Test levels

### 1. Unit tests (no HTTP)

Test isolated components:
- `test_config.py` — `GatewayConfig` validation, missing keys, wrong types
- `test_exceptions.py` — exception construction, required attributes
- `test_models.py` — dataclass construction, default values
- `test_xml.py` — `build_*()` produces expected XML; `parse_*()` extracts correct fields from XML fixtures

### 2. Integration tests (mocked HTTP)

Test the full flow from public call to deserialization, with HTTP intercepted by `responses`:
- `test_transport.py` — retry on network errors, HTTP error classification
- `test_operations.py` — each SOAP operation: input → correct envelope → response parsing → expected output

### 3. End-to-end

Not included. `test_mode=True` with the `TEST_` prefix is the mechanism for testing against the real system without affecting stock.

## XML fixtures

Fixtures reside in `tests/fixtures/` as `.xml` files:

```
tests/fixtures/
├── response_send_apd_ok.xml
├── response_send_apd_error.xml
├── response_send_jobs_ok.xml
├── response_read_jobs_mode0.xml
├── response_read_jobs_mode1.xml
├── response_read_amd.xml
├── response_delete_job_ok.xml
└── response_soap_fault.xml
```

Fixtures represent real or plausible t-Server responses and are the source of truth for the parsers.

## pytest configuration

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--tb=short -q"
```

Coverage configured via `pytest-cov`:

```toml
[tool.coverage.run]
source = ["src/hanel_warehouse_gateway"]
branch = true

[tool.coverage.report]
fail_under = 80
```

## Consequences

- Tests are runnable offline without access to the t-Server
- XML fixtures implicitly document the structure of expected responses
- Adding a new SOAP operation requires: XML fixture + tests in `test_xml.py` + tests in `test_operations.py`

# Configuration

`GatewayConfig` holds all parameters needed to connect to the Hanel t-Server.
It is a plain dataclass: you can build it directly in Python, or load it from a
`.env` file / environment variables with `GatewayConfig.from_env()`.

## Direct instantiation

The most common option when integrating the module into an existing
application. `endpoint_url` is the only required field; everything else has a
default (see [All fields](#all-fields)). Environment variables are entirely
optional — they only matter if you use `from_env()`.

```python
from hanel_warehouse_gateway import GatewayConfig, HanelWarehouseGateway

config = GatewayConfig(
    endpoint_url="http://192.168.1.100:8080/HanelService",
    test_mode=True,
    timeout_seconds=20,
)
gateway = HanelWarehouseGateway(config)
```

## All fields

| Field | Default | Notes |
|-------|---------|-------|
| `endpoint_url` | — (**required**) | Full URL of the Hanel SOAP endpoint. Must start with `http://` or `https://`. |
| `timeout_seconds` | `30` | HTTP request timeout. Must be `> 0`. |
| `retry_attempts` | `3` | Number of attempts on network errors. Must be `>= 1`. |
| `retry_delay_seconds` | `2.0` | Delay between retries. Must be `>= 0`. |
| `test_mode` | `False` | If `True`, prepends `test_prefix` to order numbers so operators can identify test orders. |
| `test_prefix` | `"TEST_"` | Prefix applied to order numbers when `test_mode=True`. |
| `log_level` | `"INFO"` | One of `DEBUG`, `INFO`, `WARNING`, `ERROR`. |
| `log_soap_payloads` | `False` | If `True`, logs raw SOAP request/response payloads (verbose; use for debugging). |
| `validation_truncate` | `False` | If `True`, truncates fields longer than 40 chars instead of raising. |
| `lot_management_enabled` | `False` | If `True`, uses the V02/V03/V04 SOAP operations with `batch_number` support. |
| `namespace_main` | `"http://main.jws.com.hanel.de"` | Fixed SOAP namespace. Do not change unless the t-Server requires it. |
| `namespace_xsd` | `"http://main.jws.com.hanel.de/xsd"` | Fixed SOAP namespace. Do not change unless the t-Server requires it. |

Invalid values raise `ValueError` at construction time (e.g. an `endpoint_url`
without an `http(s)://` scheme, a non-positive `timeout_seconds`, or an
unknown `log_level`).

## Environment variables

Read by `from_env()`. Each maps to a field above; anything not set falls back
to the field default.

| Variable | Required | Maps to | Description |
|----------|----------|---------|-------------|
| `HANEL_ENDPOINT_URL` | **Yes** | `endpoint_url` | Full URL of the Hanel SOAP endpoint |
| `HANEL_TEST_MODE` | No | `test_mode` | `true` / `false` (default: `false`) |
| `HANEL_TEST_PREFIX` | No | `test_prefix` | Prefix for order numbers in test mode (default: `TEST_`) |
| `HANEL_LOT_MANAGEMENT_ENABLED` | No | `lot_management_enabled` | `true` / `false` (default: `false`) |
| `HANEL_LOG_LEVEL` | No | `log_level` | `DEBUG` / `INFO` / `WARNING` / `ERROR` (default: `INFO`) |
| `HANEL_LOG_SOAP_PAYLOADS` | No | `log_soap_payloads` | `true` / `false` (default: `false`) |

## Example `.env`

```dotenv
HANEL_ENDPOINT_URL=http://192.168.1.100:8080/HanelService
HANEL_TEST_MODE=false
HANEL_TEST_PREFIX=TEST_
```

## Usage

```python
from hanel_warehouse_gateway import GatewayConfig, HanelWarehouseGateway

# Load from .env / environment
config = GatewayConfig.from_env()

# With overrides (useful in tests)
config = GatewayConfig.from_env({
    "endpoint_url": "http://localhost:8080/HanelService",
    "test_mode": True,
    "timeout_seconds": 5,
})

gateway = HanelWarehouseGateway(config)
```

## Reference

::: hanel_warehouse_gateway.GatewayConfig

# Configuration

`GatewayConfig` holds all parameters needed to connect to the Hanel t-Server. Use `GatewayConfig.from_env()` to load from a `.env` file or environment variables.

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `HANEL_ENDPOINT_URL` | **Yes** | Full URL of the Hanel SOAP endpoint |
| `HANEL_TEST_MODE` | No | `true` / `false` (default: `false`) |
| `HANEL_TEST_PREFIX` | No | Prefix for order numbers in test mode (default: `TEST_`) |

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

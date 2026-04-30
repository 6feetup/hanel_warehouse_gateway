# Exceptions

All exceptions raised by the module are subclasses of `HanelGatewayError`.

## Hierarchy

```
HanelGatewayError
├── HanelGatewayNetworkError      — network failure after all retries
├── HanelGatewayHttpError         — non-2xx HTTP response
├── HanelGatewaySoapFaultError    — SOAP fault in the response envelope
├── HanelGatewayApplicationError  — returnValue != 0 in the application response
└── HanelGatewayValidationError   — invalid input, no HTTP call made
```

## Catching errors

```python
from hanel_warehouse_gateway import (
    HanelGatewayError,
    HanelGatewayNetworkError,
    HanelGatewayHttpError,
    HanelGatewaySoapFaultError,
    HanelGatewayApplicationError,
    HanelGatewayValidationError,
)

try:
    result = gateway.send_movement_order("ORD-001", positions)
except HanelGatewayValidationError as exc:
    # Input rejected before any HTTP call — check exc.field and exc.value
    print(f"Invalid field '{exc.field}': {exc.value!r}")
except HanelGatewayNetworkError:
    # All retry attempts exhausted
    ...
except HanelGatewayApplicationError as exc:
    # Warehouse returned a non-zero returnValue
    print(f"returnValue={exc.return_value}")
except HanelGatewayError as exc:
    # Catch-all for any other gateway error
    print(exc)
```

All exceptions expose: `message`, `operation`, `detail`, `timestamp`.

## Reference

::: hanel_warehouse_gateway.HanelGatewayError

::: hanel_warehouse_gateway.HanelGatewayNetworkError

::: hanel_warehouse_gateway.HanelGatewayHttpError

::: hanel_warehouse_gateway.HanelGatewaySoapFaultError

::: hanel_warehouse_gateway.HanelGatewayApplicationError

::: hanel_warehouse_gateway.HanelGatewayValidationError

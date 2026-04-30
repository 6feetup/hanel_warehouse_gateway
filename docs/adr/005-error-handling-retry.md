# ADR-005 — Error handling and retry strategy

**Status:** Accepted

## Context

The module interacts with an external system (Hanel t-Server) subject to network errors, HTTP errors, SOAP faults, and application-level error codes. Specification §5 defines the exception hierarchy and retry rules. This ADR formalises the implementation choices.

## Decision

### Exception hierarchy

```python
class HanelGatewayError(Exception):
    """Base exception. All module errors inherit from this."""
    def __init__(self, message: str, operation: str, detail: str, timestamp: str): ...

class HanelGatewayNetworkError(HanelGatewayError):
    """Network error after all retry attempts are exhausted."""

class HanelGatewayHttpError(HanelGatewayError):
    """HTTP response with a non-2xx status code. No retry."""
    def __init__(self, …, http_status: int): ...

class HanelGatewaySoapFaultError(HanelGatewayError):
    """SOAP fault present in the response envelope. No retry."""
    def __init__(self, …, fault_string: str, fault_code: str): ...

class HanelGatewayApplicationError(HanelGatewayError):
    """returnValue != 0 in the response. No retry."""
    def __init__(self, …, return_value: int): ...

class HanelGatewayValidationError(HanelGatewayError):
    """Invalid input detected before sending. No HTTP call is made."""
    def __init__(self, …, field: str, value: str): ...
```

All exceptions include: `message`, `operation`, `detail`, `timestamp` (ISO 8601).

### Retry strategy

Retry applies **exclusively** to network errors (`requests.ConnectionError`, `requests.Timeout`). It does not apply to HTTP errors, SOAP faults, or application errors.

Algorithm implemented in `transport.py`:

```python
for attempt in range(1, config.retry_attempts + 1):
    try:
        response = requests.post(…)
        break
    except (requests.ConnectionError, requests.Timeout) as exc:
        if attempt == config.retry_attempts:
            raise HanelGatewayNetworkError(…) from exc
        logger.warning("Retry %d/%d for operation %s: %s", attempt, config.retry_attempts, operation, exc)
        time.sleep(config.retry_delay_seconds)
```

### HTTP error classification

After an HTTP response is received:
- Status 200 → proceeds with XML parsing
- Status 4xx/5xx → immediate `HanelGatewayHttpError`, no retry

### SOAP fault detection

XML parsing checks for the presence of the `<soapenv:Fault>` tag before looking for `returnValue`. If present: `HanelGatewaySoapFaultError`.

### Application codes

`returnValue == 0` → success.
`returnValue != 0` → `HanelGatewayApplicationError` with the raw value and the response message. The module does not interpret or map Hanel error codes (the documentation does not list them; see §5.4 of the requirements).

## Consequences

- The caller can catch `HanelGatewayError` to handle all errors uniformly, or catch subclasses for differentiated handling
- The maximum wait window is `retry_attempts * retry_delay_seconds` seconds
- The raw `returnValue` is always included in the exception to facilitate future diagnosis

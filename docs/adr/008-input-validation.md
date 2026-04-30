# ADR-008 — Input field validation behaviour

**Status:** Accepted

## Context

Specification §7 states that the `articleNumber` and `articleName` fields have a limit of 40 alphanumeric characters. The behaviour on violation is configurable: truncation (with a warning) or an exception. The default and the configuration mechanism need to be formalised.

## Decision

The **default behaviour is `raise HanelGatewayValidationError`**.

Silent truncation is opt-in via `config["validation_truncate"] = True`.

## Rationale

Silent truncation hides a data problem in the calling system. An exception forces the caller to notice it immediately. The conservative default is preferable; the caller can consciously choose truncation.

## Configuration parameter

| Parameter | Type | Default | Description |
|---|---|---|---|
| `validation_truncate` | `bool` | `False` | If `True`, truncates to 40 chars and logs `WARNING` instead of raising an exception |

This parameter is added to `GatewayConfig` (see ADR-003).

## Fields subject to validation

| Field | Limit | Operation |
|---|---|---|
| `article_number` | max 40 chars | `register_article`, `send_movement_order`, `cancel_order` |
| `article_name` | max 40 chars | `register_article` |
| `job_number` | max 40 chars | `send_movement_order`, `cancel_order` |

## Implementation

Validation occurs in `operations.py` before the envelope is built, via a helper function:

```python
def _validate_field_length(value: str, field: str, operation: str, config: GatewayConfig) -> str:
    if len(value) <= 40:
        return value
    if config.validation_truncate:
        logger.warning("Field '%s' truncated to 40 chars in operation '%s'", field, operation)
        return value[:40]
    raise HanelGatewayValidationError(
        message=f"Field '{field}' exceeds the 40-character limit",
        operation=operation,
        detail=f"Length: {len(value)}, value: {value!r}",
        timestamp=datetime.utcnow().isoformat(),
        field=field,
        value=value,
    )
```

## Consequences

- By default, oversized data produces an immediate, traceable exception
- Callers that prefer truncation must declare it explicitly in the configuration
- In truncation mode the `WARNING` log ensures traceability even without an exception

# ADR-008 — Input field validation behaviour

**Status:** Accepted

## Context

Specification §7 states that the `articleNumber` and `articleName` fields have a limit of 40 characters (with `articleNumber` further constrained to digits only). The behaviour on violation is configurable: truncation (with a warning) or an exception. The default and the configuration mechanism need to be formalised.

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

| Field | Length limit | Charset constraint | Operation |
|---|---|---|---|
| `article_number` | max 40 chars | **digits only** (`[0-9]`) | `register_article`, `send_movement_order` |
| `article_name` | max 40 chars | none (spaces/symbols allowed) | `register_article` |
| `job_number` | max 40 chars | none | `send_movement_order`, `cancel_order` |
| `batch_number` | max 40 chars | none | `register_article`, `send_movement_order` (lot mode) |

## Character constraints

The `article_number` is a numeric code. The t-Server rejects values that contain non-digit
characters (letters, hyphens, spaces, symbols) with an opaque application error (`returnValue`).
To surface this earlier and more clearly, the module validates the article code against
`^[0-9]+$` **before** the request is sent.

This check **always raises `HanelGatewayValidationError`** on violation, *independently of*
`validation_truncate`. Rationale: unlike an over-length field, an article code cannot be
auto-corrected by stripping characters without changing the identity of the article — silent
mutation would point a request at a different (or non-existent) article. The empty string is
also rejected (the `+` quantifier requires at least one digit).

The constraint applies to `article_number` only. `article_name`, `job_number`, and
`batch_number` keep length-only validation. In `register_article`, the charset check runs on
the caller-supplied value **before** the `test_prefix` is prepended, because the prefix is
module-controlled and may legitimately contain non-digit characters (e.g. `TEST_`).

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

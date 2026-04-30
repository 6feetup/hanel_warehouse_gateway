# ADR-003 — Configuration management

**Status:** Accepted

## Context

The module must be configurable without code changes. The public interface accepts a `dict` as per §2 of the requirements. Internally, parameters must be validated and normalised robustly.

## Parameter classification

Parameters are divided into three categories with distinct origins:

| Category | Parameters | Origin |
|---|---|---|
| **Volatile / environment** | `endpoint_url`, `test_mode`, `test_prefix` | Environment variable (`.env`) |
| **Secrets** | *(future credentials, e.g. API key, password)* | Environment variable (`.env`) |
| **Static / structural** | all others | Dict passed by the caller or default values |

Volatile parameters and secrets must never be hardcoded in source code or committed files. They are read from environment variables, which in development are loaded from a `.env` file (not committed).

## Options evaluated

| Option | Pros | Cons |
|---|---|---|
| Plain `dict` | Zero overhead | No validation, no type checking, silent errors |
| `pydantic.BaseModel` | Powerful validation, type coercion, clear errors | Unnecessary external dependency |
| `dataclasses` stdlib + `__post_init__` | Explicit validation, zero dependencies, native type hints | Manual type coercion |
| `TypedDict` | Type hints without runtime overhead | No runtime validation |

## Decision

We adopt a **`@dataclass` `GatewayConfig`** (stdlib) with validation in `__post_init__`. The public interface `HanelWarehouseGateway(config: dict)` converts the dict into a `GatewayConfig` at initialisation.

Volatile parameters and secrets are read from environment variables via **`python-dotenv`**, which automatically loads the `.env` file at the project root if present. `python-dotenv` is the only additional external dependency permitted alongside `requests`.

## Parameters

```python
@dataclass
class GatewayConfig:
    endpoint_url: str
    namespace_main: str = "http://main.jws.com.hanel.de"
    namespace_xsd: str = "http://main.jws.com.hanel.de/xsd"
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: float = 2.0
    test_mode: bool = False
    test_prefix: str = "TEST_"
    log_level: str = "INFO"
    log_soap_payloads: bool = False
    validation_truncate: bool = False  # see ADR-008
```

The `validation_truncate` parameter is an addition to the original requirements (see ADR-008).

## Validation behaviour

`__post_init__` verifies:
- `endpoint_url` is non-empty and starts with `http://` or `https://`
- `timeout_seconds` > 0
- `retry_attempts` >= 1
- `retry_delay_seconds` >= 0
- `log_level` is one of `DEBUG`, `INFO`, `WARNING`, `ERROR`

Configuration errors raise `ValueError` with an explicit message (not `HanelGatewayValidationError`, which is reserved for business data validation before sending).

## .env file

In development, volatile parameters and secrets are defined in a `.env` file at the project root:

```dotenv
# .env — DO NOT commit this file
HANEL_ENDPOINT_URL=http://192.168.1.100:8080/HanelService
HANEL_TEST_MODE=false
HANEL_TEST_PREFIX=TEST_
# Future secret example:
# HANEL_API_KEY=...
```

The `.env` file **must not be committed**. The repository includes a committed `.env.example` with placeholder values as a reference:

```dotenv
# .env.example — copy to .env and fill in the real values
HANEL_ENDPOINT_URL=http://<host>:<port>/HanelService
HANEL_TEST_MODE=false
HANEL_TEST_PREFIX=TEST_
```

`.gitignore` must contain the line `.env`.

## Construction from environment variables + dict

`GatewayConfig` provides a factory method `from_env()` that:
1. Loads the `.env` file via `python-dotenv` (if present)
2. Reads environment variables with the `HANEL_` prefix
3. Accepts an optional dict for static parameters (overrides or additional values)
4. Dict values take precedence over environment variables

```python
@classmethod
def from_env(cls, overrides: dict | None = None) -> "GatewayConfig":
    from dotenv import load_dotenv
    load_dotenv()  # no-op if .env does not exist
    env_values = {
        "endpoint_url": os.getenv("HANEL_ENDPOINT_URL"),
        "test_mode": os.getenv("HANEL_TEST_MODE", "false").lower() == "true",
        "test_prefix": os.getenv("HANEL_TEST_PREFIX", "TEST_"),
    }
    merged = {k: v for k, v in env_values.items() if v is not None}
    if overrides:
        merged.update(overrides)
    return cls.from_dict(merged)

@classmethod
def from_dict(cls, d: dict) -> "GatewayConfig":
    known_keys = {f.name for f in fields(cls)}
    filtered = {k: v for k, v in d.items() if k in known_keys}
    return cls(**filtered)
```

Unknown keys are silently ignored with a `WARNING` log, to allow forward compatibility if the caller passes additional parameters.

## Typical usage

```python
# Development: reads from .env
client = HanelWarehouseGateway(GatewayConfig.from_env())

# Production: environment variables injected by the orchestrator (Docker, k8s…)
client = HanelWarehouseGateway(GatewayConfig.from_env())

# Tests: explicit override without .env
client = HanelWarehouseGateway(GatewayConfig.from_env({
    "endpoint_url": "http://mock-server/",
    "test_mode": True,
}))
```

## Consequences

- `endpoint_url`, `test_mode`, `test_prefix` never appear in committed files
- Future secrets follow the same pattern without architectural changes
- `python-dotenv` is the second (and last) permitted production external dependency
- Adding a volatile parameter requires: adding the environment variable to `.env.example`, updating `from_env()`, updating this ADR and `CLAUDE.md`
- Configuration errors surface at initialisation, not at first use
- Internal code always uses the typed `GatewayConfig`, never a raw dict

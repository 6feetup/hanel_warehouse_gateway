# Technical Specification — `hanel_warehouse_gateway`

## Purpose

This document defines the technical requirements for the implementation of the Python module `hanel_warehouse_gateway`, responsible for communication with the SOAP Web Service of the Hanel automated vertical warehouse (t-Server). The module must be completely decoupled from the calling system: it exposes its own interface and contains no external application logic.

---

## 1. Module Architecture

The module is structured in three layers:

**Layer 1 — SOAP Transport**
Handles XML envelope construction, HTTP/HTTPS transmission, and raw response reception. Does not interpret content.

**Layer 2 — Operations**
Maps each business operation to a specific SOAP call. Serializes inputs, deserializes responses, handles return codes.

**Layer 3 — Public Interface**
Exposes typed Python methods that the calling system uses without any knowledge of the underlying SOAP details. Returns structured objects (dataclass or dict), never raw XML.

```
Calling system
      │
      ▼
┌─────────────────────────┐
│     Public interface    │  ← single point of contact
├─────────────────────────┤
│     SOAP operations     │  ← request/response mapping
├─────────────────────────┤
│    HTTP/SOAP transport  │  ← connection, timeout, retry
└─────────────────────────┘
      │
      ▼
  Hanel t-Server
```

---

## 2. Configuration

The module must be configurable without code changes. All parameters are loaded from an external configuration source (e.g. `.ini`, `.env`, or a dict passed to the constructor).

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `endpoint_url` | `str` | Full URL of the SOAP Web Service (e.g. `http://192.168.x.x:8080/...`) |
| `namespace_main` | `str` | Main namespace — fixed value: `http://main.jws.com.hanel.de` |
| `namespace_xsd` | `str` | Type namespace — fixed value: `http://main.jws.com.hanel.de/xsd` |
| `timeout_seconds` | `int` | Timeout for a single HTTP call (default: 30) |
| `retry_attempts` | `int` | Maximum number of attempts on network error (default: 3) |
| `retry_delay_seconds` | `float` | Wait between attempts (default: 2.0) |
| `test_mode` | `bool` | If `True`, automatically prepends `test_prefix` to all `jobNumber` values sent |
| `test_prefix` | `str` | Prefix used in test mode (default: `TEST_`) |
| `log_level` | `str` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `log_soap_payloads` | `bool` | If `True`, logs full XML envelopes (only at `DEBUG` level) |

> *Extended by REQ-LOT-001: adds `lot_management_enabled` (`bool`, default `False`) to enable lot-management operations V02/V03/V04. See §6 of that document.*

### Configuration Example

```python
config = {
    "endpoint_url": "http://192.168.1.100:8080/HanelService",
    "timeout_seconds": 30,
    "retry_attempts": 3,
    "retry_delay_seconds": 2.0,
    "test_mode": False,
    "log_level": "INFO",
    "log_soap_payloads": False,
}

client = HanelWarehouseGateway(config)
```

---

## 3. Available Operations

### 3.1 Article Master Registration — `register_article`

**Flow:** Article master data (Flow 1)
**SOAP operation:** `sendAPDReqV01` — *SEND ARTICLE MASTER*

**Purpose:** registers or updates an article in the warehouse.

**Input:**

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `article_number` | `str` | max 40 chars, digits only (`0-9`) | Unique article code |
| `article_name` | `str` | max 40 chars | Article description |

> *Extended by REQ-LOT-001: adds optional `batch_number: str | None = None` input parameter. See §4.1 of that document.*

**Behaviour:** the article master is always owned by the calling system. The warehouse only receives and stores; it does not create articles autonomously.

**Output:** `bool` — `True` if `returnValue == 0`, `False` otherwise.

**Reference envelope:**
```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:main="http://main.jws.com.hanel.de"
                  xmlns:xsd="http://main.jws.com.hanel.de/xsd">
  <soapenv:Header/>
  <soapenv:Body>
    <main:sendAPDReqV01>
      <main:param>
        <xsd:articlePoolDataRecord>
          <xsd:articleNumber>{article_number}</xsd:articleNumber>
          <xsd:articleName>{article_name}</xsd:articleName>
        </xsd:articlePoolDataRecord>
      </main:param>
    </main:sendAPDReqV01>
  </soapenv:Body>
</soapenv:Envelope>
```

> *This envelope applies only when `lot_management_enabled=False`. When `True`, the operation becomes `sendAPDV03` with `APDTypeV03`. See §7.4 of REQ-LOT-001.*

---

### 3.2 Send Movement Order — `send_movement_order`

**Flow:** Inbound/outbound movement orders (Flow 2)
**SOAP operation:** `sendJobsReqV01` — *SEND PICK/LOAD LIST*

**Purpose:** sends a movement order (pick or load) to the warehouse, containing one or more article lines.

**Input — `MovementOrder` object:**

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `job_number` | `str` | max 40 chars, unique | Order identifier |
| `positions` | `list[MovementLine]` | at least 1 element | Order lines |

**Input — `MovementLine` object:**

| Field | Type | Values | Notes |
|---|---|---|---|
| `article_number` | `str` | max 40 chars | Must match a previously registered article |
| `operation` | `str` | `+` = pick, `-` = load | Movement direction |
| `nominal_quantity` | `int` | > 0, integer | Requested quantity (the warehouse only accepts integer quantities; fractional values are rejected on send) |

> *Extended by REQ-LOT-001: adds optional `batch_number: str | None = None` to `MovementLine`. See §4.2 and §5 of that document.*

**Test mode behaviour:** if `test_mode=True`, the module automatically prepends the configured prefix to the `job_number` (e.g. `ORDER1` → `TEST_ORDER1`). This allows warehouse operators to identify and ignore test orders without affecting real stock levels.

**Output:** `bool` — `True` if `returnValue == 0`.

**Reference envelope:**
```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:main="http://main.jws.com.hanel.de"
                  xmlns:xsd="http://main.jws.com.hanel.de/xsd">
  <soapenv:Header/>
  <soapenv:Body>
    <main:sendJobsReqV01>
      <main:param>
        <xsd:job>
          <xsd:jobNumber>{job_number}</xsd:jobNumber>
          <xsd:JobPosition>
            <xsd:articleNumber>{article_number}</xsd:articleNumber>
            <xsd:operation>{operation}</xsd:operation>
            <xsd:nominalQuantity>{nominal_quantity}</xsd:nominalQuantity>
          </xsd:JobPosition>
          <!-- repeat xsd:JobPosition for each line -->
        </xsd:job>
      </main:param>
    </main:sendJobsReqV01>
  </soapenv:Body>
</soapenv:Envelope>
```

> *This envelope applies only when `lot_management_enabled=False`. When `True`, the operation becomes `sendJobsV02` with `JobPositionTypeV02`. See §7.1 of REQ-LOT-001.*

---

### 3.3 Fetch Completed Movements — `get_completed_movements`

**Flow:** Movement confirmations (Flow 3)
**SOAP operation:** `readAllJobsReqV01` with `mode=1` — *READ PROCESSED ORDERS*

**Purpose:** retrieves completed orders from the warehouse, including the quantities actually moved. This is the primary mechanism by which the calling system is notified of the outcome of each mission.

**Input:** none.

**Output — list of `MovementResult` objects:**

| Field | Type | Notes |
|---|---|---|
| `job_number` | `str` | Order identifier |
| `job_priority` | `int` | Assigned priority |
| `job_status` | `int` | See status table below |
| `job_date` | `str` | Format `DDMMYY` |
| `job_time` | `str` | Format `HHMM` |
| `positions` | `list[MovementLineResult]` | Lines with actual quantities |

**`MovementLineResult` object:**

| Field | Type | Notes |
|---|---|---|
| `article_number` | `str` | Article code |
| `operation` | `str` | `+` or `-` |
| `nominal_quantity` | `float` | Originally requested quantity |
| `actual_quantity` | `float` | Quantity actually moved |
| `container_size` | `int` | Container size code |
| `position_status` | `int` | `0` = pending, `1` = completed |

> *Extended by REQ-LOT-001: adds `batch_number: str | None` to `MovementLineResult` (the lot actually moved by the warehouse). See §4.3 and §5 of that document.*

**`job_status` values:**

| Value | Meaning |
|---|---|
| `0` | Queued / pending |
| `1` | In progress |
| `2` | Partially completed |
| `3` | Completed |

**Note:** when `actual_quantity` is less than `nominal_quantity`, the warehouse moved less than requested (e.g. insufficient stock). The calling system is responsible for handling this discrepancy.

**Reference envelope:**
```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:main="http://main.jws.com.hanel.de"
                  xmlns:xsd="http://main.jws.com.hanel.de/xsd">
  <soapenv:Header/>
  <soapenv:Body>
    <main:readAllJobsReqV01>
      <main:param>
        <xsd:mode>1</xsd:mode>
      </main:param>
    </main:readAllJobsReqV01>
  </soapenv:Body>
</soapenv:Envelope>
```

> *This envelope applies only when `lot_management_enabled=False`. When `True`, the operation becomes `readAllJobsV02` with `JobTypeV02`. See §7.2 of REQ-LOT-001.*

---

### 3.4 Fetch All Orders — `get_all_orders`

**Flow:** Queue monitoring and diagnostics (no direct business flow)
**SOAP operation:** `readAllJobsReqV01` with `mode=0` — *READ ALL ORDERS*

**Purpose:** retrieves all orders currently in the warehouse queue, including those pending and in progress. Used for queue status monitoring, diagnostics, and reconciliation.

**Input:** none.

**Output:** list of `MovementResult` objects (same structure as `get_completed_movements`; includes orders in all statuses).

**Reference envelope:**
```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:main="http://main.jws.com.hanel.de"
                  xmlns:xsd="http://main.jws.com.hanel.de/xsd">
  <soapenv:Header/>
  <soapenv:Body>
    <main:readAllJobsReqV01>
      <main:param>
        <xsd:mode>0</xsd:mode>
      </main:param>
    </main:readAllJobsReqV01>
  </soapenv:Body>
</soapenv:Envelope>
```

> *This envelope applies only when `lot_management_enabled=False`. When `True`, the operation becomes `readAllJobsV02` with `JobTypeV02`. See §7.2 of REQ-LOT-001.*

---

### 3.5 Fetch Stock Levels — `get_inventory`

**Flow:** Stock level query (Flow 4)
**SOAP operation:** `readAllAMDReqV01` — *READ STOCK LEVELS*

**Purpose:** retrieves the complete stock situation for all articles in the warehouse, broken down by physical location (lift, shelf, compartment).

**Input:** none.

**Output — list of `StockRecord` objects:**

| Field | Type | Notes |
|---|---|---|
| `article_number` | `str` | Article code |
| `article_name` | `str` | Description |
| `lift_number` | `int` | Warehouse/lift number |
| `shelf_number` | `int` | Shelf number |
| `compartment_number` | `int` | X position within the shelf |
| `compartment_depth_number` | `int` | Y position within the shelf |
| `container_size` | `int` | Container size code |
| `fifo` | `int` | FIFO ordering value |
| `inventory_at_storage_location` | `float` | Quantity at this location |
| `minimum_inventory` | `float` | Configured minimum threshold |

> *Extended by REQ-LOT-001: adds `batch_number: str | None` to `StockRecord`. When lot management is active, an article appears in multiple records (one per lot × location). See §4.4 and §5 of that document.*

**Operational notes:**
- An article may appear in multiple `StockRecord` entries if distributed across multiple physical locations. The total stock for an article is the sum of all records sharing the same `article_number`.
- Records with `lift_number=0` and `shelf_number=0` indicate articles present in the master registry but with no physical stock.
- This operation is required to reconcile manual movements performed directly at the machine console, which do not generate notifications to the calling system.

**Reference envelope:**
```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:main="http://main.jws.com.hanel.de">
  <soapenv:Header/>
  <soapenv:Body>
    <main:readAllAMDReqV01/>
  </soapenv:Body>
</soapenv:Envelope>
```

> *This envelope applies only when `lot_management_enabled=False`. When `True`, the operation becomes `readAllAMDV04` with `AMDTypeV02`. See §7.3 of REQ-LOT-001.*

---

### 3.6 Cancel Order — `cancel_order`

**Flow:** Error handling / order cancellation (support operation, no direct business flow)
**SOAP operation:** `deleteJobReqV01` — *DELETE PICK LIST*

**Purpose:** removes an order from the warehouse queue. Applicable only to orders not yet processed (status `0`).

**Input:**

| Field | Type | Notes |
|---|---|---|
| `job_number` | `str` | Identifier of the order to cancel |

**Output:** `bool` — `True` if `returnValue == 0`.

**Test mode behaviour:** if `test_mode=True`, the prefix is automatically applied here as well, consistent with `send_movement_order`.

**Reference envelope:**
```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:main="http://main.jws.com.hanel.de"
                  xmlns:xsd="http://main.jws.com.hanel.de/xsd">
  <soapenv:Header/>
  <soapenv:Body>
    <main:deleteJobReqV01>
      <main:param>
        <xsd:jobNumber>{job_number}</xsd:jobNumber>
      </main:param>
    </main:deleteJobReqV01>
  </soapenv:Body>
</soapenv:Envelope>
```

---

## 4. Mapping and Routing

### 4.1 Three-Level Mapping

The table below relates business flows, public interface methods, and the corresponding SOAP operations.

| Business Flow | Python Method | SOAP Operation | Notes |
|---|---|---|---|
| Flow 1 — Article master data | `register_article` | `sendAPDReqV01` | Master owned by calling system; warehouse is receiver only |
| Flow 2 — Inbound/outbound orders | `send_movement_order` | `sendJobsReqV01` | `+` = pick, `-` = load |
| Flow 3 — Movement confirmations | `get_completed_movements` | `readAllJobsReqV01` (mode=1) | Polling for outcomes; includes `actual_quantity` per line |
| Flow 4 — Stock level query | `get_inventory` | `readAllAMDReqV01` | Required to detect manual movements at the machine console |
| *(queue monitoring)* | `get_all_orders` | `readAllJobsReqV01` (mode=0) | Diagnostics; all orders regardless of status |
| *(order cancellation)* | `cancel_order` | `deleteJobReqV01` | Only orders in status 0 (not yet processed) |

> *This table reflects `lot_management_enabled=False` (V01 operations). When `True`, operations V02/V03/V04 are used for all rows except `cancel_order`. See §8 of REQ-LOT-001.*

### 4.2 Method → SOAP Operation Reference

| Python Method | SOAP Operation | Key Parameters |
|---|---|---|
| `register_article(article_number, article_name)` | `sendAPDReqV01` | `articleNumber`, `articleName` |
| `send_movement_order(order_number, positions)` | `sendJobsReqV01` | `jobNumber`, `JobPosition[]` with `operation` and `nominalQuantity` |
| `get_completed_movements()` | `readAllJobsReqV01` | `mode=1` (fixed) |
| `get_all_orders()` | `readAllJobsReqV01` | `mode=0` (fixed) |
| `get_inventory()` | `readAllAMDReqV01` | *(no parameters)* |
| `cancel_order(order_number)` | `deleteJobReqV01` | `jobNumber` |

### 4.3 Internal Dispatcher

The dispatcher routes each call to the correct SOAP operation. It is not exposed externally: the calling system interacts exclusively through the public interface methods.

```
register_article(...)         → sendAPDReqV01
send_movement_order(...)      → sendJobsReqV01
get_completed_movements()     → readAllJobsReqV01 (mode=1)
get_all_orders()              → readAllJobsReqV01 (mode=0)
get_inventory()               → readAllAMDReqV01
cancel_order(...)             → deleteJobReqV01
```

> *This dispatcher reflects `lot_management_enabled=False`. When `True`, the routing changes for all operations except `cancel_order`. See §8 of REQ-LOT-001.*

---

## 5. Error Handling

### 5.1 Error Classification

| Category | Examples | Behaviour |
|---|---|---|
| **Network error** | Timeout, connection refused, host unreachable | Automatic retry (see §5.2) |
| **HTTP error** | Status 4xx, 5xx | No retry; raises `HanelGatewayHttpError` |
| **SOAP error** | Fault in the response envelope | No retry; raises `HanelGatewaySoapFaultError` |
| **Application error** | `returnValue != 0` in response | No retry; raises `HanelGatewayApplicationError` with code and message |
| **Input validation error** | Field too long, wrong type | Raises `HanelGatewayValidationError` before sending |

### 5.2 Automatic Retry

Retry applies **only to network errors**. All other error types fail immediately.

Algorithm:
1. First attempt.
2. On network error, wait `retry_delay_seconds` seconds.
3. Retry until `retry_attempts` is reached.
4. If all attempts fail, raises `HanelGatewayNetworkError` with details of the last error.

### 5.3 Exception Hierarchy

```python
HanelGatewayError                # base
├── HanelGatewayNetworkError     # network error after all retries
├── HanelGatewayHttpError        # non-200 HTTP response
├── HanelGatewaySoapFaultError   # SOAP Fault in response
├── HanelGatewayApplicationError # returnValue != 0
└── HanelGatewayValidationError  # invalid input (pre-send)
```

Every exception must include:
- Human-readable message
- Operation that failed
- Technical detail (HTTP status, fault string, returnValue, etc.)
- Timestamp

### 5.4 Known returnValue Codes

| Value | Meaning |
|---|---|
| `0` | Operation completed successfully |
| `!= 0` | Application error — detail to be logged and propagated |

> The Hanel documentation does not provide a complete list of error codes. The module must always log the raw `returnValue` and include it in the exception to enable future diagnosis.

---

## 6. Logging

The module implements structured logging at all layers.

### Mandatory Log Events

| Event | Level |
|---|---|
| SOAP call initiated (operation + non-sensitive parameters) | `INFO` |
| Successful outcome (operation + duration) | `INFO` |
| Retry in progress (attempt N of M, reason) | `WARNING` |
| Final failure (type, operation, detail) | `ERROR` |
| Outgoing XML envelope | `DEBUG` (only if `log_soap_payloads=True`) |
| Incoming XML envelope | `DEBUG` (only if `log_soap_payloads=True`) |

### Log Format

Each entry must include: `timestamp`, `level`, `operation`, `duration_ms` (where applicable), `message`.

---

## 7. Constraints and Implementation Notes

### Field Constraints
- `articleNumber`: maximum 40 characters **and strictly numeric** (digits `0-9` only).
  The article number is a numeric code; the t-Server rejects article codes containing letters,
  hyphens, spaces, or symbols. The module enforces this **before sending**: a non-numeric
  `articleNumber` always raises `HanelGatewayValidationError`, regardless of
  `validation_truncate` (an article code cannot be auto-corrected by stripping characters
  without changing its identity). The 40-character limit follows the configurable truncate/raise
  behaviour below.
- `articleName`: maximum **40 characters**. Only the length is constrained (truncate/raise,
  configurable); the value may contain spaces and other characters.
- `jobNumber`: must be unique for each order sent. The calling system is responsible for uniqueness; the module does not maintain an internal registry.

### Single Production Environment
There is no separate test environment on the warehouse system. When `test_mode=True`, the module automatically prepends the configured prefix to all `jobNumber` values, allowing warehouse operators to identify and discard test orders without impacting real stock levels.

### Shelf Optimisation (Warehouse-Side)
The warehouse autonomously optimises the order in which shelves are presented (completing one shelf before moving to the next). The module must not implement any line-ordering logic: the order in which `MovementLine` entries are sent is irrelevant to operational efficiency.

### Single Shelf Presentation for Duplicate Lines
If multiple lines within the same order request the same article from the same shelf, the warehouse presents the shelf **only once**. The module must not deduplicate lines: this is native t-Server behaviour.

### Thread Safety
The module does not guarantee thread safety by default. If the calling system makes concurrent calls, it must handle synchronisation externally or instantiate one client per thread.

---

## 8. Public Interface — Summary

```python
class HanelWarehouseGateway:

    def __init__(self, config: dict) -> None: ...

    def register_article(
        self,
        article_number: str,
        article_name: str
    ) -> bool: ...

    def send_movement_order(
        self,
        order_number: str,
        positions: list[MovementLine]
    ) -> bool: ...

    def get_completed_movements(
        self
    ) -> list[MovementResult]: ...

    def get_all_orders(
        self
    ) -> list[MovementResult]: ...

    def get_inventory(
        self
    ) -> list[StockRecord]: ...

    def cancel_order(
        self,
        order_number: str
    ) -> bool: ...
```

### Supporting Dataclasses

```python
@dataclass
class MovementLine:
    article_number: str
    operation: str          # '+' = pick, '-' = load
    nominal_quantity: int   # > 0; fractional values rejected on send

@dataclass
class MovementLineResult:
    article_number: str
    operation: str
    nominal_quantity: float
    actual_quantity: float
    container_size: int
    position_status: int    # 0=pending, 1=completed

@dataclass
class MovementResult:
    job_number: str
    job_priority: int
    job_status: int         # 0=queued, 1=in progress, 2=partial, 3=completed
    job_date: str           # format DDMMYY
    job_time: str           # format HHMM
    positions: list[MovementLineResult]

@dataclass
class StockRecord:
    article_number: str
    article_name: str
    lift_number: int
    shelf_number: int
    compartment_number: int
    compartment_depth_number: int
    container_size: int
    fifo: int
    inventory_at_storage_location: float
    minimum_inventory: float
```

> *Extended by REQ-LOT-001: `MovementLine`, `MovementLineResult`, and `StockRecord` each gain an optional `batch_number: str | None = None` field. `register_article` gains an optional `batch_number` parameter. See §5 of that document.*

---

## 9. Suggested Python Dependencies

| Library | Purpose |
|---|---|
| `requests` | HTTP transmission of SOAP envelopes |
| `xml.etree.ElementTree` (stdlib) | XML parsing of responses |
| `dataclasses` (stdlib) | Data structure definitions |
| `logging` (stdlib) | Structured logging |

High-level SOAP libraries (e.g. `zeep`) are not required: calls are constructed manually as HTTP POST requests with `Content-Type: text/xml`. This ensures full control over the payload and eliminates unnecessary external dependencies.

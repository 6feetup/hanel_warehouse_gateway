# Scripts & E2E Testing

`scripts/hanel_cli.py` is a command-line tool for manually testing the gateway against the mock server (or a real t-Server endpoint). It exercises the full stack: input validation, serialization, HTTP transport, response parsing, and Python models.

## Prerequisites

1. **Mock server running:**
   ```bash
   docker compose up -d
   ```

2. **`.env` file configured** (or use `--endpoint` to override):
   ```dotenv
   HANEL_ENDPOINT_URL=http://localhost:8080/HanelService
   HANEL_TEST_MODE=false
   HANEL_LOT_MANAGEMENT_ENABLED=false
   ```
   Set `HANEL_LOT_MANAGEMENT_ENABLED=true` to use V02/V03/V04 SOAP operations with `batch_number` support.

3. **Dependencies installed:**
   ```bash
   uv sync
   ```

## Usage

```
uv run python scripts/hanel_cli.py <operation> [--input FILE] [--endpoint URL] [--test-mode] [--verbose]
```

| Flag | Description |
|------|-------------|
| `operation` | One of: `register_article`, `send_movement_order`, `get_completed_movements`, `get_all_orders`, `get_inventory`, `cancel_order`, `ping` |
| `--input FILE` | JSON file with operation parameters. If omitted, reads from stdin. |
| `--endpoint URL` | Overrides `HANEL_ENDPOINT_URL` from `.env`. |
| `--test-mode` | Enables `test_mode=True` (prepends `TEST_` to order numbers and to article numbers — both at registration and inside order lines — so test operations are identifiable warehouse-side). |
| `--verbose`, `-v` | Logs the full SOAP request/response payloads and any failure to stderr at DEBUG level (sets `log_soap_payloads=True`). Use this to debug calls and warehouse errors. |

Output is always JSON on stdout. On success:

```json
{"ok": true, "result": ...}
```

On error, every diagnostic attribute of the exception is included (the exact
keys depend on the error type), for example:

```json
{
  "ok": false,
  "type": "HanelGatewaySoapFaultError",
  "message": "SOAP fault in deleteJobReqV01: Warehouse busy or unavailable",
  "operation": "deleteJobReqV01",
  "detail": "Warehouse busy or unavailable | actor=... | detail=<detail>...</detail>",
  "timestamp": "2026-06-13T10:00:00",
  "fault_code": "env:Server",
  "fault_string": "Warehouse busy or unavailable",
  "fault_actor": "...",
  "fault_detail": "<detail>...</detail>"
}
```

Other error types expose their own fields: `http_status` (HTTP errors),
`return_value` (application errors), `field`/`value` (validation errors).
Combine `--verbose` with these fields to pinpoint warehouse-side failures.

Exit code is `0` on success, `1` on error.

---

## Operations

### `register_article`

Registers or updates an article in the warehouse catalogue.

**JSON input:**
```json
{
  "article_number": "2001",
  "article_name": "M6 stainless bolt",
  "batch_number": "LOTTO-2026-A"
}
```

`batch_number` is optional. It is only sent to the warehouse when `HANEL_LOT_MANAGEMENT_ENABLED=true`.

**Command:**
```bash
uv run python scripts/hanel_cli.py register_article \
  --input scripts/examples/register_article.json \
  --endpoint http://localhost:8080/HanelService
```

**Expected output:**
```json
{
  "ok": true,
  "result": true
}
```

---

### `send_movement_order`

Sends a movement order to the warehouse.

`operation`: `"+"` = load (put into warehouse), `"-"` = pick (take from warehouse).

**JSON input — single position:**
```json
{
  "order_number": "ORD-CLI-001",
  "positions": [
    {"article_number": "1001", "operation": "+", "nominal_quantity": 5}
  ]
}
```

**JSON input — multiple positions:**
```json
{
  "order_number": "ORD-CLI-002",
  "positions": [
    {"article_number": "1001", "operation": "+", "nominal_quantity": 5},
    {"article_number": "1002", "operation": "-", "nominal_quantity": 2}
  ]
}
```

**JSON input — with lot/batch numbers** (requires `HANEL_LOT_MANAGEMENT_ENABLED=true`):
```json
{
  "order_number": "ORD-LOT-001",
  "positions": [
    {"article_number": "1001", "operation": "+", "nominal_quantity": 5, "batch_number": "LOTTO-2026-A"}
  ]
}
```

`batch_number` per position is optional. It is included in the SOAP request only when `HANEL_LOT_MANAGEMENT_ENABLED=true`.

**Command:**
```bash
uv run python scripts/hanel_cli.py send_movement_order \
  --input scripts/examples/send_movement_order_single.json \
  --endpoint http://localhost:8080/HanelService
```

---

### `get_completed_movements`

Retrieves all completed orders. No JSON input required.

**Command:**
```bash
uv run python scripts/hanel_cli.py get_completed_movements \
  --endpoint http://localhost:8080/HanelService
```

**Expected output:**
```json
{
  "ok": true,
  "result": [
    {
      "job_number": "ORD-001",
      "job_priority": 1,
      "job_status": 3,
      "job_date": "300425",
      "job_time": "1430",
      "positions": [
        {
          "article_number": "1001",
          "operation": "+",
          "nominal_quantity": 5.0,
          "actual_quantity": 5.0,
          "container_size": 1,
          "position_status": 1
        }
      ]
    }
  ]
}
```

!!! note
    If `actual_quantity < nominal_quantity` in a position, stock was insufficient. Handling is the caller's responsibility.

---

### `get_all_orders`

Retrieves all orders currently in the warehouse queue (any status, not only completed). No JSON input required.

**Command:**
```bash
uv run python scripts/hanel_cli.py get_all_orders
```

**Expected output:**
```json
{
  "ok": true,
  "result": [
    {
      "job_number": "ORD-001",
      "job_priority": 1,
      "job_status": 0,
      "job_date": "300425",
      "job_time": "1430",
      "positions": [
        {
          "article_number": "1001",
          "operation": "+",
          "nominal_quantity": 5.0,
          "actual_quantity": 0.0,
          "container_size": 1,
          "position_status": 0
        }
      ]
    }
  ]
}
```

!!! note
    `job_status`: `0`=queued, `1`=in progress, `2`=partial, `3`=completed.

---

### `get_inventory`

Retrieves stock levels for all articles in the warehouse. No JSON input required.

This is the only mechanism to detect manual movements performed directly at the warehouse console.

**Command:**
```bash
uv run python scripts/hanel_cli.py get_inventory
```

**Expected output:**
```json
{
  "ok": true,
  "result": [
    {
      "article_number": "1001",
      "article_name": "M6 stainless bolt",
      "lift_number": 1,
      "shelf_number": 2,
      "compartment_number": 3,
      "compartment_depth_number": 1,
      "container_size": 1,
      "fifo": 0,
      "inventory_at_storage_location": 42.0,
      "minimum_inventory": 5.0,
      "batch_number": null
    }
  ]
}
```

!!! note
    An article may appear in multiple records if distributed across several storage locations.

---

### `cancel_order`

Cancels a queued order. Only applicable to orders not yet processed (status 0).

**JSON input:**
```json
{
  "order_number": "ORD-001"
}
```

**Command:**
```bash
echo '{"order_number": "ORD-001"}' | \
  uv run python scripts/hanel_cli.py cancel_order \
  --endpoint http://localhost:8080/HanelService
```

**Output on failure (order already completed):**
```json
{
  "ok": false,
  "type": "HanelGatewayApplicationError",
  "message": "deleteJobReqV01 returned error code 1",
  "operation": "deleteJobReqV01",
  "detail": "returnValue=1 | response=...",
  "return_value": 1
}
```

---

### `ping`

Connectivity health-check. Sends the lightweight read-only `readAllJobs`
request (the Hanel t-Server has no dedicated echo/ping operation) and reports
whether the server is reachable. Any HTTP reply — including a SOAP fault or a
non-2xx status — counts as alive; only a network failure (connection refused or
timeout) is reported as unreachable. To stay fast, the probe uses a single
attempt and a capped timeout instead of the operational retry/timeout settings,
so an unreachable server is reported within a few seconds. Takes no JSON input
and never fails: it returns a boolean result.

**Command:**
```bash
uv run python scripts/hanel_cli.py ping \
  --endpoint http://localhost:8080/HanelService
```

**Output when the server is reachable:**
```json
{
  "ok": true,
  "result": true
}
```

**Output when the server is unreachable:**
```json
{
  "ok": true,
  "result": false
}
```

---

## End-to-end test sequence

Run these commands in order to exercise the full workflow:

```bash
ENDPOINT=http://localhost:8080/HanelService

# 1. Reset mock server state
curl -s -X POST http://localhost:8080/admin/reset

# 2. Register a new article
echo '{"article_number": "2001", "article_name": "M6 stainless bolt"}' | \
  uv run python scripts/hanel_cli.py register_article --endpoint $ENDPOINT

# 3. Send a movement order
echo '{
  "order_number": "ORD-CLI-001",
  "positions": [{"article_number": "1001", "operation": "+", "nominal_quantity": 3}]
}' | uv run python scripts/hanel_cli.py send_movement_order --endpoint $ENDPOINT

# 4. Complete all pending orders (mock server admin endpoint)
curl -s -X POST http://localhost:8080/admin/complete-all

# 5. Verify completed movements
uv run python scripts/hanel_cli.py get_completed_movements --endpoint $ENDPOINT

# 6. Try to cancel the (now completed) order — expect HanelGatewayApplicationError
echo '{"order_number": "ORD-CLI-001"}' | \
  uv run python scripts/hanel_cli.py cancel_order --endpoint $ENDPOINT
```

---

---

## End-to-end test sequence — lot management

Run these commands to test the lot management workflow (requires `HANEL_LOT_MANAGEMENT_ENABLED=true` in `.env`):

```bash
ENDPOINT=http://localhost:8080/HanelService

# 1. Reset mock server state
curl -s -X POST http://localhost:8080/admin/reset

# 2. Register an article with a batch number (uses sendAPDReqV03)
echo '{"article_number": "2001", "article_name": "M6 stainless bolt", "batch_number": "LOTTO-2026-A"}' | \
  uv run python scripts/hanel_cli.py register_article --endpoint $ENDPOINT

# 3. Send a movement order with batch number on each position (uses sendJobsV02)
echo '{
  "order_number": "ORD-LOT-001",
  "positions": [{"article_number": "1001", "operation": "+", "nominal_quantity": 3, "batch_number": "LOTTO-2026-A"}]
}' | uv run python scripts/hanel_cli.py send_movement_order --endpoint $ENDPOINT

# 4. Complete all pending orders
curl -s -X POST http://localhost:8080/admin/complete-all

# 5. Verify completed movements — response includes batch_number per position (uses readAllJobsV02)
uv run python scripts/hanel_cli.py get_completed_movements --endpoint $ENDPOINT
```

---

## Example JSON files

Ready-to-use files are in `scripts/examples/`:

| File | Operation |
|------|-----------|
| `register_article.json` | `register_article` |
| `send_movement_order_single.json` | `send_movement_order` — single position |
| `send_movement_order_multi.json` | `send_movement_order` — multiple positions |
| `cancel_order.json` | `cancel_order` |

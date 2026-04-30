# hanel_cli.py — Manual testing tool

CLI script for testing the `HanelWarehouseGateway` manually against the mock server (or a real t-Server endpoint). It exercises the full stack: serialization, HTTP transport, response parsing, and Python models.

## Prerequisites

1. **Mock server running:**
   ```bash
   docker compose up -d
   ```

2. **`.env` file configured** (or use `--endpoint` to override):
   ```dotenv
   HANEL_ENDPOINT_URL=http://localhost:8080/HanelService
   HANEL_TEST_MODE=false
   ```

3. **Dependencies installed:**
   ```bash
   uv sync
   ```

## Usage

```
uv run python scripts/hanel_cli.py <operation> [--input FILE] [--endpoint URL] [--test-mode]
```

| Flag | Description |
|---|---|
| `operation` | One of: `register_article`, `send_movement_order`, `get_completed_movements`, `cancel_order` |
| `--input FILE` | JSON file with operation parameters. If omitted, reads from stdin. |
| `--endpoint URL` | Overrides `HANEL_ENDPOINT_URL` from `.env`. |
| `--test-mode` | Enables `test_mode=True` (prepends `TEST_` to order numbers). |

Output is always JSON on stdout:
```json
{"ok": true, "result": ...}
{"ok": false, "error": "...", "type": "HanelGatewayApplicationError"}
```

---

## Operations

### `register_article`

Registers or updates an article in the warehouse catalogue.

**JSON input:**
```json
{
  "article_number": "ART-CLI-001",
  "article_name": "Vite M6 Inox"
}
```

**Commands:**
```bash
# From file
uv run python scripts/hanel_cli.py register_article \
  --input scripts/examples/register_article.json \
  --endpoint http://localhost:8080/HanelService

# From stdin
echo '{"article_number": "ART-CLI-001", "article_name": "Vite M6 Inox"}' | \
  uv run python scripts/hanel_cli.py register_article \
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

Sends a movement order (pick `+` or load `-`) to the warehouse.

**JSON input — single position:**
```json
{
  "order_number": "ORD-CLI-001",
  "positions": [
    {"article_number": "ART-001", "operation": "+", "nominal_quantity": 5.0}
  ]
}
```

**JSON input — multiple positions:**
```json
{
  "order_number": "ORD-CLI-002",
  "positions": [
    {"article_number": "ART-001", "operation": "+", "nominal_quantity": 5.0},
    {"article_number": "ART-002", "operation": "-", "nominal_quantity": 2.0}
  ]
}
```

> `operation`: `"+"` = pick (take from warehouse), `"-"` = load (put into warehouse)

**Command:**
```bash
uv run python scripts/hanel_cli.py send_movement_order \
  --input scripts/examples/send_movement_order.json \
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

### `get_completed_movements`

Retrieves all completed orders from the warehouse. No JSON input needed.

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
      "job_number": "ORD-003",
      "job_priority": 1,
      "job_status": 3,
      "job_date": "300425",
      "job_time": "1430",
      "positions": [
        {
          "article_number": "ART-001",
          "operation": "+",
          "nominal_quantity": 10.0,
          "actual_quantity": 10.0,
          "container_size": 1,
          "position_status": 1
        }
      ]
    }
  ]
}
```

> If `actual_quantity < nominal_quantity` in a position, stock was insufficient.

---

### `cancel_order`

Cancels a queued order (only orders not yet processed, status 0).

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

**Expected output (success):**
```json
{
  "ok": true,
  "result": true
}
```

**Expected output (order already completed or not found):**
```json
{
  "ok": false,
  "error": "...",
  "type": "HanelGatewayApplicationError"
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
echo '{"article_number": "ART-CLI-001", "article_name": "Vite M6 Inox"}' | \
  uv run python scripts/hanel_cli.py register_article --endpoint $ENDPOINT

# 3. Send a movement order
echo '{
  "order_number": "ORD-CLI-001",
  "positions": [{"article_number": "ART-001", "operation": "+", "nominal_quantity": 3.0}]
}' | uv run python scripts/hanel_cli.py send_movement_order --endpoint $ENDPOINT

# 4. Complete all pending orders (mock server admin endpoint)
curl -s -X POST http://localhost:8080/admin/complete-all

# 5. Verify completed movements
uv run python scripts/hanel_cli.py get_completed_movements --endpoint $ENDPOINT

# 6. Try to cancel the (now completed) order — expect error
echo '{"order_number": "ORD-CLI-001"}' | \
  uv run python scripts/hanel_cli.py cancel_order --endpoint $ENDPOINT
```

---

## Example JSON files

Ready-to-use files are in `scripts/examples/`:

| File | Operation |
|---|---|
| `register_article.json` | `register_article` |
| `send_movement_order_single.json` | `send_movement_order` — single position |
| `send_movement_order_multi.json` | `send_movement_order` — multiple positions |
| `cancel_order.json` | `cancel_order` |

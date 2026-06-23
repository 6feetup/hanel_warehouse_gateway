# ADR-015: Lot Management Support (REQ-LOT-001)

**Status:** Accepted

**Date:** 2026-06-04

## Context

The Hanel t-Server exposes SOAP API versions V02, V03, and V04 that add support for
batch/lot numbers (`batchNumber`) on articles, movement orders, and inventory records.
The existing module only supports V01 operations.

## Decision

- Add a `lot_management_enabled: bool = False` flag to `GatewayConfig` (env var:
  `HANEL_LOT_MANAGEMENT_ENABLED`).
- When `lot_management_enabled=False` (default), all behaviour is identical to the
  pre-existing V01 implementation — full backward compatibility is preserved.
- When `lot_management_enabled=True`, the gateway uses:
  - `sendAPDReqV03` instead of `sendAPDReqV01` for `register_article`
  - `sendJobsV02` instead of `sendJobsReqV01` for `send_movement_order`
  - `readAllJobsV02` instead of `readAllJobsReqV01` for `get_completed_movements` / `get_all_orders`
  - `readAllAMDV04` instead of `readAllAMDReqV01` for `get_inventory`
  - `deleteJobReqV01` is unchanged (no lot-aware version exists)
- `batch_number: str | None = None` is added as the last field on `MovementLine`,
  `MovementLineResult`, and `StockRecord`.
- `register_article` gains an optional `batch_number` parameter in both
  `SoapOperations` and `HanelWarehouseGateway`.
- The XML parsers (`parse_movement_results`, `parse_stock_records`) are not forked:
  they use `findtext(..., None, ns)` which returns `None` when the tag is absent (V01)
  and the value when present (V02/V04) — single parser, two versions.
- When `lot_management_enabled=True` and an application error occurs, the message
  includes a hint pointing to configuration (REQ-LOT-21).

## Consequences

- Zero risk of regression for existing V01 users.
- The `batch_number` field on dataclasses is additive (default `None`); callers that
  do not use lot management are unaffected.
- PA-01 (exact XML tag names) is still provisional — see ADR-016.

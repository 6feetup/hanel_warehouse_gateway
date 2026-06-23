# ADR-018: Inventory `<article>` Tag and `h10_special_field` on StockRecord

**Status:** Accepted

**Date:** 2026-06-23

## Context

A real `readAllAMDResV04` response captured from the t-Server
(`docs/inventory_response.xml`) revealed two mismatches with the implementation:

1. **Record wrapper element.** Each stock record is wrapped in an `<article>` element
   (with the xsd namespace declared as the default namespace), not the
   `<articleMasterDataRecord>` tag that had been assumed when no real sample was
   available. As a result `parse_stock_records` matched nothing and `get_inventory()`
   always returned an empty list.
2. **Extra field `h10SpecialField`.** Every record carries an `h10SpecialField`
   element holding an optional EAN/barcode for the storage location (often empty).
   It was not mapped onto `StockRecord`.

This is a public-interface change (a new field on the `StockRecord` dataclass) and
therefore requires an ADR and a version bump (see CLAUDE.md).

## Decision

- In `parse_stock_records` (`_xml.py`), match stock records with
  `.//xsd:article` instead of `.//xsd:articleMasterDataRecord`. The fictional tag is
  dropped entirely — no backward-compatibility fallback, since it never existed in a
  real response.
- Add `h10_special_field: str | None = None` to `StockRecord`. The parser maps an
  empty `<h10SpecialField/>` to `None` (consistent with how `batch_number` is handled);
  a non-empty value is exposed verbatim as a string.
- Realign the inventory fixtures (`tests/fixtures/read_inventory_response.xml`,
  `read_inventory_v04_response.xml`) and the mock server (`mock_server/responses.py`,
  `state.py`, `data/inventory.json`) to the real response shape: `<article>` wrapper,
  `h10SpecialField`, and the real response element name `readAllAMDResV04`.

The field is added at the end of the dataclass with a default, so the change is
additive and backward compatible for callers constructing `StockRecord` positionally
up to `batch_number`.

## Consequences

- `get_inventory()` now returns the actual stock records instead of an empty list.
- Callers gain access to the location barcode via `StockRecord.h10_special_field`.
- All XML tag knowledge remains confined to `_xml.py` and the fixtures, per ADR-004.
- The real sample also confirmed the `batchNumber` tag name, resolving the open point
  in [ADR-016](016-lot-tag-names-provisional.md) (now Accepted).

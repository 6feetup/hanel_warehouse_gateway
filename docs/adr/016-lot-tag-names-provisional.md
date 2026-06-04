# ADR-016: Provisional XML Tag Names for Lot Management

**Status:** Provisional

**Date:** 2026-06-04

## Context

PA-01 (open point from REQ-LOT-001): the exact XML tag name for the lot/batch number
in the Hanel t-Server WSDL has not been verified against real server output. The
implementation assumes `batchNumber` based on Hanel naming conventions.

## Decision

Use `<xsd:batchNumber>` as the XML element name for batch/lot numbers in all V02/V03/V04
envelopes and parsers.

All XML tags are confined to `src/hanel_warehouse_gateway/_xml.py` and the
`tests/fixtures/` files. If the real WSDL uses a different name, only those two
locations need to change — no other module is affected.

## Resolution

Once the WSDL is available, verify the tag name and update this ADR status to
`Accepted` or `Superseded` as appropriate.

## Consequences

- The module may not interoperate with a real t-Server until PA-01 is resolved.
- The fix, if needed, is a one-file change in `_xml.py` plus fixture updates.
